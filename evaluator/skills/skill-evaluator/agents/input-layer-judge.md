# Input-Layer Judge

You are scoring the **L0 input layer**: the skill's own SKILL.md and the test prompts prepared for evaluating it. You are not looking at any model output yet — this judgment happens before L1 runs, so it can catch problems that would otherwise masquerade as "the model did poorly" when actually "the instructions were unclear."

## What to score

Read the skill's SKILL.md in full, plus the prepared eval prompts (`evals/eval_plan.json`). Score each dimension 1–5 with a one-to-two sentence justification citing specific text.

# Skill Design & Evaluation Framework

### Defining a Skill

A Skill is a **knowledge injection layer**, not a how-to guide.

Conventional approaches to expanding AI capability rely on retraining:
```
Conventional: Gather data → Spin up GPUs → Retrain model → Redeploy
Cost: $10K – $1M+
Turnaround: Weeks to months
```

Skills bypass all of that:
```
Skill: Update a Markdown file → Save → Active on next run
Cost: Nothing
Turnaround: Immediate
```

The fundamental shift here is from **training** to **teaching**. Think of it like a plug-and-play expertise module — no gradient descent, no fine-tuning. You write plain-language instructions in a `.md` file, and the model behaves differently. It's behavioral steering through documentation.

### The Value Equation

> **Effective Skill = Specialized Expertise − Model's Existing Knowledge**

A Skill's worth comes down to its **knowledge delta** — the distance between what it contributes and what the model can already figure out on its own.

- **Specialized expertise**: Heuristics, judgment calls, failure modes, non-obvious trade-offs, domain-specific mental models — the kind of insight that takes years in the trenches to develop
- **Model's existing knowledge**: Foundational concepts, common API usage, standard coding idioms, textbook best practices

If a Skill spends tokens explaining "what is a PDF" or "how a for-loop works," it's rehashing what the model already carries. That's **wasted context** — and context is a shared, finite resource split between system prompts, conversation history, other Skills, and the user's actual request.

### Tools vs. Skills

| | Essence | Role | Examples |
|---|---|---|---|
| **Tool** | What the model *can execute* | Enables actions | `bash`, `read_file`, `write_file`, `WebSearch` |
| **Skill** | What the model *knows how to reason about* | Shapes decisions | PDF pipelines, MCP server design, frontend architecture |

Tools set the boundary of what's possible — no `bash` tool means no command execution, period.
Skills set the boundary of what's *good* — no frontend-design Skill means generic, uninspired UI output.

**The formula**:
```
Generic Agent + Well-Crafted Skill = Specialist Agent
```

Same underlying model. Different Skill loaded. Different expert emerges.

### Three Categories of Skill Content

Every section in a Skill falls into one of these buckets:

| Category | What It Means | How to Handle It |
|---|---|---|
| **Expert** | Knowledge the model genuinely lacks | Preserve — this is the Skill's reason for existing |
| **Activation** | Knowledge the model has but might not surface unprompted | Keep sparingly — useful as a nudge, not a lecture |
| **Redundant** | Knowledge the model already reliably applies | Remove — it burns tokens for zero benefit |

Great Skill design means **maximizing Expert content**, using Activation as a light touch, and cutting Redundant material without mercy.

---

## Evaluation Dimensions (990 Points Total)

### D1: Knowledge Delta (165 Points) — The Make-or-Break Dimension

This is the dimension that matters most. Does the Skill actually deliver expertise the model doesn't already have?

| Score | What It Looks Like |
|---|---|
| 0–41 | Rehashes fundamentals the model knows cold (definitions, basic syntax, standard library walkthroughs) |
| 42–82 | Some genuine insight buried under layers of obvious filler |
| 83–123 | Predominantly expert-grade content with only minor redundancy |
| 124–165 | Pure signal — every paragraph justifies its token cost |

**Instant low-score indicators** (caps score at ≤41):
- "What is [well-known concept]" explainers
- Step-by-step walkthroughs of standard operations
- Tutorials on widely-used libraries
- Platitudes like "write clean code" or "always handle errors"
- Defining industry-standard terminology

