# Clawscript Launch Playbook

Concrete, sequenced steps for taking Clawscript from "public repo" to
"Hacker News front page" without face-planting. Written in the order
you should execute it.

---

## Phase 0 — Before you post (48 hours out)

1. **Add a LICENSE file.**
   All-rights-reserved gets dogpiled on HN and blocks any corporate
   adopter. Pick MIT or Apache-2.0. One minute of work; outsize
   reputational payoff. Commit as `LICENSE`, commit message "Add MIT
   license".

2. **Verify the demo GIF plays cleanly in the README on GitHub.**
   Open `https://github.com/will-march/clawscript` on both desktop and
   mobile. GitHub caches GIFs aggressively; if anything looks wrong,
   regenerate `clawscript-demo.gif` with `vhs demo.tape` and push.

3. **Ship a side-by-side snippet.**
   Add a small block to the README showing the same retry logic in:
   (a) Clawscript, (b) LangChain, (c) raw `anthropic` SDK. Visual
   comparison sells in seconds.

4. **Star your own repo from a second account.**
   Zero stars at submission time reads "nobody cares yet." Target
   ~10 stars pre-launch via one private ping to close friends.

5. **A/B test titles with three trusted technical friends.**
   Title options live in `HN-POST.md`. HN title choice is the biggest
   single lever for front-page fate.

6. **Rehearse the first five HN replies.**
   The comments you will absolutely get: "this is just LangGraph",
   "why not BAML / Instructor", "480 LOC is not a language", "this
   is limiting". Have honest 1-2 sentence responses pre-written.

---

## Phase 1 — Launch day (Tue or Wed)

1. **Submit at 08:15 PT.**
   The HN algorithm gives a post ~90 minutes to earn front-page rank.
   Submit during US morning commute so voters are fresh.

2. **Block your calendar from 08:00-11:00 PT.**
   You must be at your keyboard. Every comment in the first two hours
   is high-leverage.

3. **Post a single X thread.**
   3-4 tweets. Link the HN story, embed the 45-second demo GIF,
   one-sentence pitch per tweet.
   Tag: `@AnthropicAI @simonw @swyx @jxnlco @hwchase17 @omarsar0`.
   One thread, not a flurry. Quality > volume.

4. **Cross-post (staggered across the day):**
   - `r/LocalLLaMA` at 10:00 PT (friendly, technical).
   - `lobste.rs` at 11:00 PT (smaller, higher-signal).
   - Anthropic Discord `#showcase` channel at noon PT (if it exists).
   - `r/programming` at 14:00 PT (tougher crowd — only if HN is going
     well).
   - **Not** `r/MachineLearning` — self-promotion is banned and will
     get you shadowbanned.

5. **Respond to every HN comment within 15 minutes for the first two
   hours.**
   After that, within an hour for the rest of the day. Acknowledge
   prior art generously. "Good point, I should have mentioned X" wins
   more mindshare than a defense.

6. **Do not argue.**
   If a commenter misunderstands, clarify once. If they persist, leave
   them. Every hostile thread you extend is a thread pushing you off
   the front page.

---

## Phase 2 — Objection-handling cheat sheet

Keep this open in a scratch tab during launch.

| Likely comment | Your response |
|---|---|
| "This is just LangGraph" | "LangGraph is a graph-construction API — you build a StateGraph object. Clawscript is a *language* you write. Different ergonomics; pick what fits." |
| "Why not Instructor / BAML?" | "Structured output is orthogonal. Clawscript handles flow. You can call a schema validator via `tool()` inside a Clawscript program." |
| "480 LOC isn't a language" | "Correct, it's a reference interpreter. The language is grammar + validator + semantics. The LOC is a feature — read it all before committing." |
| "This is limiting" | "Yes, that's the product. If you want flexibility, use Skills." |
| "How is this deterministic if the model is stochastic?" | "Control flow is deterministic from bound values. Prompt *outputs* remain model-stochastic; replayable mode is on the roadmap, not claimed today." |
| "Can't I do this with a decorator + dict?" | "Yes. The interpreter is the point: it enforces the rules at parse time so your program fails fast, and it produces a uniform trace format." |
| "Trademark on 'Claw'?" | "Different mark from 'Claude'. Happy to rename if Anthropic objects." |
| "Why Python syntax instead of your own?" | "Because `ast.parse` is a free parser and every editor already knows the grammar. The cost of inventing a grammar is high; the benefit vs Python is small." |

