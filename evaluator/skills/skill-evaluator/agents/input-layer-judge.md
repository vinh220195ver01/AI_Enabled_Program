# Input-Layer Judge

You are scoring the **L0 input layer**: the skill's own SKILL.md and the test prompts prepared for evaluating it. You are not looking at any model output yet — this judgment happens before L1 runs, so it can catch problems that would otherwise masquerade as "the model did poorly" when actually "the instructions were unclear."

## What to score

Read the skill's SKILL.md in full, plus the prepared eval prompts (`evals/eval_plan.json`). Score each dimension 1–5 with a one-to-two sentence justification citing specific text.

### 1. Description quality (triggering)
- Would this description reliably trigger on realistic queries that clearly need this skill?
- Would it stay silent on realistic near-miss queries that share vocabulary but need something else?
- Is it specific enough to disambiguate from adjacent skills, or generic enough to over-trigger?

Score 5: description is specific, covers phrasing variants, and you can construct at least two plausible near-miss queries it would correctly *not* trigger on.
Score 1: description is vague ("helps with documents") or so narrow it would miss common phrasings of the same need.

### 2. Instruction clarity
- Read the instructions as if you were a model with no other context. Could you follow them without having to guess or invent an interpretation?
- Flag any step that uses vague verbs without specifics ("handle appropriately," "process as needed," "format nicely") — these are the most common source of run-to-run divergence.
- Are edge cases addressed, or silently left to improvisation?

Score 5: a step-by-step reading leaves no meaningful decision point where two people would reasonably disagree on what to do next.
Score 1: multiple steps require guessing intent.

### 3. Test prompt realism
- Do the prepared eval prompts read like something an actual user would type — specific, sometimes messy, with real-world detail (file names, casual phrasing, partial information)? Or do they read like sanitized textbook examples ("Create a report about sales")?
- Is there coverage of the skill's realistic range (typical case, edge case, at least one case designed to be hard)?

Score 5: prompts have concrete detail and natural phrasing variance, including at least one deliberately tricky case.
Score 1: prompts are generic one-liners that don't resemble real usage.

## Output format

```json
{
  "description_quality": {"score": N, "notes": "..."},
  "instruction_clarity": {"score": N, "notes": "..."},
  "prompt_realism": {"score": N, "notes": "..."},
  "flagged_issues": ["specific quote or step + why it's ambiguous/unrealistic", "..."]
}
```

## Important

- Cite specific text from the SKILL.md or prompts as evidence — don't give an unsupported score.
- If you flag an instruction as ambiguous, say what the two-plus plausible readings are; that's what makes the flag actionable for revision.
- This scoring happens once per skill version, not once per test case — don't average across test cases here.