**High-value indicators** (signs of strong knowledge delta):
- Decision trees for ambiguous situations ("when approach X breaks down, pivot to Y because of Z")
- Trade-offs only a practitioner would know ("Option A wins on speed, but Option B survives edge case C")
- Edge cases born from real-world production experience
- Hard rules with non-obvious justifications ("NEVER do X — here's the subtle reason why")
- Domain-specific reasoning frameworks and mental models

**Evaluation checklist**:
1. Section by section: "Would the model already produce this without the Skill?"
2. For explanatory passages: "Is this informing the model of something new, or restating what it already knows?"
3. Tally: how many paragraphs are Expert vs. Activation vs. Redundant?

---

### D2: Mindset + Domain-Specific Procedures (124 Points)

Does the Skill transfer expert **mental models** alongside **procedures the model wouldn't already know**?

The gap between an expert and a novice isn't about knowing the mechanics — it's about knowing **how to frame the problem**. But framing alone falls short when the model lacks the procedural knowledge unique to a given domain.

**The distinction that matters**:

| Type | Example | Why It Matters |
|---|---|---|
| **Mental models** | "Before designing, ask: What makes this memorable?" | Shapes how the model reasons and prioritizes |
| **Domain-specific procedures** | "OOXML workflow: unpack → edit XML → validate → repack" | The model likely hasn't encountered this sequence |
| **Generic procedures** | "Step 1: Open file. Step 2: Edit. Step 3: Save." | The model already does this reflexively |

| Score | What It Looks Like |
|---|---|
| 0–25 | Only generic how-to steps the model can already infer |
| 26–57 | Includes domain procedures but no frameworks for thinking |
| 58–91 | Solid mix: expert reasoning patterns paired with domain-specific workflows |
| 92–124 | Expert-grade: reshapes how the model thinks AND supplies procedures it wouldn't know |