---

## Phase 3 — Content to ship in week 1

Shipping two blog posts + one short video in the first week doubles the
tail on a successful HN launch.

1. **Blog post 1 — "I spent $300 in one afternoon on a looping agent.
   So I wrote a language."**
   - The itch story. First-person. Concrete.
   - Publish on dev.to or Substack. Cross-post to Hashnode.
   - Link from a fresh HN comment on your original post: "wrote up the
     origin story here".

2. **Blog post 2 — "Debugging an LLM agent from a JSONL trace."**
   - Technical walkthrough. Screenshot-heavy.
   - Show the jq / DuckDB / Observable workflow.
   - Publish 4-5 days after post 1.

3. **8-minute Loom or YouTube walkthrough.**
   - Live code a new example end-to-end.
   - Post to `r/MachineLearning` (tutorials are allowed; self-promotion
     isn't).

---

## Phase 4 — Metrics to watch

| Metric | Target (first 48h) | How to check |
|---|---|---|
| HN points | 150+ for front page | HN live |
| Repo stars | 200+ | `gh api repos/will-march/clawscript \| jq .stargazers_count` |
| Unique cloners | 50+ | `gh api repos/will-march/clawscript/traffic/clones` |
| Referrer breakdown | HN > X > Reddit | GitHub → Insights → Traffic |
| Issues / PRs | Respond within 2h | GitHub notifications |
| README dwell time | n/a (not trackable without Plausible) | - |

**Non-metrics to ignore:** Twitter likes (vanity), share count on
Reddit (noise), HN karma (noise). Stars and clones are the only
durable signal.

---

## Phase 5 — Amplification (week 2 and beyond)

1. **Direct outreach to 3-5 adjacent AI infra founders.**
   BAML, Inngest, Temporal, DSPy maintainers, Instructor (Jason Liu).
   "I built something adjacent to X — open to a chat?" They may
   retweet, mention in their newsletter, or just share useful feedback.

2. **Newsletter pitches:**
   - Latent.space — guest essay.
   - Dan Mac's AI newsletter — pitch as a dev tool roundup item.
   - The Pragmatic Engineer — only if you have a production adopter
     story; Gergely wants case studies, not tool announcements.
   - Simon Willison's weeknotes — he covers interesting tools weekly;
     DM on Mastodon or tag him on a specific feature.

3. **Talks:**
   - PyCon 2027 CFP opens ~Nov 2026 — lightning talk pitch: "A 480-line
     DSL for auditable LLM agents".
   - AI Engineer Summit — rolling submissions.
   - Local AI / ML meetups in SF / NYC / Berlin / London — most are
     hungry for talks.

4. **Follow-up HN post — 6-8 weeks later.**
   Rule: do not resubmit the same story. The follow-up must have a
   genuinely new feature or a production case study. Good candidates:
   (a) full replay mode, (b) LSP server for editor support,
   (c) "We shipped Clawscript at [company] and here's what broke".

---

## Phase 6 — When to give up or pivot

Realistic cutoff: **if after 3 months you have <50 stars and zero
external contributors, the market has told you this is a personal
tool, not a product.**

That is a legitimate outcome. Your next move:

1. Write a one-page retrospective. Publish it. "Here's what I learned
   building an unpopular thing" content is actually valuable.
2. Keep Clawscript as your own utility. No shame in a tool you use.
3. Move on. Do not sink more than a working-week per month into it
   unless there's organic pull (unsolicited issues, PRs, or adopters).

The failure mode to avoid: a year of sporadic commits to a dead repo.
Either commit to it as a product with evening/weekend budget, or
declare it finished and archive.

---

## One-line summary of the whole playbook

Ship the demo video and the license first. Post Tuesday morning.
Stay at the keyboard for two hours. Respond to every comment.
Follow up with two blog posts in the first week. Measure stars and
clones. Three months is the cutoff for "is this going anywhere".
