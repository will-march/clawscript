"""Generate per-example explainer PDFs plus a detailed setup-and-deploy guide.

Run:  python3 make_docs.py

Outputs:
    rag_cited-explainer.pdf
    llm_judge-explainer.pdf
    extract_json-explainer.pdf
    react_agent-explainer.pdf
    SETUP-AND-DEPLOY.pdf
"""
from fpdf import FPDF


class Doc(FPDF):
    title_text = ""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120)
        w = self.w - self.l_margin - self.r_margin
        self.cell(w / 2, 6, self.title_text, align="L")
        self.cell(w / 2, 6, f"Page {self.page_no()}", align="R")
        self.ln(8)
        self.set_text_color(0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150)
        self.cell(0, 6, "Clawscript v0.1 -- 2026-04-17", align="C")
        self.set_text_color(0)

    def h1(self, text):
        self.set_font("Helvetica", "B", 22)
        self.ln(2)
        self.cell(0, 12, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(50)
        self.set_line_width(0.5)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)

    def h2(self, text):
        self.set_font("Helvetica", "B", 14)
        self.ln(3)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def h3(self, text):
        self.set_font("Helvetica", "B", 11)
        self.ln(2)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")

    def body(self, text):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10.5)
        self.multi_cell(0, 5.2, text)
        self.ln(1)

    def mono(self, text):
        self.set_x(self.l_margin)
        self.set_font("Courier", "", 9)
        self.set_fill_color(245, 245, 245)
        self.multi_cell(0, 4.6, text, fill=True, border=0)
        self.set_font("Helvetica", "", 10.5)
        self.ln(1)

    def bullets(self, items):
        self.set_font("Helvetica", "", 10.5)
        for it in items:
            self.set_x(self.l_margin + 4)
            self.multi_cell(0, 5.2, f"*  {it}")
        self.ln(1)

    def numbered(self, items):
        self.set_font("Helvetica", "", 10.5)
        for i, it in enumerate(items, 1):
            self.set_x(self.l_margin + 4)
            self.multi_cell(0, 5.2, f"{i}.  {it}")
        self.ln(1)

    def callout(self, label, text):
        self.set_fill_color(250, 243, 224)
        self.set_draw_color(220, 180, 90)
        self.set_line_width(0.3)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 10)
        y0 = self.get_y()
        self.multi_cell(0, 5.5, label, fill=True)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 4.8, text, fill=True)
        y1 = self.get_y()
        self.rect(self.l_margin, y0, self.w - self.l_margin - self.r_margin, y1 - y0)
        self.ln(2)

    def table(self, rows, col_widths, header_bold=True):
        self.set_font("Helvetica", "B" if header_bold else "", 9.5)
        self.set_fill_color(230, 230, 235)
        for i, cell in enumerate(rows[0]):
            self.cell(col_widths[i], 7, cell, border=1, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 9)
        for row in rows[1:]:
            max_lines = 1
            for i, cell in enumerate(row):
                w = self.get_string_width(cell)
                lines = max(1, int(w / (col_widths[i] - 2)) + 1)
                max_lines = max(max_lines, lines)
            h = max(6, 4.5 * max_lines + 2)
            x0 = self.get_x()
            y0 = self.get_y()
            for i, cell in enumerate(row):
                self.rect(x0, y0, col_widths[i], h)
                self.set_xy(x0 + 1, y0 + 1)
                self.multi_cell(col_widths[i] - 2, 4, cell, border=0)
                x0 += col_widths[i]
                self.set_xy(x0, y0)
            self.set_xy(self.l_margin, y0 + h)
        self.ln(2)


def make_doc(title):
    pdf = Doc()
    pdf.title_text = title
    pdf.set_auto_page_break(True, margin=16)
    pdf.set_margins(18, 18, 18)
    return pdf