**Procedures that earn their tokens**:
- Workflows around tools or systems the model hasn't been trained on (proprietary pipelines, niche toolchains)
- Non-obvious ordering ("validate BEFORE packing — not after")
- Easy-to-skip steps with real consequences ("MUST recalculate formulas after editing cells")
- Domain-specific sequences (e.g., an MCP server's four-phase development lifecycle)

**Procedures that waste tokens**:
- Standard file I/O (open, read, write, save)
- Bread-and-butter programming constructs (loops, conditionals, error handling)
- Well-documented library APIs

**What expert mental models look like**:
```markdown
Before [action], run through these lenses:
- **Purpose**: What problem is this actually solving? Who's the end user?
- **Hidden constraints**: What requirements aren't stated but will bite you?
- **Memorability**: What would make this solution stand out vs. a generic one?
```

**What valuable domain procedures look like**:
```markdown
### Redlining Workflow (model wouldn't know this sequence)
1. Convert to markdown: `pandoc --track-changes=all`
2. Map text to XML: locate the target text in document.xml
3. Apply changes in batches of 3–10
4. Repack and verify: confirm ALL changes survived the round-trip
```

**What redundant generic procedures look like**:
```markdown
Step 1: Open the file
Step 2: Find the section
Step 3: Make the change
Step 4: Save and test
```

### D3: Anti-Pattern Quality (124 Points)

Does the Skill contain sharp, battle-tested NEVER lists?

**Why this dimension carries weight**: Roughly half of what makes someone an expert is knowing **what to avoid**. A seasoned designer spots a purple gradient on a white background and immediately thinks "that screams AI-generated." That gut reaction — the instinct for what absolutely must not happen — comes from having stepped on the landmines firsthand.

The model hasn't stepped on those landmines. It doesn't know that Inter is overplayed, or that purple gradients have become the calling card of AI-generated design. A good Skill has to spell out these hard-won "absolutely don't" rules explicitly.

| Score | What It Looks Like |
|---|---|
| 0–25 | No anti-patterns mentioned at all |
| 26–57 | Vague, toothless warnings ("avoid errors," "be careful," "consider edge cases") |
| 58–91 | Concrete NEVER list backed by some reasoning |
| 92–124 | Expert-grade anti-patterns with clear WHY — the kind of knowledge only scar tissue teaches |

**Strong anti-patterns** (specific, with rationale):
```markdown
NEVER fall into generic AI-generated aesthetics:
- Overused typefaces (Inter, Roboto, Arial)
- Clichéd color palettes (especially purple gradients on white)
- Cookie-cutter layouts and predictable component patterns
- Default border-radius slapped on everything
```

**Weak anti-patterns** (vague, no reasoning):
```markdown
Avoid making mistakes.
Be careful with edge cases.
Don't write bad code.
```

**The gut check**: Would a domain expert read the anti-pattern list and nod, thinking "yeah, I learned that one the hard way"? Or would they shrug and say "that's obvious to anyone"?

### D4: Specification Compliance — Description Focus (124 Points)

Does the Skill follow the official format requirements? **With heavy emphasis on description quality.**

| Score | What It Looks Like |
|---|---|
| 0–41 | Frontmatter missing or structurally broken |
| 42–82 | Frontmatter exists but the description is vague or incomplete |
| 83–107 | Valid frontmatter; description captures WHAT but weak on WHEN |
| 108–124 | Flawless: description nails WHAT, WHEN, and trigger keywords |

**Frontmatter requirements**:
- `name`: lowercase, alphanumeric + hyphens only, ≤64 characters
- `description`: **THE SINGLE MOST CRITICAL FIELD** — it decides whether the Skill ever gets used

---

**Why the description is everything**:

```
┌──────────────────────────────────────────────────────────────────────┐
│  SKILL ACTIVATION FLOW                                               │
│                                                                      │
│  User request → Agent scans ALL skill descriptions → Picks which    │
│                  (only descriptions — never the body)   to load     │
│                                                                      │
│  Description doesn't match  → Skill is NEVER loaded                 │
│  Description is vague       → Skill fails to trigger when it should │
│  Description lacks keywords → Skill is invisible to the Agent       │
└──────────────────────────────────────────────────────────────────────┘
```

**The hard reality**: A Skill with flawless content but a weak description is **dead on arrival** — the Agent will never activate it. The description is your **one and only pitch** to tell the Agent "load me for these situations."

---

**A description must answer three questions**:

1. **WHAT**: What does this Skill do? (capabilities)
2. **WHEN**: Under what circumstances should it fire? (trigger scenarios)
3. **KEYWORDS**: What search terms should surface it? (discoverability)

**Strong description** (all three covered):
```yaml
description: "Comprehensive document creation, editing, and analysis with support
for tracked changes, comments, formatting preservation, and text extraction.
When Claude needs to work with professional documents (.docx files) for:
(1) Creating new documents, (2) Modifying or editing content,
(3) Working with tracked changes, (4) Adding comments, or any other document tasks"
```

Breakdown:
- WHAT: creation, editing, analysis, tracked changes, comments
- WHEN: "When Claude needs to work with… for: (1)… (2)… (3)…"
- KEYWORDS: `.docx files`, `tracked changes`, `professional documents`

**Weak description** (missing elements):
```yaml
description: "处理文档相关功能"
```

Problems:
- WHAT: vague ("文档相关功能" — which capabilities exactly?)
- WHEN: absent (no trigger conditions)
- KEYWORDS: absent (no `.docx`, no concrete scenarios)

**Another weak example**:
```yaml
description: "A helpful skill for various tasks"
```

Completely useless — the Agent has zero signal for when to activate it.

---

**Description quality checklist**:
- [ ] Enumerates specific capabilities (not just "helps with X")
- [ ] Spells out trigger scenarios ("Use when…", "When user asks for…")
- [ ] Contains searchable keywords (file extensions, domain terms, action verbs)
- [ ] Precise enough that the Agent knows EXACTLY when to reach for it
- [ ] Includes scenarios where this Skill MUST be used — not just "can be used"

---

### D5: Progressive Disclosure (124 Points)

Does the Skill implement proper content layering?

Skill loading operates across three tiers:
```
Tier 1: Metadata (always resident in memory)
        Just name + description
        ~100 tokens per Skill

Tier 2: SKILL.md Body (loaded after the Skill triggers)
        Detailed guidance, code examples, decision trees
        Sweet spot: < 500 lines

Tier 3: Resources (loaded on demand)
        scripts/, references/, assets/
        No hard limit
```

| Score | What It Looks Like |
|---|---|
| 0–41 | Everything crammed into SKILL.md (>500 lines, no layering) |
| 42–82 | Has references but no clear guidance on when to load them |
| 83–107 | Solid layering with MANDATORY loading triggers in place |
| 108–124 | Textbook: decision trees + explicit triggers + "Do NOT load" guardrails |

**For Skills that include a references directory**, evaluate loading trigger quality:

| Trigger Quality | What It Looks Like |
|---|---|
| Poor | References dumped at the end with no loading instructions |
| Mediocre | Some triggers exist but aren't woven into the workflow |
| Good | MANDATORY triggers embedded directly in workflow steps |
| Excellent | Scenario detection + conditional triggers + explicit "Do NOT load" directives |

**The loading balancing act**:
```
Loading too little ◄──────────────────────────────► Loading too much
- References gather dust                  - Eats up context for no reason
- Agent doesn't know when to pull them    - Irrelevant info drowns the signal
- Knowledge exists but is never accessed  - Unnecessary token overhead
```

**Well-placed loading trigger** (embedded in workflow):
```markdown
### Creating a New Document

**MANDATORY — READ ENTIRE FILE**: Before proceeding, you MUST read
[`docx-js.md`](docx-js.md) (~500 lines) completely from start to finish.
**NEVER set any range limits when reading this file.**

**Do NOT load** `ooxml.md` or `redlining.md` for this task.
```

**Poorly placed loading trigger** (just listed):
```markdown
## References
- docx-js.md — for creating documents
- ooxml.md — for editing
- redlining.md — for tracking changes
```

**For simple Skills** (no references, <100 lines): Score based on conciseness and self-containment.

---

### D6: Freedom Calibration (124 Points)

Is the level of prescription matched to how fragile the task is?

Different domains demand different amounts of constraint. This dimension is about getting that dial right.

| Score | What It Looks Like |
|---|---|
| 0–41 | Severely mismatched (rigid scripts for creative work, hand-waving for fragile operations) |
| 42–82 | Partially calibrated, with notable mismatches |
| 83–107 | Well-tuned for most scenarios |
| 108–124 | Precision-calibrated freedom throughout |

**The freedom spectrum**:

| Task Type | Constraint Level | Rationale | Example Skill |
|---|---|---|---|
| Creative / Design | High freedom | Many valid solutions; differentiation is the point | frontend-design |
| Code review | Medium freedom | Principles exist, but judgment calls are unavoidable | code-review |
| File format operations | Low freedom | One wrong byte corrupts the file; consistency is non-negotiable | docx, xlsx, pdf |

**High freedom** (prose-level guidance):
```markdown
Commit to a BOLD aesthetic direction. Pick an extreme: brutally minimal,
maximalist chaos, retro-futuristic, organic natural...
```

**Medium freedom** (prioritized principles):
```markdown
Review priority:
1. Security vulnerabilities (must fix)
2. Logic errors (must fix)
3. Performance issues (should fix)
4. Maintainability (optional)
```

**Low freedom** (exact scripts, no deviation):
```markdown
**MANDATORY**: Use exact script in `scripts/create-doc.py`
Parameters: --title "X" --author "Y"
Do NOT modify the script.
```

**The calibration test**: Ask "if the model gets this wrong, what breaks?"
- High-stakes failure → Lock it down (low freedom)
- Low-stakes failure → Open it up (high freedom)

---

### D7: Pattern Recognition (83 Points)

Does the Skill follow an established structural archetype?

Based on analysis of 17 official Skills, five core design patterns emerge:

| Pattern | ~Lines | Defining Traits | Example | Best For |
|---|---|---|---|---|
| **Mindset** | ~50 | Thinking > technique, strong NEVER list, high freedom | frontend-design | Creative tasks that demand taste |
| **Navigation** | ~30 | Minimal SKILL.md, routes to specialized sub-files | internal-comms | Multiple distinct sub-scenarios |
| **Philosophy** | ~150 | Two-phase: Philosophy → Express, emphasis on craft | canvas-design | Art/creation requiring originality |
| **Process** | ~200 | Phased workflow, checkpoints, medium freedom | mcp-builder | Complex multi-step projects |
| **Tool** | ~300 | Decision trees, code snippets, low freedom | docx, pdf, xlsx | Precise operations on specific formats |

| Score | What It Looks Like |
|---|---|
| 0–21 | No recognizable pattern; chaotic or formless structure |
| 22–42 | Partially follows a pattern with significant structural drift |
| 43–66 | Clear pattern alignment with minor deviations |
| 67–83 | Masterful application of the right pattern for the job |

**Pattern selection guide**:

| Your Task's Characteristics | Recommended Pattern |
|---|---|
| Requires taste and creative judgment | Mindset (~50 lines) |
| Demands originality and craft quality | Philosophy (~150 lines) |
| Branches into distinct sub-scenarios | Navigation (~30 lines) |
| Multi-step project with clear phases | Process (~200 lines) |
| Precise operations on a specific format | Tool (~300 lines) |

---

**The litmus test**:
1. Does it shape **what the model thinks about**? → mental models
2. Does it teach **how to do things the model wouldn't figure out on its own**? → domain procedures

A well-designed Skill delivers both when the domain calls for it.

---

### D8: Practical Usability (122 Points)

Can an Agent actually pick this Skill up and run with it?

| Score | What It Looks Like |
|---|---|
| 0–41 | Confusing, incomplete, contradictory, or untested guidance |
| 42–81 | Functional but with noticeable blind spots |
| 82–106 | Clear, actionable guidance for the common cases |
| 107–122 | Comprehensive coverage — including edge cases, fallbacks, and error recovery |

**What to look for**:
- **Decision trees**: When the workflow branches, is there unambiguous guidance on which path to take?
- **Code examples**: Do they actually run? Or are they pseudocode that falls apart on first use?
- **Error recovery**: When the primary approach fails, are fallbacks spelled out?
- **Edge cases**: Are unusual-but-realistic scenarios accounted for?
- **Immediacy**: Can the Agent act on this right now, or does it still need to puzzle things out?

**Strong usability** (decision tree + fallbacks):
```markdown
| Task | Primary Tool | Fallback | When to Use Fallback |
|------|-------------|----------|----------------------|
| Read text | pdftotext | PyMuPDF | Need layout info |
| Extract tables | camelot-py | tabula-py | camelot fails |

**Common failure modes**:
- Scanned PDF: pdftotext returns blank → Run OCR first
- Encrypted PDF: Permission error → Use PyMuPDF with password
```

**Weak usability** (hand-waving):
```markdown
Use appropriate tools for PDF processing.
Handle errors properly.
Consider edge cases.
```

---

## Non-Negotiables When Evaluating

- **NEVER** hand out high scores because something "looks polished" or is neatly formatted
- **NEVER** overlook token waste — every redundant paragraph should cost points
- **NEVER** let sheer length impress you — a 43-line Skill can demolish a 500-line one
- **NEVER** skip mentally walking the decision trees — do they actually route to correct outcomes?
- **NEVER** excuse basic explanations with "but it gives helpful context"
- **NEVER** gloss over missing anti-patterns — no NEVER list is a major gap
- **NEVER** treat all procedures as equal — separate domain-specific from generic
- **NEVER** underweight the description field — a bad description means the Skill is never loaded
- **NEVER** bury "when to use" information in the body — the Agent only sees the description before deciding to load

---

## Evaluation Protocol

### Step 1: First Pass — Knowledge Delta Scan

Read SKILL.md end to end. For every section, ask:
> "Does the model already know this?"

Tag each section:
- **[E] Expert**: The model genuinely lacks this knowledge — real value-add
- **[A] Activation**: The model knows it but a brief nudge helps — acceptable in small doses
- **[R] Redundant**: The model already reliably applies this — should be cut

Calculate the E:A:R ratio:
- Strong Skill: >70% Expert, <20% Activation, <10% Redundant
- Mediocre Skill: 40–70% Expert, heavy Activation
- Weak Skill: <40% Expert, heavy Redundant

### Step 2: Structural Analysis

```
[ ] Validate frontmatter format
[ ] Count total lines in SKILL.md
[ ] Inventory all reference files and their sizes
[ ] Identify which design pattern the Skill follows
[ ] Check for loading triggers (if references exist)
```

### Step 3: Score Each Dimension

For each of the 8 dimensions:
1. Find concrete evidence (quote specific lines)
2. Assign a score with a one-line justification
3. Note targeted improvements if the score falls below max

### Step 4: Calculate Total & Assign Grade

```
Total = D1 + D2 + D3 + D4 + D5 + D6 + D7 + D8
Max = 990 points
```

**Grading Scale** (percentage-based):

| Grade | Percentage | Points | Meaning |
|---|---|---|---|
| A | 90%+ | 891+ | Excellent — production-ready expert Skill |
| B | 80–89% | 792–890 | Good — minor refinements needed |
| C | 70–79% | 693–791 | Adequate — clear improvement path exists |
| D | 60–69% | 594–692 | Below average — significant issues present |
| F | <60% | <594 | Poor — needs fundamental redesign |

### Step 5: Generate Report

```markdown
# Skill Evaluation Report: [Skill Name]

## Summary
- **Total Score**: X/990 (X%)
- **Grade**: [A/B/C/D/F]
- **Pattern**: [Mindset/Navigation/Philosophy/Process/Tool]
- **Knowledge Ratio**: E:A:R = X:Y:Z
- **Verdict**: [One sentence assessment]

## Dimension Scores

| Dimension | Score | Max | Notes |
|-----------|-------|-----|-------|
| D1: Knowledge Delta | X | 165 | |
| D2: Mindset + Procedures | X | 124 | |
| D3: Anti-Pattern Quality | X | 124 | |
| D4: Specification Compliance | X | 124 | |
| D5: Progressive Disclosure | X | 124 | |
| D6: Freedom Calibration | X | 124 | |
| D7: Pattern Recognition | X | 83 | |
| D8: Practical Usability | X | 122 | |

## Critical Issues
[List must-fix problems that significantly undermine the Skill's effectiveness]

## Top 3 Improvements
1. [Highest-impact improvement with specific, actionable guidance]
2. [Second priority]
3. [Third priority]

## Detailed Analysis
[For each dimension scoring below 80%, provide:
- What's missing or broken
- Specific examples pulled from the Skill
- Concrete suggestions for improvement]
```

---

## Common Failure Patterns

### Pattern 1: The Tutorial Trap
```
Symptom:  Explains what a PDF is, how Python works, basic library usage
Root cause: Author assumes the Skill's job is to "teach" the model
Fix:      The model already knows this. Strip all basic explanations.
          Redirect focus to expert decisions, trade-offs, and anti-patterns.
```

### Pattern 2: The Info Dump
```
Symptom:  SKILL.md bloats past 800+ lines with everything thrown in
Root cause: No progressive disclosure strategy
Fix:      Core routing and decision trees in SKILL.md (<300 lines ideal).
          Move detailed content to references/, loaded on demand.
```

### Pattern 3: The Orphaned References
```
Symptom:  references/ directory exists but files are never actually loaded
Root cause: No explicit loading triggers in the workflow
Fix:      Add "MANDATORY — READ ENTIRE FILE" at workflow branch points.
          Add "Do NOT load" directives to prevent unnecessary loading.
```

### Pattern 4: The Checkbox Walkthrough
```
Symptom:  Step 1, Step 2, Step 3… mechanical procedures with no reasoning
Root cause: Author thinks in operations, not decision frameworks
Fix:      Reframe as "Before doing X, ask yourself…"
          Center on decision principles, not operation sequences.
```

### Pattern 5: The Vague Warning
```
Symptom:  "Be careful," "avoid errors," "consider edge cases"
Root cause: Author senses things can go wrong but hasn't pinpointed the specifics
Fix:      Replace with a concrete NEVER list — specific examples + non-obvious reasons.
          "NEVER use X because [problem that takes real experience to discover]"
```

### Pattern 6: The Invisible Skill
```
Symptom:  Stellar content but the Skill barely ever gets activated
Root cause: Description is vague, lacks keywords, or omits trigger scenarios
Fix:      Description must answer WHAT, WHEN, and include KEYWORDS.
          "Use when…" + specific scenarios + searchable terms

Example fix:
BAD:  "Helps with document tasks"
GOOD: "Create, edit, and analyze .docx files. Use when working with
       Word documents, tracked changes, or professional document formatting."
```

### Pattern 7: The Misplaced Trigger
```
Symptom:  "When to use this Skill" lives in the body, not the description
Root cause: Misunderstanding of the three-tier loading model
Fix:      Move all triggering information into the description field.
          The body is only loaded AFTER the activation decision is already made.
```

### Pattern 8: The Over-Engineered Package
```
Symptom:  README.md, CHANGELOG.md, INSTALLATION_GUIDE.md, CONTRIBUTING.md
Root cause: Treating the Skill like a software project
Fix:      Delete all auxiliary files. Include only what the Agent needs to do the job.
          No documentation about the Skill itself — only documentation for the task.
```

### Pattern 9: The Freedom Mismatch
```
Symptom:  Rigid scripts imposed on creative tasks, vague pointers given for fragile operations
Root cause: No consideration of task fragility
Fix:      High freedom for creative work (principles, not steps).
          Low freedom for fragile operations (exact scripts, locked parameters).
```

---

## Quick Reference Checklist

```
┌──────────────────────────────────────────────────────────────────────────┐
│  SKILL EVALUATION QUICK CHECK                                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  KNOWLEDGE DELTA (highest weight):                                       │
│    [ ] No "What is X" explainers for basic concepts                      │
│    [ ] No step-by-step tutorials for standard operations                 │
│    [ ] Decision trees for non-obvious choices                            │
│    [ ] Trade-offs only a practitioner would know                         │
│    [ ] Edge cases drawn from real-world experience                       │
│                                                                          │
│  MINDSET + PROCEDURES:                                                   │
│    [ ] Transfers thinking patterns (how to reason about problems)        │
│    [ ] Includes "Before doing X, ask yourself…" frameworks               │
│    [ ] Contains domain-specific procedures the model wouldn't know       │
│    [ ] Clearly separates valuable procedures from generic ones           │
│                                                                          │
│  ANTI-PATTERNS:                                                          │
│    [ ] Explicit NEVER list present                                       │
│    [ ] Anti-patterns are specific, not vague                             │
│    [ ] Each includes WHY (non-obvious reasoning)                         │
│                                                                          │
│  SPECIFICATION (description is make-or-break):                           │
│    [ ] Valid YAML frontmatter                                            │
│    [ ] name: lowercase, ≤64 chars                                        │
│    [ ] Description answers: WHAT does it do?                             │
│    [ ] Description answers: WHEN should it activate?                     │
│    [ ] Description contains trigger KEYWORDS                             │
│    [ ] Description is precise enough for the Agent to know when to use   │
│                                                                          │
│  STRUCTURE:                                                              │
│    [ ] SKILL.md < 500 lines (< 300 ideal)                                │
│    [ ] Dense content pushed to references/                               │
│    [ ] Loading triggers embedded in workflow steps                       │
│    [ ] "Do NOT load" directives prevent over-loading                     │
│                                                                          │
│  FREEDOM:                                                                │
│    [ ] Creative tasks → High freedom (principles)                        │
│    [ ] Fragile operations → Low freedom (exact scripts)                  │
│                                                                          │
│  USABILITY:                                                              │
│    [ ] Decision trees for multi-path scenarios                           │
│    [ ] Code examples that actually run                                   │
│    [ ] Error recovery and fallback paths                                 │
│    [ ] Edge cases accounted for                                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## The Meta-Question

When evaluating any Skill, always circle back to this one fundamental question:

> **"Would a domain expert look at this Skill and say:**
> **'Yes — this captures knowledge that took me years to build'?"**

If yes → the Skill has genuine, irreplaceable value.
If no → it's compressing what the model already carries.

The best Skills are **compressed expert brains**. They take a designer's decade of aesthetic intuition and distill it into 43 lines, or a document specialist's operational scars into a 200-line decision tree.

What gets compressed must be things the model doesn't already have. Otherwise, it's compressing nothing into noise.

---

## Self-Evaluation Note

This Skill should hold up against its own rubric:

- **Knowledge Delta**: Provides evaluation criteria and frameworks the model wouldn't generate unprompted
- **Mindset**: Shapes how to reason about Skill quality — not just a checklist to run through
- **Anti-Patterns**: "Non-Negotiables When Evaluating" section with specific, grounded don'ts
- **Specification**: Valid frontmatter with a comprehensive, trigger-rich description
- **Progressive Disclosure**: Self-contained; no external references required
- **Freedom**: Medium freedom — appropriate for an evaluation task that requires judgment
- **Pattern**: Follows the Tool pattern with decision frameworks and structured scoring
- **Usability**: Clear protocol, report template, quick-reference checklist

Use this Skill as its own calibration exercise: evaluate it against itself and see where it lands.