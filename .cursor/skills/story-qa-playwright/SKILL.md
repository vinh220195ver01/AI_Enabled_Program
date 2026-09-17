---
name: story-qa-playwright
description: Script user-provided manual test cases into Playwright, run them locally, then open a GitHub pull request and wait until CI finishes. Use only when this skill is explicitly named or attached. Triggers include manual test cases, story QA, Playwright scripting, and a review-ready GitHub MR/PR.
disable-model-invocation: true
---

# Story QA Playwright

Turn **manual test cases** (or a story) into Playwright coverage and a **review-ready GitHub pull request**. Do not merge. Stop when CI is complete and the PR is waiting on a reviewer.

**Preferred input:** the user pastes manual test cases. Script those cases as written. Do not invent extra cases unless they ask.

## Deliverable

A GitHub PR that:

- Adds Playwright tests (and only the product code required for those tests to be valid)
- Passed **local** Playwright before push
- Has a finished GitHub Actions pipeline (all checks completed)
- Is left open for reviewer approval

## Workflow

Copy and track:

```
Story QA:
- [ ] 1. Parse input and map existing coverage
- [ ] 2. Lock the case list
- [ ] 3. Implement Playwright tests
- [ ] 4. Run locally until green
- [ ] 5. Branch, commit, push, open PR
- [ ] 6. Wait for GitHub checks to finish
- [ ] 7. Stop for reviewer approval
```

### 1. Parse input and map existing coverage

- If the user pasted cases, that list is the spec. Keep original IDs and titles.
- If they only gave a story/ticket, treat that as the spec and go to step 2 fallback.
- Inspect existing Playwright layout (`playwright.config.*`, `tests/`, `e2e/`, `fixtures/`, page objects).
- Follow the repo’s patterns. If none exist, put new tests under `tests/e2e/` and use `@playwright/test`.
- Do not duplicate tests that already cover the same case.

Accept messy manual-case text (spreadsheet paste, numbered list, Given/When/Then, steps/expected). Normalize internally; do not make the user reformat unless a case is missing both steps and expected result.

### 2. Lock the case list

**Manual cases provided:** one Playwright test per case (or per clearly separable scenario inside one case). Preserve IDs in `test('TC-12 …')` titles. Ask only when a step cannot be automated (captcha, physical device, email they cannot access).

**Story only:** design about 10 cases covering happy path, alternate path, validation, empty data, boundary, persistence, permission, destructive confirm, nearby regression, and keyboard/focus if UI. Name each so a reviewer can map it to an AC.

### 3. Implement Playwright tests

- Use `test` / `expect` from `@playwright/test`.
- Every new test case must follow the Page Object Model: reuse or extend the existing page objects, and create a page object under the repository's established page-object directory when no suitable object exists. Keep locators and page interactions in page objects; keep the test spec focused on the manual-case flow, exact step comments, and expected-result assertions.
- Prefer locators the app already uses (`getByRole`, `getByTestId`).
- Isolate data: unique names, test fixtures, or API setup the repo already has. Do not rely on leftover UI state.
- Keep tests independent; no order dependence.
- Do not add flake-prone `waitForTimeout`. Wait on locators or network the project already uses.
- Product-code changes only if a test cannot be honest without them (for example a missing test id). Call those out in the PR body.

### 4. Run locally until green

From the project root:

```bash
node .cursor/skills/story-qa-playwright/scripts/run-local-playwright.mjs
```

If you scoped tests, pass a file glob or `-g` pattern as extra args.

Fix failures before any commit. If a failure is an app bug, keep a failing test only when the user asked for that; otherwise report the bug, skip that case with a comment, and continue the rest.

### 5. Branch, commit, push, open PR

This skill **requires** a commit and PR (that is the deliverable).

- Branch: `test/<ticket-or-story-slug>` (fallback `test/story-qa`).
- Do not change git config, skip hooks, or force-push.
- Commit only QA-related files.
- Include every relevant file touched by the scenario, including the actual Playwright spec (for example `tests/e2e/tc02.spec.ts`), any related manual-case or support files, and any repo files needed to keep the QA workflow valid.
- Never leave a test implementation uncommitted or excluded from the PR just because it is "small" or "related".
- Add a source comment above the relevant assertions that preserves the exact manual-case step/verification wording, without paraphrasing or rewording it. The comment should match the original step and expected result language precisely.
- Put the step comment and the expected result comment in separate lines directly above the exact assertion code they describe. Do not combine them into a single line.
- Use `await` for every asynchronous action that requires waiting on a locator, click, page navigation, reload, or visibility assertion.
- Push and open the PR with `gh`. Target the repo default branch.

PR title: `test: cover <story> with Playwright`

PR body template:

```markdown
## Summary
- Story / source: <ticket or "manual test cases">
- Adds <N> Playwright cases (scripted from the input list; no extra cases).

## Local
- Command: <exact command>
- Result: passed

## Pipeline
- Waiting for GitHub checks to complete after open; will update if anything fails.

## Review
- Do not merge until a reviewer approves.
```

### 6. Wait for GitHub checks to finish

```bash
node .cursor/skills/story-qa-playwright/scripts/wait-pr-pipeline.mjs
```

Pass a PR number or URL if it is not the current branch’s PR.

If checks fail: pull logs with `gh`, fix, push (no force), and wait again. Repeat until all checks have **completed successfully**.

### 7. Stop for reviewer approval

When local tests and GitHub checks are green:

- Post the PR URL
- List the test cases
- State that the pipeline finished and the PR is waiting for reviewer approval
- Do **not** merge, do **not** request extra reviewers unless the user asked

## Standard Prompt Template

Use this wording when asking an agent to run the workflow in this repo:

```text
Implement TCxx using the repo QA workflow.
Use the repo-defined instructions in .cursor/skills/story-qa-playwright/SKILL.md and the fixed entry-point script.
Do not improvise outside the workflow. Run the repo validation, commit all related QA files, push the branch, create the PR against develop, and wait for the GitHub Actions checks to finish.
```

This is the standard prompt format expected for all TC implementations in this repo.

## Scripts

Execute these; do not only read them.

- `scripts/run-local-playwright.mjs` — run Playwright from the repo root (`npx playwright test`)
- `scripts/wait-pr-pipeline.mjs` — `gh pr checks --watch`, then fail unless every check succeeded
