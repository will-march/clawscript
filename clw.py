"""Clawscript reference interpreter (clw.py).

Parses a Clawscript source file with ast, enforces strict static rules,
walks the AST node-by-node emitting a JSONL trace. Pure-Python expressions
evaluate locally; prompt()/tool() dispatch to the Anthropic SDK.

Usage:
    python clw.py program.clw [--trace trace.jsonl]

The module intentionally keeps the statement walker explicit so every
control-flow decision is traceable. Expressions route through Python's
compile+eval for brevity (they cannot re-enter control flow).
"""
from __future__ import annotations

import ast
import builtins as _builtins
import inspect
import json
import os
import sys
import time
import typing
from typing import Any, Callable


# ---------- Errors and control-flow signals ----------

class ClawError(Exception):
    """Base class for Clawscript runtime errors."""


class ValidationError(ClawError):
    """Raised when a program fails static validation."""


class InvariantError(ClawError):
    """Raised when assert_invariant() fails."""


class ApprovalDenied(ClawError):
    """Raised when require_approval() is not granted."""


class BoundExceeded(ClawError):
    """Raised when a @bounded_loop(N) cap is exceeded."""


class _Return(BaseException):
    def __init__(self, value: Any) -> None:
        self.value = value


class _Break(BaseException):
    pass


class _Continue(BaseException):
    pass


# ---------- Lexical environment ----------

