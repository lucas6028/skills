---
name: solution-explorer
description: Generate multiple distinct approaches, solutions, or conceptual framings for a given problem, task, bug, design decision, or open-ended question — instead of committing to a single answer. Use this skill whenever the user presents a problem and would benefit from seeing the option space rather than one recommendation: phrases like "how should I approach X", "what are my options for", "ideas for solving", "different ways to", "I'm stuck on", "what are the tradeoffs", "should I do A or B", or any time the user is comparing strategies, weighing designs, brainstorming, or facing a decision where there is no single best answer. Trigger it even when the user asks for "a solution" (singular) if the problem is genuinely open-ended — surfacing alternatives is usually more useful than one opinion.
---

# Solution Explorer

Many problems have no single correct answer. The valuable thing a person often lacks is not *an* answer but a clear map of the **option space** — the genuinely different ways the problem could be approached, and what each one costs and buys. This skill produces that map.

The goal is breadth with honesty: distinct approaches that rest on different underlying ideas, presented neutrally with their real tradeoffs, so the user can choose based on what *they* value (which you usually can't fully know).

## When to use this skill

Use it for open-ended problems where multiple reasonable approaches exist:
- Engineering/design ("how should I architect the caching layer?", "ways to fix this race condition")
- Decisions and strategy ("should we build or buy?", "how do I structure the team?")
- Debugging with several plausible root causes
- Process, planning, writing structure, research direction, life/career framing
- Any "I'm stuck" or "what are my options" prompt

Do **not** force multiple options when the problem genuinely has one correct answer (a factual question, a syntax error with one fix, a settled best practice). In those cases just answer directly and say so. Manufacturing fake alternatives is worse than giving the one right answer.

## Core principles

1. **Distinct, not cosmetic.** Each approach should rest on a different core idea or strategy — not the same solution with minor wording changes. If two options collapse into "basically the same thing," merge them. Aim for approaches that a thoughtful expert would actually recognize as separate schools of thought.

2. **No false "best."** Lead with the explicit framing that there may be no single best answer. Don't rank unless the user asks. If one approach is dominant for most cases, you can note that, but still show the others and the conditions under which they win.

3. **Honest tradeoffs.** Every approach has costs. State them. A pros-only list is a sales pitch, not a map. The most useful sentence is often "this is better when ___ and worse when ___."

4. **Surface the hidden axis.** Different approaches usually differ along some underlying dimension (speed vs. flexibility, simplicity vs. power, cost now vs. cost later, control vs. convenience). Naming that axis helps the user see the *shape* of the decision, not just the list.

5. **Right number of options.** Default to 3–4 substantively different approaches. Two is fine if the space is genuinely binary; five-plus only if the domain is rich and the extras are real. Padding the list with weak filler options dilutes the strong ones.

## Output structure

Use this structure. Keep it scannable. Use prose under each approach, not deeply nested bullets.

```
**The decision underneath:** [1-2 sentences naming what's really being traded off, and an explicit note if there's no universally best answer.]

### Approach 1 — [short evocative name for the core idea]
[2-4 sentences: what it is and the concept it rests on.]
- Best when: [conditions where this wins]
- Costs: [what you give up / what's hard about it]

### Approach 2 — [name]
[...]

### Approach 3 — [name]
[...]

**Choosing:** [A short closing paragraph — NOT a verdict. Map the options to what the user might value: "If you care most about X, lean toward 1; if Y matters more, 3 fits better." Then, if helpful, ONE clarifying question whose answer would actually change the recommendation.]
```

Adapt headings to the medium — for a quick chat answer, a lighter inline version is fine, but always keep: the decision-underneath framing, named distinct approaches, per-approach tradeoffs, and a non-prescriptive close.

## Generating genuinely different approaches

If you find yourself listing variations of one idea, deliberately walk these lenses to find real alternatives. Not all apply to every problem — use them as a divergence prompt:

- **Build vs. buy vs. avoid** — make it, adopt something existing, or sidestep needing it at all.
- **Where the complexity lives** — push it to the user, the system, the data, the process, or upstream/downstream.
- **Time horizon** — the cheap-now solution vs. the invest-now-save-later solution.
- **Reversibility** — easy-to-undo experiments vs. committed one-way-door choices.
- **Scale of change** — minimal patch, targeted refactor, or fundamental redesign.
- **Who/what bears the constraint** — optimize for the machine, the team, the budget, or the timeline.
- **Invert the problem** — instead of solving X, eliminate the conditions that make X a problem.
- **Borrow from another domain** — how does a different field solve the structurally-similar problem?

## Examples

**Example — "How should I handle config in my app?"**

> **The decision underneath:** you're trading flexibility against simplicity, and how much you trust the runtime environment. There's no universal winner — it depends on team size and deploy targets.
>
> **Approach 1 — Plain files (concept: config as code).** Commit a config file; the app reads it at startup. *Best when:* small team, few environments, you want config versioned alongside code. *Costs:* secrets leak into the repo unless handled separately; changing config means a deploy.
>
> **Approach 2 — Environment variables (concept: config from the outside).** The environment supplies values; the app stays config-agnostic. *Best when:* containerized/cloud deploys, you need secrets out of the codebase. *Costs:* poor for structured/nested config; easy to misconfigure silently.
>
> **Approach 3 — Dedicated config service (concept: config as a live, central resource).** A service (or vault) serves config at runtime. *Best when:* many services, frequent changes without redeploys, strict secret handling. *Costs:* real operational overhead; new dependency and failure mode.
>
> **Choosing:** if you're one app on one platform, Approach 1 or 2 is almost certainly enough; the service only pays off at scale. One question that would settle it: how often does config need to change *without* shipping new code?

**Example — single right answer (don't force options).**

> User: "My Python code throws `IndentationError` on this line."
> This isn't an option-space problem — there's one fix (correct the indentation). State the fix directly; don't invent alternative "approaches."

## Reminders

- Lead by acknowledging there may be no single best answer when that's true.
- Make approaches *conceptually* distinct, not reworded twins.
- Always include costs, not just benefits.
- End by mapping options to values, not by issuing a verdict — unless the user explicitly asks you to pick.