def cover(pdf, title, subtitle, blurb):
    pdf.add_page()
    pdf.ln(35)
    pdf.set_font("Helvetica", "B", 30)
    pdf.cell(0, 16, title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(90)
    pdf.multi_cell(0, 7, subtitle, align="C")
    pdf.set_text_color(0)
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(0, 5.2, blurb, align="C")
    pdf.ln(10)


# ============================================================
# RAG CITED EXPLAINER
# ============================================================

def build_rag_cited():
    pdf = make_doc("rag_cited.clw -- Grounded RAG with citation invariants")
    cover(
        pdf,
        "rag_cited.clw",
        "Grounded retrieval-augmented generation with\nmandatory citations or explicit abstention.",
        "An explainer for the Clawscript example that refuses to return\n"
        "an uncited answer. Showcases assert_invariant as a hallucination guard.",
    )

    pdf.add_page()
    pdf.h1("1. What the program does")
    pdf.body(
        "Given a user question, the program retrieves five candidate documents "
        "from a tool, builds a numbered source block, asks Claude to answer "
        "using only those sources with bracketed citations, and then runs a "
        "hard check: the answer must either cite at least one retrieved doc "
        "or say exactly 'NO ANSWER IN SOURCES'. Any other output terminates "
        "the program with InvariantError."
    )
    pdf.h2("The shape of a run")
    pdf.bullets([
        "Input: a natural-language question.",
        "Tool call: retrieve(query, k=5) returns a list of {id, text} dicts.",
        "LLM call: one prompt() to claude-sonnet-4-6 with strict instructions.",
        "Validation: a list comprehension finds which doc-ids appear in the answer.",
        "Output: a dict {answer, citations, abstained}.",
    ])

    pdf.add_page()
    pdf.h1("2. Why Clawscript fits this problem")
    pdf.body(
        "RAG with citations is the most common hallucination mitigation in "
        "production LLM apps. The problem: prompt-level instructions to 'cite "
        "everything' are regularly ignored. The model fabricates a citation, "
        "or cites nothing, or starts answering outside the source pack."
    )
    pdf.body(
        "Prompt-only RAG trusts the model to comply. This program does not. "
        "The citation check is a program invariant: no passing citations, no "
        "returning from the function. When the invariant fires, it fires "
        "audibly -- an invariant_fail trace record and a non-zero exit code."
    )
    pdf.callout(
        "Design heuristic",
        "If a compliance team would write a 'must' sentence about output "
        "shape, that sentence belongs inside an assert_invariant, not inside "
        "the prompt.",
    )

    pdf.add_page()
    pdf.h1("3. Code walk-through")
    pdf.h2("The signature")
    pdf.mono(
        "@typed\n"
        "def answer_with_citations(question: str) -> dict:"
    )
    pdf.body(
        "The @typed decorator enforces that 'question' is a str on entry and "
        "that the return value is a dict on exit. Mistakes here raise "
        "TypeError with a line-accurate message."
    )
    pdf.h2("Retrieval with a lower-bound invariant")
    pdf.mono(
        "docs = tool(\"retrieve\", query=question, k=5)\n"
        "assert_invariant(len(docs) > 0, \"retrieval returned zero docs\")"
    )
    pdf.body(
        "If the retrieval tool returns an empty list, the program stops "
        "before the LLM call. No hallucinating over an empty context."
    )
    pdf.h2("The literal prompt")
    pdf.mono(
        'answer = prompt(\n'
        '    "claude-sonnet-4-6",\n'
        '    f"Answer using ONLY the sources below. Every factual\\n"\n'
        '    f"sentence must end with a bracketed citation like\\n"\n'
        '    f"[doc-id]. If sources do not support an answer, reply\\n"\n'
        '    f"exactly \'NO ANSWER IN SOURCES\'.\\n\\nSources:\\n{context}\\n"\n'
        '    f"\\nQuestion: {question}"\n'
        ')'
    )
    pdf.body(
        "The model and text are visible in source. The validator enforces "
        "that the model is a string literal and the text is either a literal "
        "or an f-string. Neither the interpreter nor the runtime can "
        "paraphrase the request."
    )

    pdf.add_page()
    pdf.h2("The citation check")
    pdf.mono(
        'citations = [d["id"] for d in docs if f"[{d[\'id\']}]" in answer]\n'
        'abstained = "NO ANSWER IN SOURCES" in answer\n'
        'assert_invariant(\n'
        '    len(citations) > 0 or abstained,\n'
        '    "answer must cite at least one retrieved doc or explicitly abstain",\n'
        ')'
    )
    pdf.body(
        "Two accepted outcomes: the answer contains at least one [doc-id] "
        "that appeared in the retrieved set, OR the answer contains the "
        "abstention sentinel. Anything else halts the program."
    )
    pdf.callout(
        "Note on citation granularity",
        "The check only verifies presence of a doc-id substring. A more "
        "rigorous variant would count per-sentence citations. That change "
        "is one list comprehension and one invariant away.",
    )

    pdf.add_page()
    pdf.h1("4. Running it")
    pdf.mono(
        "# stub mode (no API key)\n"
        "python3 clw.py examples/rag_cited.clw --trace /tmp/rag.jsonl\n\n"
        "# real mode (Claude answers)\n"
        "export ANTHROPIC_API_KEY=sk-ant-...\n"
        "python3 clw.py examples/rag_cited.clw --trace /tmp/rag.jsonl"
    )
    pdf.h2("Expected trace shape (abridged)")
    pdf.mono(
        '{"event":"program_start","file":"examples/rag_cited.clw"}\n'
        '{"event":"checkpoint","label":"rag_start","data":{"q":"..."}}\n'
        '{"event":"tool_begin","name":"retrieve","kwargs":{...}}\n'
        '{"event":"tool_end","name":"retrieve"}\n'
        '{"event":"invariant_ok","message":"retrieval returned zero docs"}\n'
        '{"event":"checkpoint","label":"retrieved","data":{"n":5}}\n'
        '{"event":"prompt_begin","model":"claude-sonnet-4-6"}\n'
        '{"event":"prompt_end","model":"claude-sonnet-4-6","tokens_in":...}\n'
        '{"event":"checkpoint","label":"answered","data":{"chars":812}}\n'
        '{"event":"invariant_ok","message":"answer must cite..."}\n'
        '{"event":"checkpoint","label":"validated","data":{...}}\n'
        '{"event":"program_end","status":"ok"}'
    )
    pdf.h2("Variations to try")
    pdf.bullets([
        "Increase k to 10 and tighten the invariant to require >= 2 citations.",
        "Register a real 'retrieve' tool backed by a vector DB (pgvector, "
        "Pinecone, Turbopuffer). The Clawscript code needs zero changes.",
        "Add a second invariant: each citation must correspond to a doc in the "
        "retrieved set (catches fabricated doc-ids).",
        "Emit a 'retrieved' checkpoint per document to capture snippets in "
        "the trace for later dataset construction.",
    ])

    pdf.output("rag_cited-explainer.pdf")
    print("wrote rag_cited-explainer.pdf")


# ============================================================
# LLM JUDGE EXPLAINER
# ============================================================

def build_llm_judge():
    pdf = make_doc("llm_judge.clw -- LLM-as-judge eval harness")
    cover(
        pdf,
        "llm_judge.clw",
        "Structured evaluation with protocol-level\ninvariants on the grader's output.",
        "Turns a fragile LLM grader into a repeatable harness whose trace\n"
        "is a dataset: one 'judged' checkpoint per evaluated case.",
    )

    pdf.add_page()
    pdf.h1("1. What the program does")
    pdf.body(
        "Given a list of (question, answer, rubric) cases, the program asks a "
        "grader model to score each one 1-5 with a one-sentence reason. The "
        "grader is forced into a two-line protocol; any deviation raises "
        "InvariantError. After all cases run, the batch average is computed "
        "and a final invariant gates the batch against a threshold."
    )

    pdf.add_page()
    pdf.h1("2. Why Clawscript fits this problem")
    pdf.body(
        "LLM-as-judge pipelines tend to drift. The grader returns prose, or "
        "switches languages, or invents new score scales. Downstream "
        "dashboards quietly ingest garbage because the parsing is forgiving."
    )
    pdf.body(
        "This harness enforces the contract at the program level: exactly "
        "two lines, strict prefixes, integer score in [1,5]. A grader that "
        "drifts terminates the run at the bad case -- you see the problem "
        "immediately instead of a week later when the dashboard looks funny."
    )
    pdf.callout(
        "Production practice",
        "The 'judged' checkpoint records {question, score, reason} per case. "
        "Pipe the trace into DuckDB or a warehouse and you have per-release "
        "eval rows for free, with no bespoke logger.",
    )

    pdf.add_page()
    pdf.h1("3. Code walk-through")
    pdf.h2("The grader function")
    pdf.mono(
        "@typed\n"
        "def grade(question: str, answer: str, rubric: str) -> dict:"
    )
    pdf.h2("Strict two-line protocol")
    pdf.mono(
        'verdict = prompt(\n'
        '    "claude-sonnet-4-6",\n'
        '    f"You are a strict grader. Score the answer 1-5 using\\n"\n'
        '    f"the rubric. Reply with EXACTLY two lines:\\n"\n'
        '    f"SCORE: <int>\\nREASON: <one sentence>\\n..."\n'
        ')\n'
        'lines = verdict.strip().split("\\n")\n'
        'assert_invariant(len(lines) == 2, ...)\n'
        'assert_invariant(lines[0].startswith("SCORE: "), ...)\n'
        'assert_invariant(lines[1].startswith("REASON: "), ...)'
    )
    pdf.body(
        "Three invariants in a row, each covering one way the grader "
        "historically drifts. None are in the prompt -- they are program "
        "guarantees."
    )

    pdf.add_page()
    pdf.h2("Range check on the score")
    pdf.mono(
        'score = int(lines[0][len("SCORE: "):].strip())\n'
        'assert_invariant(1 <= score <= 5, f"score {score} outside [1,5]")'
    )
    pdf.body(
        "A grader that returns 'SCORE: 10' does not get quietly clamped. It "
        "stops the run and emits invariant_fail with the offending number in "
        "the message."
    )
    pdf.h2("Per-case checkpoint = one dataset row")
    pdf.mono(
        'checkpoint("judged", question=question, score=score, reason=reason)'
    )
    pdf.body(
        "The keyword arguments to checkpoint become fields on the JSONL "
        "record. A later jq or DuckDB query can pull these into a table "
        "with no intermediate ETL."
    )
    pdf.h2("Batch-level gate")
    pdf.mono(
        'avg = sum(r["score"] for r in results) / len(results)\n'
        'assert_invariant(avg >= 3.0, f"eval batch avg {avg} below threshold")'
    )
    pdf.body(
        "Use as a CI gate: fail the build when a newly-trained model "
        "regresses below the threshold."
    )

    pdf.add_page()
    pdf.h1("4. Running it")
    pdf.mono(
        "python3 clw.py examples/llm_judge.clw --trace /tmp/judge.jsonl\n\n"
        "# later, extract a DataFrame of judged cases:\n"
        "jq -c 'select(.event == \"judged\") | .data' \\\n"
        "    /tmp/judge.jsonl > /tmp/rows.jsonl"
    )
    pdf.h2("Variations")
    pdf.bullets([
        "Swap the grader model per run and pin it via the first arg of "
        "prompt() -- the literal-model rule means each row's trace tells "
        "you exactly which grader produced it.",
        "Replace the in-file 'cases' list with a tool('load_dataset', name=...) "
        "call to ingest hundreds of cases without editing the program.",
        "Add a disagreement check: run two graders and assert their scores "
        "are within 1 point, otherwise flag for human review.",
    ])

    pdf.output("llm_judge-explainer.pdf")
    print("wrote llm_judge-explainer.pdf")


# ============================================================
# EXTRACT JSON EXPLAINER
# ============================================================

def build_extract_json():
    pdf = make_doc("extract_json.clw -- Structured extraction with bounded retry")
    cover(
        pdf,
        "extract_json.clw",
        "Structured-output extraction that retries on\nbad JSON -- but never forever.",
        "Demonstrates the classic 'LLM returns bad JSON, try again'\n"
        "pattern written so it literally cannot loop forever.",
    )

    pdf.add_page()
    pdf.h1("1. What the program does")
    pdf.body(
        "Given a free-text bio, the program asks Claude to return a JSON "
        "object with keys {name, age, role} and strict types. On a parse "
        "failure or a schema invariant failure, the retry path fires. After "
        "three failed attempts the program terminates with InvariantError -- "
        "no 'just one more' silent attempt."
    )

    pdf.add_page()
    pdf.h1("2. Why Clawscript fits this problem")
    pdf.body(
        "Structured-output extraction is arguably the most important LLM "
        "workload in production: tickets, resumes, medical notes, invoices. "
        "The failure mode is almost always the same: malformed JSON, missing "
        "field, wrong type."
    )
    pdf.body(
        "Libraries like Instructor solve a piece of this (Pydantic "
        "validation + retry). Clawscript solves a different piece: the "
        "retry has a hard, literal cap in source, and the program cannot be "
        "edited to remove that cap without also removing the @bounded_loop "
        "decorator -- at which point the validator rejects the program."
    )
    pdf.callout(
        "Contrast with prompt-only structured output",
        "A prompt that says 'always return valid JSON' is a suggestion. A "
        "@bounded_loop(3) + parse_json + type invariants chain is a contract.",
    )

    pdf.add_page()
    pdf.h1("3. Code walk-through")
    pdf.h2("Double-decorator on the function")
    pdf.mono(
        "@bounded_loop(3)\n"
        "@typed\n"
        "def extract_person(bio: str) -> dict:"
    )
    pdf.body(
        "Decorators apply outside-in (bottom-up in source). @typed runs "
        "first on the raw function, then @bounded_loop(3) wraps the typed "
        "version. At call time: cap-stack push, typed arg check, body, "
        "typed return check, cap-stack pop."
    )
    pdf.h2("The bounded retry loop")
    pdf.mono(
        "while attempt < 3:\n"
        "    checkpoint(\"extract_try\", n=attempt, last_error=last_error)\n"
        "    raw = prompt(\"claude-sonnet-4-6\", f\"Extract ... Bio: {bio}\")\n"
        "    try:\n"
        "        data = tool(\"parse_json\", text=raw)\n"
        "        # schema invariants follow\n"
        "        return data\n"
        "    except Exception as e:\n"
        "        last_error = repr(e)\n"
        "        attempt = attempt + 1"
    )
    pdf.body(
        "The validator rejects this program if you remove @bounded_loop(3). "
        "The interpreter raises BoundExceeded on a fourth iteration even if "
        "the 'attempt < 3' condition somehow evaluated true. Belt and braces."
    )

    pdf.add_page()
    pdf.h2("The schema invariants")
    pdf.mono(
        'assert_invariant(isinstance(data.get("name"), str), "name must be string")\n'
        'assert_invariant(isinstance(data.get("age"), int), "age must be int")\n'
        'assert_invariant(isinstance(data.get("role"), str), "role must be string")'
    )
    pdf.body(
        "Each invariant raises InvariantError on failure, which propagates "
        "into the try's except block -- triggering a retry. The model gets "
        "three chances to produce a valid shape."
    )
    pdf.h2("The terminal invariant")
    pdf.mono(
        'assert_invariant(False, f"extraction failed after 3 attempts: {last_error}")'
    )
    pdf.body(
        "If the loop exits without returning, the program stops deliberately. "
        "'last_error' carries the most recent exception repr -- the operator "
        "sees WHY extraction failed, not just that it did."
    )

    pdf.add_page()
    pdf.h1("4. Running it")
    pdf.mono(
        "python3 clw.py examples/extract_json.clw --trace /tmp/ex.jsonl"
    )
    pdf.body(
        "With stub mode (no API key), the stub prompt() returns "
        "'[stub response from claude-sonnet-4-6]' which is not valid JSON. "
        "You will see the retry path fire three times then InvariantError. "
        "This is exactly the behavior you want to see in staging when the "
        "real model is misbehaving."
    )
    pdf.h2("What the failing trace looks like")
    pdf.mono(
        '{"event":"checkpoint","label":"extract_try","data":{"n":0}}\n'
        '{"event":"tool_error","name":"parse_json","error":"JSONDecodeError"}\n'
        '{"event":"checkpoint","label":"schema_fail","data":{"error":"..."}}\n'
        '{"event":"checkpoint","label":"extract_try","data":{"n":1}}\n'
        '...\n'
        '{"event":"invariant_fail","message":"extraction failed after 3 attempts"}\n'
        '{"event":"program_end","status":"error"}'
    )
    pdf.h2("Variations")
    pdf.bullets([
        "Replace the manual invariants with a registered JSON-schema "
        "validator tool: tool('validate', schema='person.json', data=data).",
        "Raise the cap to 5 but add a delay between attempts using "
        "tool('sleep', seconds=1).",
        "Emit the raw model output on each failure as part of the "
        "schema_fail checkpoint -- critical for debugging in production.",
    ])

    pdf.output("extract_json-explainer.pdf")
    print("wrote extract_json-explainer.pdf")


# ============================================================
# REACT AGENT EXPLAINER
# ============================================================

def build_react_agent():
    pdf = make_doc("react_agent.clw -- Bounded ReAct tool loop")
    cover(
        pdf,
        "react_agent.clw",
        "A ReAct-style agent loop that cannot\nspin past its iteration cap.",
        "The 'model picks tools until done' pattern written so the\n"
        "interpreter -- not the model -- enforces the stopping rule.",
    )

    pdf.add_page()
    pdf.h1("1. What the program does")
    pdf.body(
        "Given a task, the program iteratively asks Claude for the next "
        "action. Each turn the model must reply with exactly one line: "
        "either ACTION: <tool>|<arg> or FINAL: <answer>. Actions are "
        "dispatched to the tool registry; the result is fed back into the "
        "history. FINAL terminates the loop. Any protocol drift triggers "
        "InvariantError. A seventh iteration is not possible -- the "
        "@bounded_loop(6) decorator stops the interpreter before that."
    )

    pdf.add_page()
    pdf.h1("2. Why Clawscript fits this problem")
    pdf.body(
        "ReAct agents are the canonical 'let the model drive' pattern. They "
        "are also the canonical way to burn $50 on a single query when the "
        "agent forgets the stopping condition and loops over web searches "
        "forever."
    )
    pdf.body(
        "Prompt-level stopping rules ('when you are done, say FINAL') are "
        "ignored about 1% of the time. At a million queries a day that is "
        "ten thousand runaway agents per day. @bounded_loop(6) makes this "
        "class of failure structurally impossible: the interpreter raises "
        "BoundExceeded and the program exits with a typed error you can "
        "alert on."
    )
    pdf.callout(
        "Financial framing",
        "Use @bounded_loop(N) as a budget dial. N=6 with ~2 prompts per "
        "iteration and an average 1k token output is a ceiling of maybe a "
        "few cents per run. The cap is the fundamental reason a CFO trusts "
        "shipping agent code.",
    )

    pdf.add_page()
    pdf.h1("3. Code walk-through")
    pdf.h2("The stopping rule in one line")
    pdf.mono("@bounded_loop(6)")
    pdf.body(
        "This is the budget. Six iterations, no more. The interpreter "
        "enforces this even if the body of the while loop is buggy."
    )
    pdf.h2("Forcing the model into a protocol")
    pdf.mono(
        'decision = prompt(\n'
        '    "claude-sonnet-4-6",\n'
        '    f"Reply with EITHER\\n"\n'
        '    f"  ACTION: <tool_name>|<arg>\\n"\n'
        '    f"OR\\n"\n'
        '    f"  FINAL: <answer>\\n"\n'
        '    f"Pipe-separated, one line, no preamble.\\n\\n"\n'
        '    f"Tools: search, calc\\n\\nTask: {task}\\n\\nHistory:\\n{state}"\n'
        ')\n'
        'first_line = decision.strip().split("\\n")[0]'
    )
    pdf.body(
        "Taking only the first line defends against a model that produces "
        "an explanation-then-action. Pair this with strict prefix checks."
    )

    pdf.add_page()
    pdf.h2("Protocol enforcement")
    pdf.mono(
        'if first_line.startswith("FINAL:"):\n'
        '    answer = first_line[len("FINAL:"):].strip()\n'
        '    checkpoint("react_done", steps=step + 1, answer=answer)\n'
        '    return answer\n\n'
        'assert_invariant(\n'
        '    first_line.startswith("ACTION:"),\n'
        '    f"protocol violation at step {step}"\n'
        ')'
    )
    pdf.body(
        "FINAL is a success exit. Anything that is neither FINAL nor ACTION "
        "is a protocol violation and halts. The model does not get to "
        "improvise a third kind of response."
    )
    pdf.h2("Dispatching the action")
    pdf.mono(
        'body = first_line[len("ACTION:"):].strip()\n'
        'parts = body.split("|", 1)\n'
        'assert_invariant(len(parts) == 2, f"bad ACTION format: {body!r}")\n'
        'name = parts[0].strip()\n'
        'arg = parts[1].strip()\n'
        'result = tool(name, arg=arg)'
    )
    pdf.body(
        "A simple pipe-separated format keeps parsing one line of code. "
        "For production, replace this with a JSON action format and the "
        "parse_json tool -- the rest of the program is unaffected."
    )

    pdf.add_page()
    pdf.h1("4. Running it")
    pdf.mono(
        "python3 clw.py examples/react_agent.clw --trace /tmp/react.jsonl"
    )
    pdf.h2("What a successful run looks like")
    pdf.mono(
        '{"event":"checkpoint","label":"react_step","data":{"n":0,...}}\n'
        '{"event":"prompt_begin","model":"claude-sonnet-4-6"}\n'
        '{"event":"prompt_end","tokens_in":...,"tokens_out":...}\n'
        '{"event":"tool_begin","name":"search","kwargs":{"arg":"France"}}\n'
        '{"event":"tool_end","name":"search"}\n'
        '{"event":"checkpoint","label":"react_step","data":{"n":1,...}}\n'
        '...\n'
        '{"event":"checkpoint","label":"react_done","data":{"steps":3,"answer":"..."}}'
    )
    pdf.h2("What a runaway run would look like")
    pdf.body(
        "It wouldn't. After the sixth iteration the interpreter raises "
        "BoundExceeded and emits program_end with status=error. There is "
        "no runaway state to describe."
    )
    pdf.h2("Extending it")
    pdf.bullets([
        "Swap the pipe protocol for JSON: `{\"action\":\"search\",\"arg\":\"...\"}`. "
        "Use tool('parse_json', text=line) to parse.",
        "Add more tools to the registry in clw.py main(): web_fetch, sql_query, "
        "file_read. The program does not change.",
        "Replace the terminal invariant with a graceful fallback: when the "
        "cap is exhausted, return the last state as a partial answer.",
        "Emit a 'cost_estimate' checkpoint per step using token counts from "
        "the previous prompt_end record for live budget alerts.",
    ])

    pdf.output("react_agent-explainer.pdf")
    print("wrote react_agent-explainer.pdf")


# ============================================================
# SETUP AND DEPLOY GUIDE
# ============================================================

def build_setup_guide():
    pdf = make_doc("Clawscript -- Setup, Running, Deploying")
    cover(
        pdf,
        "Clawscript",
        "Setup, running, and deploying .clw scripts.",
        "A hands-on guide covering prerequisites through production deployment,\n"
        "written for a developer who has never touched the language.",
    )

    # --- TOC ---
    pdf.add_page()
    pdf.h1("Contents")
    toc = [
        "1. Prerequisites",
        "2. Installing Clawscript",
        "3. Your first .clw program",
        "4. Project layout",
        "5. Running programs -- three modes",
        "6. The tool registry",
        "7. Writing programs -- conventions and pitfalls",
        "8. Error handling patterns",
        "9. Testing and validation",
        "10. Debugging via traces",
        "11. Deploying -- containerization",
        "12. Deploying -- CI/CD",
        "13. Deploying -- runtime platforms (Lambda, Fluid Compute, K8s)",
        "14. Observability and log aggregation",
        "15. Security notes",
        "16. Upgrading and versioning programs",
        "17. FAQ and gotchas",
    ]
    pdf.numbered(toc)

    # --- 1. Prerequisites ---
    pdf.add_page()
    pdf.h1("1. Prerequisites")
    pdf.body(
        "Clawscript has two components: the reference interpreter (pure "
        "Python, ~480 LOC, one file) and optionally the Anthropic Python "
        "SDK for real model calls. You need:"
    )
    pdf.bullets([
        "Python 3.9 or newer. The interpreter uses only the standard "
        "library plus one optional dependency.",
        "Optional: anthropic (pip install anthropic). Without it the "
        "interpreter runs in stub mode -- useful for development and CI.",
        "Optional: an Anthropic API key. Export ANTHROPIC_API_KEY=sk-ant-... "
        "before running in real mode.",
        "Optional: jq, DuckDB, or any JSONL-capable tool for reading the "
        "trace output.",
    ])
    pdf.h2("OS support")
    pdf.body(
        "Linux, macOS, and Windows (via WSL or native Python). No "
        "OS-specific dependencies."
    )

    # --- 2. Install ---
    pdf.add_page()
    pdf.h1("2. Installing Clawscript")
    pdf.body(
        "Clawscript ships as a single file: clw.py. There is no package "
        "to install from PyPI in v0.1. Clone or copy the file into your "
        "project."
    )
    pdf.h2("Minimum install -- copy one file")
    pdf.mono(
        "# clone the repo\n"
        "git clone https://github.com/<org>/clawscript.git\n"
        "cd clawscript\n\n"
        "# or copy just the interpreter into an existing project\n"
        "curl -o clw.py https://raw.githubusercontent.com/<org>/clawscript/main/clw.py"
    )
    pdf.h2("Install the optional SDK")
    pdf.mono(
        "python3 -m pip install anthropic\n"
        "export ANTHROPIC_API_KEY=sk-ant-...\n"
        "# verify:\n"
        "python3 -c \"import anthropic; print(anthropic.__version__)\""
    )
    pdf.h2("Sanity-check the interpreter")
    pdf.mono(
        "python3 clw.py --help\n"
        "# usage: python clw.py <program.clw> [--trace trace.jsonl]"
    )

    # --- 3. First program ---
    pdf.add_page()
    pdf.h1("3. Your first .clw program")
    pdf.body(
        "Write this file as hello.clw:"
    )
    pdf.mono(
        "# hello.clw\n\n"
        "@typed\n"
        "def greet(name: str) -> str:\n"
        "    checkpoint(\"enter\", name=name)\n"
        "    assert_invariant(len(name) > 0, \"name required\")\n"
        "    message = f\"hello, {name}\"\n"
        "    checkpoint(\"done\", chars=len(message))\n"
        "    return message\n\n"
        "print(greet(\"world\"))"
    )
    pdf.body("Run it:")
    pdf.mono("python3 clw.py hello.clw")
    pdf.body("Expected output (trace lines plus your print):")
    pdf.mono(
        '{"step":1,"event":"program_start","file":"hello.clw"}\n'
        '{"step":2,"event":"step","node":"FunctionDef","line":3}\n'
        '{"step":3,"event":"step","node":"Expr","line":10}\n'
        '...\n'
        '{"step":N,"event":"checkpoint","label":"done",...}\n'
        "hello, world"
    )
    pdf.callout(
        "Trace goes to stdout by default",
        "If you want only your print output on screen and the trace on disk, "
        "use --trace: python3 clw.py hello.clw --trace hello.jsonl",
    )

    # --- 4. Project layout ---
    pdf.add_page()
    pdf.h1("4. Project layout")
    pdf.body("A typical Clawscript project looks like:")
    pdf.mono(
        "my-agent/\n"
        "  clw.py                  # the interpreter (copied in)\n"
        "  tools.py                # your tool registry\n"
        "  runtime.py              # wires tracer/client/approver/tools\n"
        "  programs/\n"
        "    ingest.clw\n"
        "    classify.clw\n"
        "    report.clw\n"
        "  tests/\n"
        "    test_ingest.py        # validator-level and stubbed-run tests\n"
        "  traces/                 # gitignored\n"
        "  Dockerfile\n"
        "  requirements.txt        # anthropic, optional extras\n"
        "  README.md"
    )
    pdf.body(
        "The interpreter is a library -- import it from runtime.py rather "
        "than shelling out, if you want to pass a custom tool registry or "
        "approver."
    )
    pdf.h2("runtime.py minimum")
    pdf.mono(
        "import os, sys, anthropic\n"
        "from cls import Interpreter, Tracer\n"
        "from tools import REGISTRY\n\n"
        "def main(path):\n"
        "    tracer = Tracer(open(\"traces/run.jsonl\", \"w\"))\n"
        "    client = anthropic.Anthropic() if os.environ.get(\"ANTHROPIC_API_KEY\") else None\n"
        "    interp = Interpreter(tracer=tracer, client=client, tools=REGISTRY)\n"
        "    with open(path) as f:\n"
        "        interp.run(f.read(), filename=path)\n\n"
        "if __name__ == \"__main__\":\n"
        "    main(sys.argv[1])"
    )

    # --- 5. Running modes ---
    pdf.add_page()
    pdf.h1("5. Running programs -- three modes")
    pdf.h2("Stub mode (no API key)")
    pdf.body(
        "prompt() returns a placeholder string. Fast, deterministic, free. "
        "Use for: validator testing, flow-control checks, CI sanity."
    )
    pdf.mono("python3 clw.py programs/ingest.clw")
    pdf.h2("Real mode (with API key)")
    pdf.body(
        "prompt() dispatches to Claude. Use for: staging runs, golden-path "
        "evaluation, production."
    )
    pdf.mono(
        "export ANTHROPIC_API_KEY=sk-ant-...\n"
        "python3 clw.py programs/ingest.clw --trace traces/$(date +%s).jsonl"
    )
    pdf.h2("Embedded mode (library)")
    pdf.body(
        "Import cls in your own Python program. Useful for wrapping Clawscript "
        "with retries, scheduling, or when Clawscript is one step in a larger "
        "pipeline."
    )
    pdf.mono(
        "from cls import Interpreter, Tracer\n"
        "interp = Interpreter(tracer=Tracer(sink=my_sink), tools=my_tools)\n"
        "interp.run(source=program_text, filename='inline')"
    )
    pdf.h2("Validation-only mode")
    pdf.body(
        "Useful in pre-commit or CI: parse and validate without executing. "
        "One-liner:"
    )
    pdf.mono(
        "python3 -c \"import ast, sys; from cls import Validator; \\\n"
        "v = Validator(); v.visit(ast.parse(open(sys.argv[1]).read())); \\\n"
        "print(v.errors or 'OK')\" programs/ingest.clw"
    )

    # --- 6. Tool registry ---
    pdf.add_page()
    pdf.h1("6. The tool registry")
    pdf.body(
        "The registry is the only escape hatch from Clawscript back into arbitrary "
        "Python. Every tool is a callable mapped to a string name."
    )
    pdf.h2("Defining tools")
    pdf.mono(
        "# tools.py\n"
        "import json, httpx, psycopg\n\n"
        "def http_get(url: str) -> str:\n"
        "    return httpx.get(url, timeout=30).text\n\n"
        "def pg_query(sql: str) -> list:\n"
        "    with psycopg.connect() as c:\n"
        "        return c.execute(sql).fetchall()\n\n"
        "def parse_json(text: str):\n"
        "    return json.loads(text)\n\n"
        "REGISTRY = {\n"
        "    \"http_get\": http_get,\n"
        "    \"pg_query\": pg_query,\n"
        "    \"parse_json\": parse_json,\n"
        "}"
    )
    pdf.h2("Tool design rules")
    pdf.bullets([
        "Tools should be pure in intent: same input, same output, side "
        "effects are explicit. This is what makes traces replay-usable.",
        "Raise typed exceptions. The Clawscript program's try/except clauses rely "
        "on type matching.",
        "Do not retry inside a tool. Let the Clawscript program decide via "
        "@bounded_loop -- that is the whole point.",
        "Keep tool kwarg names stable. Renames are a breaking change.",
        "Validate kwargs at the boundary with a typed signature -- your "
        "CLS program inherits the type safety.",
    ])

    # --- 7. Writing programs ---
    pdf.add_page()
    pdf.h1("7. Writing programs -- conventions and pitfalls")
    pdf.h2("Conventions")
    pdf.bullets([
        "Wrap every public function with @typed. Cheap, catches mistakes "
        "from LLM-generated code paths that fan into your function.",
        "Emit a checkpoint at the START and END of each phase, plus at "
        "every invariant pass and every retry.",
        "Use f-strings for prompts. They are as static as literals but "
        "compose with bound variables -- the validator allows both.",
        "Pin every prompt to an exact model string. Operators should be "
        "able to grep the program for 'claude-' and see what runs where.",
        "Give checkpoints a small, finite vocabulary of labels. 'start', "
        "'fetched', 'summarized', 'done'. Not 'call_1_success'.",
    ])
    pdf.h2("Pitfalls")
    pdf.bullets([
        "Forgetting @bounded_loop(N) on a function with a while -- caught "
        "at validation, but surprising if you expected the file to run.",
        "Using a variable as the prompt's model argument -- validator rejects. "
        "Hardcode the model or move the variant choice into the tool layer.",
        "Catching 'except Exception' too broadly and hiding programming "
        "errors. Narrow the exception type or re-raise after logging.",
        "Assuming tool()'s exact-name lookup is case-insensitive. It is "
        "not. 'HTTP_GET' is not 'http_get'.",
        "Relying on print() for debugging in production -- use checkpoint() "
        "with kwargs instead, so the data is structured.",
    ])

    # --- 8. Error handling ---
    pdf.add_page()
    pdf.h1("8. Error handling patterns")
    pdf.h2("Pattern A -- retry a narrow condition")
    pdf.mono(
        "@bounded_loop(3)\n"
        "def call_with_retry(url: str) -> str:\n"
        "    attempt = 0\n"
        "    while attempt < 3:\n"
        "        try:\n"
        "            return tool(\"http_get\", url=url)\n"
        "        except TimeoutError:\n"
        "            attempt = attempt + 1\n"
        "    assert_invariant(False, \"timed out three times\")\n"
        "    return \"\""
    )
    pdf.h2("Pattern B -- fail closed with a graceful message")
    pdf.mono(
        "try:\n"
        "    data = tool(\"parse_json\", text=raw)\n"
        "except Exception as e:\n"
        "    checkpoint(\"parse_failed\", error=repr(e))\n"
        "    return {\"status\": \"unavailable\"}"
    )
    pdf.h2("Pattern C -- hard gate with operator approval")
    pdf.mono(
        "try:\n"
        "    require_approval(f\"delete table {table}\")\n"
        "    tool(\"pg_query\", sql=f\"DROP TABLE {table}\")\n"
        "except ApprovalDenied:\n"
        "    checkpoint(\"declined\", table=table)\n"
        "    return False"
    )
    pdf.h2("Pattern D -- never eat InvariantError")
    pdf.body(
        "Do not wrap an invariant in try/except. That defeats the purpose. "
        "If you find yourself doing it, the check is misplaced -- move it "
        "earlier, or convert the failure into data."
    )

    # --- 9. Testing ---
    pdf.add_page()
    pdf.h1("9. Testing and validation")
    pdf.body(
        "CLS programs are testable at three levels. Each has a different "
        "cost-to-signal ratio."
    )
    pdf.h2("Level 1 -- validator-only (milliseconds, deterministic)")
    pdf.mono(
        "import ast\n"
        "from cls import Validator\n\n"
        "def test_program_valid():\n"
        "    src = open(\"programs/ingest.clw\").read()\n"
        "    v = Validator(); v.visit(ast.parse(src))\n"
        "    assert v.errors == []"
    )
    pdf.h2("Level 2 -- stubbed interpreter (seconds, deterministic)")
    pdf.mono(
        "from cls import Interpreter, Tracer\n\n"
        "def test_ingest_golden():\n"
        "    captured = []\n"
        "    class Sink:\n"
        "        def write(self, s): captured.append(s)\n"
        "        def flush(self): pass\n"
        "    fake_tools = {\"http_get\": lambda url: \"stub body\"}\n"
        "    Interpreter(tracer=Tracer(Sink()), tools=fake_tools, client=None).run(\n"
        "        open(\"programs/ingest.clw\").read(), \"ingest.clw\")\n"
        "    assert any(\"program_end\" in line and \"ok\" in line for line in captured)"
    )
    pdf.h2("Level 3 -- real API (slow, non-deterministic; run nightly)")
    pdf.body(
        "Use a golden-trace approach: run against the real API once, store "
        "the trace events (labels and shapes, not the LLM text), assert "
        "those shapes in CI. Treat text drift as information, not failure."
    )

    # --- 10. Debugging ---
    pdf.add_page()
    pdf.h1("10. Debugging via traces")
    pdf.body(
        "Every run emits a complete JSONL timeline. Some useful one-liners:"
    )
    pdf.h2("Show every checkpoint label")
    pdf.mono(
        "jq -r 'select(.event==\"checkpoint\") | .label' traces/run.jsonl \\\n"
        "    | sort | uniq -c"
    )
    pdf.h2("Every failed invariant in the last week of runs")
    pdf.mono(
        "for f in traces/*.jsonl; do\n"
        "  jq -r 'select(.event==\"invariant_fail\") | [input_filename, .message] | @tsv' \"$f\"\n"
        "done"
    )
    pdf.h2("Per-run token totals")
    pdf.mono(
        "jq -r 'select(.event==\"prompt_end\") | [.tokens_in, .tokens_out] | @tsv' \\\n"
        "    traces/run.jsonl | awk '{i+=$1; o+=$2} END {print i,o}'"
    )
    pdf.h2("Render a timeline as a flamegraph-like view")
    pdf.body(
        "Load the JSONL into DuckDB, compute elapsed time between step and "
        "the next step on the same line, and plot a simple Gantt chart. "
        "For ad-hoc investigations, Observable notebooks on JSONL work well."
    )
    pdf.callout(
        "Structured > unstructured",
        "Resist the urge to add print() statements. A new event name in "
        "checkpoint(label='new_event', ...) is a better debugger because "
        "it survives into production logs.",
    )

    # --- 11. Container ---
    pdf.add_page()
    pdf.h1("11. Deploying -- containerization")
    pdf.h2("Minimal Dockerfile")
    pdf.mono(
        "FROM python:3.12-slim\n\n"
        "WORKDIR /app\n"
        "COPY requirements.txt ./\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n\n"
        "COPY clw.py tools.py runtime.py ./\n"
        "COPY programs/ programs/\n\n"
        "ENV PYTHONUNBUFFERED=1\n"
        "CMD [\"python\", \"runtime.py\", \"programs/ingest.clw\"]"
    )
    pdf.h2("Tips")
    pdf.bullets([
        "Keep the image slim: clw.py has no compiled dependencies.",
        "Do not bake ANTHROPIC_API_KEY into the image. Pass via env at "
        "runtime.",
        "Mount /traces as a volume so JSONL outputs survive container "
        "restarts, or ship them to a collector (see section 14).",
        "Run as a non-root user and disable shell access; tools can call "
        "arbitrary Python.",
    ])

    # --- 12. CI/CD ---
    pdf.add_page()
    pdf.h1("12. Deploying -- CI/CD")
    pdf.h2("GitHub Actions skeleton")
    pdf.mono(
        "name: ci\n"
        "on: [pull_request, push]\n"
        "jobs:\n"
        "  validate:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "        with: { python-version: '3.12' }\n"
        "      - name: Validate Clawscript programs\n"
        "        run: |\n"
        "          for f in programs/*.clw; do\n"
        "            python3 -c \"import ast; from cls import Validator; \\\n"
        "            v=Validator(); v.visit(ast.parse(open('$f').read())); \\\n"
        "            assert v.errors == [], v.errors\"\n"
        "          done\n"
        "      - name: Stubbed smoke tests\n"
        "        run: pytest tests/"
    )
    pdf.h2("Deploy pipeline patterns")
    pdf.bullets([
        "Validation gate before build: a program that fails the Clawscript "
        "validator must never ship. Bake this into required checks.",
        "Stubbed smoke tests on every PR. Catch flow-level regressions "
        "without paying for LLM calls.",
        "Real-API evals on a schedule (nightly / pre-release). Compare a "
        "golden trace shape to the current run. Flag drift.",
        "Canary deploys: roll out new programs to a small traffic slice, "
        "watch the invariant_fail rate in logs, promote or revert.",
    ])

    # --- 13. Runtime platforms ---
    pdf.add_page()
    pdf.h1("13. Deploying -- runtime platforms")
    pdf.h2("AWS Lambda (or Google Cloud Functions)")
    pdf.body(
        "Package clw.py, tools.py, and programs/ into a Lambda function. "
        "Handler calls interp.run on an event-specified program path. "
        "Beware timeout limits: pick @bounded_loop caps with Lambda's "
        "900-second ceiling in mind, and use CloudWatch for JSONL ingest."
    )
    pdf.h2("Vercel Fluid Compute")
    pdf.body(
        "Fluid Compute reuses function instances across concurrent requests, "
        "which pairs well with an Interpreter instance per request. The "
        "default 300-second timeout is generous for most agent runs. "
        "Traces go to stdout and flow to Vercel Logs."
    )
    pdf.h2("Kubernetes / long-running service")
    pdf.body(
        "Wrap the interpreter in an HTTP or gRPC server. One request = one "
        "program run. Keep the registry warm; mount a volume for trace "
        "output, or ship to a log aggregator."
    )
    pdf.h2("Durable execution (Temporal, Inngest, Vercel Workflow)")
    pdf.body(
        "For long-running agents that need to survive process restarts, "
        "run each Clawscript step as a durable workflow activity. Replace the "
        "built-in bounded_loop with a workflow-level retry policy when "
        "appropriate."
    )
    pdf.callout(
        "Rule of thumb",
        "Short, stateless runs -- Lambda / Fluid Compute. Long, "
        "stateful runs with human-in-the-loop pauses -- Temporal or a "
        "workflow engine. Batch jobs -- Kubernetes or Airflow DAGs.",
    )

    # --- 14. Observability ---
    pdf.add_page()
    pdf.h1("14. Observability and log aggregation")
    pdf.body(
        "The JSONL trace is the primary observability surface. Treat it "
        "like structured application logs."
    )
    pdf.h2("Recommended stack")
    pdf.bullets([
        "Ship JSONL to any log aggregator (Datadog, Honeycomb, Loki, "
        "CloudWatch). One field per record means facet-friendly.",
        "Build dashboards on the 'event' field. Useful panels: invariant_fail "
        "rate, average prompt_end duration per model, tool_error count by "
        "name, approval_requested volume.",
        "Alert on event=='invariant_fail' OR event=='program_end' && "
        "status=='error'. These are nearly always user-visible issues.",
        "Retain traces indefinitely if the workload is regulated. They are "
        "small (a few KB per run), and the per-step granularity is the "
        "compliance artifact.",
    ])
    pdf.h2("Replaying a run")
    pdf.body(
        "A trace is not a full replay yet, but it is a full decision log. "
        "With the same program version and the same tool registry, the "
        "checkpoint sequence is a high-fidelity reproduction target. "
        "Future versions of Clawscript aim for full deterministic replay by "
        "recording prompt outputs alongside the trace."
    )

    # --- 15. Security ---
    pdf.add_page()
    pdf.h1("15. Security notes")
    pdf.callout(
        "The reference interpreter is NOT a sandbox.",
        "clw.py uses Python's eval() for expressions with a safe-builtin "
        "allow-list. That is not sufficient isolation for running untrusted "
        "programs -- tools themselves can call arbitrary Python. Run "
        "untrusted Clawscript in a subprocess, container, or dedicated VM.",
    )
    pdf.h2("Threat model for trusted-program deployments")
    pdf.bullets([
        "Tool inputs come from LLM output. Treat every tool argument as "
        "untrusted text. Validate aggressively inside the tool.",
        "Prompts can contain user-supplied text. Use f-strings to compose "
        "-- but escape/sanitize any user content that could inject "
        "instructions (prompt injection).",
        "Tools that make network calls should have explicit allow-lists "
        "of destinations.",
        "Require_approval is a UI primitive; the approver function is part "
        "of your trust boundary -- ensure it authenticates the human.",
    ])
    pdf.h2("Key handling")
    pdf.bullets([
        "Never hard-code API keys. Use environment variables.",
        "Rotate keys on a schedule. Clawscript reads the key at Interpreter "
        "construction time.",
        "For multi-tenant platforms, consider a per-tenant client with "
        "Anthropic usage tracking and per-tenant rate limits.",
    ])

    # --- 16. Versioning ---
    pdf.add_page()
    pdf.h1("16. Upgrading and versioning programs")
    pdf.body(
        "CLS programs are deterministic artifacts. Version them explicitly."
    )
    pdf.bullets([
        "Store programs in git. The validator makes diffs cheap to review.",
        "Tag every production run with the program commit hash. Include "
        "it in the first checkpoint: checkpoint('start', git_sha=...).",
        "When changing a prompt, bump a version string in the checkpoint "
        "label family: 'summarize_v2'. Old traces remain queryable by v1.",
        "Pin models in source. When rotating to a newer Claude version, "
        "run the new program side-by-side with the old one, compare trace "
        "shapes and eval scores before cutting over.",
    ])
    pdf.h2("Deprecating a tool")
    pdf.body(
        "Keep the old tool name as an alias to the new implementation for "
        "one release cycle. Emit a checkpoint('deprecated_tool', name=...) "
        "from the alias so you can find remaining callers in traces."
    )

    # --- 17. FAQ ---
    pdf.add_page()
    pdf.h1("17. FAQ and gotchas")
    pdf.h3("Why can't I import?")
    pdf.body(
        "Imports are the easiest way to introduce non-determinism and "
        "hidden state. Clawscript forbids them; put the dependency behind a tool "
        "instead. You pay one registry entry and gain traceable access."
    )
    pdf.h3("Why must the prompt model be a literal?")
    pdf.body(
        "Auditability. 'Which model ran this step?' must be answerable by "
        "grep on the source. A dynamic model argument makes the answer "
        "'it depends on what was passed in'."
    )
    pdf.h3("Why does prompt() text have to be a literal or f-string?")
    pdf.body(
        "Same reason. The full prompt must be reconstructible from the "
        "source plus bound values. Hiding it behind build_prompt(x, y) "
        "defeats the visibility property."
    )
    pdf.h3("Can I use async?")
    pdf.body(
        "Not in v0.1. The grammar reserves the keyword; semantics are a "
        "future project. For concurrency, run multiple interpreters in "
        "parallel processes."
    )
    pdf.h3("Can I mutate a bound variable inside a list comprehension?")
    pdf.body(
        "Comprehensions evaluate via Python's eval, so standard Python "
        "scoping applies. Prefer explicit for-loops when you want the "
        "mutation to be visible in the step trace."
    )
    pdf.h3("Why did my while loop raise BoundExceeded even though the condition should be false?")
    pdf.body(
        "The cap check runs at the TOP of each iteration, before the "
        "condition. If you set the bound to N and the loop is ever about "
        "to enter a (N+1)th iteration, the interpreter stops it -- even "
        "if the condition would have terminated naturally. Raise the cap "
        "or restructure the loop."
    )

    pdf.output("SETUP-AND-DEPLOY.pdf")
    print("wrote SETUP-AND-DEPLOY.pdf")


def main():
    build_rag_cited()
    build_llm_judge()
    build_extract_json()
    build_react_agent()
    build_setup_guide()


if __name__ == "__main__":
    main()