class Env:
    __slots__ = ("vars", "parent")

    def __init__(self, parent: "Env | None" = None) -> None:
        self.vars: dict[str, Any] = {}
        self.parent = parent

    def get(self, name: str) -> Any:
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(name)

    def set(self, name: str, value: Any) -> None:
        self.vars[name] = value

    def flatten(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        stack: list[Env] = []
        e: Env | None = self
        while e is not None:
            stack.append(e)
            e = e.parent
        for frame in reversed(stack):
            out.update(frame.vars)
        return out


# ---------- JSONL tracer ----------

class Tracer:
    def __init__(self, sink: Any = sys.stdout) -> None:
        self.sink = sink
        self.n = 0

    def emit(self, event: dict) -> None:
        self.n += 1
        record = {"step": self.n, "ts": round(time.time(), 3), **event}
        self.sink.write(json.dumps(record, default=repr) + "\n")
        self.sink.flush()


# ---------- Static validator ----------

class Validator(ast.NodeVisitor):
    """Enforces the strict-flow rules at parse time.

    Rules:
      * 'while' must appear inside a function decorated @bounded_loop(N).
      * 'import' / 'from ... import' are forbidden.
      * prompt() must pass a string-literal model and a literal/f-string text.
      * checkpoint() label must be a string literal.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []
        self._bounded_func_stack: list[bool] = []

    def _has_bounded_decorator(self, fn: ast.FunctionDef) -> bool:
        for d in fn.decorator_list:
            if (isinstance(d, ast.Call)
                    and isinstance(d.func, ast.Name)
                    and d.func.id == "bounded_loop"):
                if (len(d.args) != 1
                        or not isinstance(d.args[0], ast.Constant)
                        or not isinstance(d.args[0].value, int)):
                    self.errors.append(
                        f"line {d.lineno}: bounded_loop(N) requires an integer literal")
                    return False
                return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._bounded_func_stack.append(self._has_bounded_decorator(node))
        self.generic_visit(node)
        self._bounded_func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_While(self, node: ast.While) -> None:
        if not (self._bounded_func_stack and self._bounded_func_stack[-1]):
            self.errors.append(
                f"line {node.lineno}: 'while' must be inside a @bounded_loop(N) function")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        self.errors.append(f"line {node.lineno}: 'import' is forbidden in Clawscript")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.errors.append(f"line {node.lineno}: 'from ... import' is forbidden")

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id == "prompt":
                if len(node.args) < 2:
                    self.errors.append(f"line {node.lineno}: prompt() requires (model, text)")
                else:
                    m, t = node.args[0], node.args[1]
                    if not (isinstance(m, ast.Constant) and isinstance(m.value, str)):
                        self.errors.append(
                            f"line {node.lineno}: prompt() model must be a string literal")
                    if not isinstance(t, (ast.Constant, ast.JoinedStr)):
                        self.errors.append(
                            f"line {node.lineno}: prompt() text must be a string literal or f-string")
            elif node.func.id == "checkpoint":
                if not node.args or not isinstance(node.args[0], ast.Constant):
                    self.errors.append(
                        f"line {node.lineno}: checkpoint() requires a string-literal label")
        self.generic_visit(node)


# ---------- Safe Python builtins exposed to Clawscript expressions ----------

_SAFE_NAMES = (
    "len range enumerate zip map filter sorted reversed sum min max abs round "
    "int float str bool list dict tuple set print repr any all isinstance type "
    "Exception ValueError TypeError KeyError IndexError RuntimeError StopIteration"
).split()

SAFE_BUILTINS: dict[str, Any] = {n: getattr(_builtins, n) for n in _SAFE_NAMES}


# ---------- Built-in constructors ----------

def make_typed(tracer: Tracer) -> Callable:
    def typed(f):
        sig = inspect.signature(f)

        def wrapped(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            for name, value in bound.arguments.items():
                hint = sig.parameters[name].annotation
                if hint is inspect.Parameter.empty:
                    continue
                origin = typing.get_origin(hint) or hint
                if isinstance(origin, type) and not isinstance(value, origin):
                    raise TypeError(
                        f"typed: '{name}' expected {hint}, got {type(value).__name__}")
            result = f(*args, **kwargs)
            ret = sig.return_annotation
            if ret is not inspect.Signature.empty:
                origin = typing.get_origin(ret) or ret
                if isinstance(origin, type) and not isinstance(result, origin):
                    raise TypeError(
                        f"typed: return expected {ret}, got {type(result).__name__}")
            tracer.emit({"event": "typed_ok", "function": getattr(f, "__name__", "?")})
            return result

        wrapped.__wrapped__ = f
        wrapped.__name__ = getattr(f, "__name__", "typed_fn")
        return wrapped

    return typed


def make_prompt(client: Any, tracer: Tracer) -> Callable:
    def prompt(model: str, text: str) -> str:
        tracer.emit({
            "event": "prompt_begin",
            "model": model,
            "chars": len(text),
        })
        if client is None:
            tracer.emit({"event": "prompt_stub", "note": "no anthropic client; returning stub"})
            return f"[stub response from {model}]"
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": text}],
        )
        out = "".join(getattr(b, "text", "") for b in resp.content)
        tracer.emit({
            "event": "prompt_end",
            "model": model,
            "tokens_in": getattr(resp.usage, "input_tokens", None),
            "tokens_out": getattr(resp.usage, "output_tokens", None),
        })
        return out
    return prompt


def make_tool(registry: dict[str, Callable], tracer: Tracer) -> Callable:
    def tool(name: str, **kwargs: Any) -> Any:
        if name not in registry:
            tracer.emit({"event": "tool_error", "name": name, "error": "unknown"})
            raise KeyError(f"tool '{name}' is not registered")
        tracer.emit({"event": "tool_begin", "name": name, "kwargs": kwargs})
        try:
            result = registry[name](**kwargs)
        except Exception as e:
            tracer.emit({"event": "tool_error", "name": name, "error": repr(e)})
            raise
        tracer.emit({"event": "tool_end", "name": name})
        return result
    return tool


def make_assert_invariant(tracer: Tracer) -> Callable:
    def assert_invariant(expr: Any, msg: str = "invariant violated") -> None:
        if not expr:
            tracer.emit({"event": "invariant_fail", "message": msg})
            raise InvariantError(msg)
        tracer.emit({"event": "invariant_ok", "message": msg})
    return assert_invariant


def make_checkpoint(tracer: Tracer) -> Callable:
    def checkpoint(label: str, **data: Any) -> None:
        tracer.emit({"event": "checkpoint", "label": label, "data": data})
    return checkpoint


def make_require_approval(tracer: Tracer, approver: Callable[[str], bool]) -> Callable:
    def require_approval(action: str) -> None:
        tracer.emit({"event": "approval_requested", "action": action})
        granted = bool(approver(action))
        tracer.emit({"event": "approval_result", "action": action, "granted": granted})
        if not granted:
            raise ApprovalDenied(action)
    return require_approval


def make_bounded_loop(interp: "Interpreter") -> Callable:
    def bounded_loop(n: int) -> Callable:
        def decorator(f):
            def wrapped(*args, **kwargs):
                interp._cap_stack.append(n)
                try:
                    return f(*args, **kwargs)
                finally:
                    interp._cap_stack.pop()
            wrapped.__wrapped__ = f
            wrapped.__cls_bounded_cap__ = n
            wrapped.__name__ = getattr(f, "__name__", "bounded_fn")
            return wrapped
        return decorator
    return bounded_loop


def default_approver(action: str) -> bool:
    reply = input(f"[clw] Approve action '{action}'? [y/N] ").strip().lower()
    return reply in ("y", "yes")


# ---------- Interpreter ----------

_AUG_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b, ast.BitOr: lambda a, b: a | b,
    ast.BitAnd: lambda a, b: a & b, ast.BitXor: lambda a, b: a ^ b,
    ast.LShift: lambda a, b: a << b, ast.RShift: lambda a, b: a >> b,
}


class Interpreter:
    def __init__(
        self,
        *,
        tracer: Tracer | None = None,
        tools: dict[str, Callable] | None = None,
        approver: Callable[[str], bool] | None = None,
        client: Any = None,
    ) -> None:
        self.tracer = tracer or Tracer()
        self.tools = tools or {}
        self.approver = approver or default_approver
        self.client = client
        self._cap_stack: list[int] = []
        self.globals = Env()
        self._install_builtins()

    def _install_builtins(self) -> None:
        g = self.globals
        g.set("prompt", make_prompt(self.client, self.tracer))
        g.set("tool", make_tool(self.tools, self.tracer))
        g.set("assert_invariant", make_assert_invariant(self.tracer))
        g.set("checkpoint", make_checkpoint(self.tracer))
        g.set("require_approval", make_require_approval(self.tracer, self.approver))
        g.set("bounded_loop", make_bounded_loop(self))
        g.set("typed", make_typed(self.tracer))

    # --- top-level entry ---
    def run(self, source: str, filename: str = "<clw>") -> Any:
        tree = ast.parse(source, filename=filename)
        v = Validator()
        v.visit(tree)
        if v.errors:
            raise ValidationError("\n".join(v.errors))
        self.tracer.emit({"event": "program_start", "file": filename})
        try:
            for stmt in tree.body:
                self._exec(stmt, self.globals)
            self.tracer.emit({"event": "program_end", "status": "ok"})
        except Exception as e:
            self.tracer.emit({"event": "program_end", "status": "error", "error": repr(e)})
            raise

    # --- expression eval (delegated to Python) ---
    def _eval(self, node: ast.AST, env: Env) -> Any:
        expr = ast.Expression(body=node)
        ast.copy_location(expr, node)
        code = compile(expr, f"<clw:{getattr(node, 'lineno', '?')}>", "eval")
        return eval(code, {"__builtins__": SAFE_BUILTINS}, env.flatten())

    # --- statement dispatch ---
    def _exec(self, node: ast.AST, env: Env) -> None:
        self.tracer.emit({
            "event": "step",
            "node": type(node).__name__,
            "line": getattr(node, "lineno", -1),
        })
        method = getattr(self, f"_stmt_{type(node).__name__}", None)
        if method is None:
            raise ClawError(f"unsupported statement: {type(node).__name__}")
        method(node, env)

    def _assign(self, target: ast.AST, value: Any, env: Env) -> None:
        if isinstance(target, ast.Name):
            env.set(target.id, value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            vals = list(value)
            if len(vals) != len(target.elts):
                raise ValueError(f"unpack mismatch: {len(vals)} vs {len(target.elts)}")
            for t, v in zip(target.elts, vals):
                self._assign(t, v, env)
        elif isinstance(target, ast.Subscript):
            obj = self._eval(target.value, env)
            key = self._eval(target.slice, env)
            obj[key] = value
        elif isinstance(target, ast.Attribute):
            obj = self._eval(target.value, env)
            setattr(obj, target.attr, value)
        else:
            raise NotImplementedError(f"assign target: {type(target).__name__}")

    # --- statement handlers ---
    def _stmt_Expr(self, node: ast.Expr, env: Env) -> None:
        self._eval(node.value, env)

    def _stmt_Assign(self, node: ast.Assign, env: Env) -> None:
        value = self._eval(node.value, env)
        for t in node.targets:
            self._assign(t, value, env)

    def _stmt_AugAssign(self, node: ast.AugAssign, env: Env) -> None:
        load = (ast.Name(id=node.target.id, ctx=ast.Load())
                if isinstance(node.target, ast.Name) else node.target)
        current = self._eval(load, env)
        rhs = self._eval(node.value, env)
        op = _AUG_OPS[type(node.op)]
        self._assign(node.target, op(current, rhs), env)

    def _stmt_AnnAssign(self, node: ast.AnnAssign, env: Env) -> None:
        if node.value is not None:
            self._assign(node.target, self._eval(node.value, env), env)

    def _stmt_If(self, node: ast.If, env: Env) -> None:
        body = node.body if self._eval(node.test, env) else node.orelse
        for s in body:
            self._exec(s, env)

    def _stmt_For(self, node: ast.For, env: Env) -> None:
        iterable = self._eval(node.iter, env)
        broke = False
        for item in iterable:
            self._assign(node.target, item, env)
            try:
                for s in node.body:
                    self._exec(s, env)
            except _Break:
                broke = True
                break
            except _Continue:
                continue
        if not broke:
            for s in node.orelse:
                self._exec(s, env)

    def _stmt_While(self, node: ast.While, env: Env) -> None:
        if not self._cap_stack:
            raise BoundExceeded("while outside @bounded_loop context")
        cap = self._cap_stack[-1]
        count = 0
        broke = False
        while self._eval(node.test, env):
            if count >= cap:
                raise BoundExceeded(
                    f"@bounded_loop({cap}) exceeded at line {node.lineno}")
            count += 1
            try:
                for s in node.body:
                    self._exec(s, env)
            except _Break:
                broke = True
                break
            except _Continue:
                continue
        if not broke:
            for s in node.orelse:
                self._exec(s, env)

    def _stmt_Try(self, node: ast.Try, env: Env) -> None:
        try:
            for s in node.body:
                self._exec(s, env)
        except (_Break, _Continue, _Return):
            raise
        except Exception as e:
            self.tracer.emit({"event": "exception", "error": repr(e)})
            handled = False
            for h in node.handlers:
                if h.type is None or isinstance(e, self._eval(h.type, env)):
                    if h.name:
                        env.set(h.name, e)
                    for s in h.body:
                        self._exec(s, env)
                    handled = True
                    break
            if not handled:
                raise
        else:
            for s in node.orelse:
                self._exec(s, env)
        finally:
            for s in node.finalbody:
                self._exec(s, env)

    def _stmt_Return(self, node: ast.Return, env: Env) -> None:
        raise _Return(self._eval(node.value, env) if node.value else None)

    def _stmt_Break(self, node: ast.Break, env: Env) -> None:
        raise _Break()

    def _stmt_Continue(self, node: ast.Continue, env: Env) -> None:
        raise _Continue()

    def _stmt_Pass(self, node: ast.Pass, env: Env) -> None:
        return None

    def _stmt_Raise(self, node: ast.Raise, env: Env) -> None:
        if node.exc is None:
            raise
        exc = self._eval(node.exc, env)
        if isinstance(exc, type):
            exc = exc()
        raise exc

    def _stmt_Assert(self, node: ast.Assert, env: Env) -> None:
        if not self._eval(node.test, env):
            msg = self._eval(node.msg, env) if node.msg else "assertion failed"
            raise AssertionError(msg)

    def _stmt_FunctionDef(self, node: ast.FunctionDef, env: Env) -> None:
        closure = env
        defaults = [self._eval(d, env) for d in node.args.defaults]
        interp = self

        def clw_func(*args: Any, **kwargs: Any) -> Any:
            local = Env(parent=closure)
            params = node.args.args
            offset = len(params) - len(defaults)
            for i, p in enumerate(params):
                if i < len(args):
                    local.set(p.arg, args[i])
                elif p.arg in kwargs:
                    local.set(p.arg, kwargs.pop(p.arg))
                elif i >= offset:
                    local.set(p.arg, defaults[i - offset])
                else:
                    raise TypeError(f"missing argument '{p.arg}'")
            for k, v in kwargs.items():
                local.set(k, v)
            try:
                for s in node.body:
                    interp._exec(s, local)
            except _Return as r:
                return r.value
            return None

        clw_func.__name__ = node.name
        clw_func.__annotations__ = {
            a.arg: self._eval(a.annotation, env)
            for a in node.args.args if a.annotation is not None
        }
        fn: Any = clw_func
        for d in reversed(node.decorator_list):
            dec = self._eval(d, env)
            fn = dec(fn)
        env.set(node.name, fn)

    def _stmt_ClassDef(self, node: ast.ClassDef, env: Env) -> None:
        class_env = Env(parent=env)
        for s in node.body:
            self._exec(s, class_env)
        bases = tuple(self._eval(b, env) for b in node.bases) or (object,)
        klass = type(node.name, bases, dict(class_env.vars))
        env.set(node.name, klass)


# ---------- CLI ----------

def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print("usage: python clw.py <program.clw> [--trace trace.jsonl]", file=sys.stderr)
        return 2
    source_path = argv[1]
    trace_sink: Any = sys.stdout
    if "--trace" in argv:
        trace_sink = open(argv[argv.index("--trace") + 1], "w")
    with open(source_path) as f:
        source = f.read()
    tracer = Tracer(trace_sink)
    client = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic()
        except Exception as e:
            print(f"[clw] anthropic import failed: {e}", file=sys.stderr)
    import json as _json
    tools = {
        "http_get": lambda url: f"(stub fetched bytes from {url})",
        "deploy": lambda target, config: {"target": target, "ok": True},
        "retrieve": lambda query, k: [
            {"id": f"doc-{i}", "text": f"stub fact {i} about {query}"} for i in range(k)
        ],
        "parse_json": lambda text: _json.loads(text),
        "search": lambda arg: f"(stub search result for: {arg})",
        "calc": lambda arg: eval(arg, {"__builtins__": {}}, {}),
    }
    interp = Interpreter(tracer=tracer, client=client, tools=tools)
    try:
        interp.run(source, filename=source_path)
    except ClawError as e:
        print(f"[clw] {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
