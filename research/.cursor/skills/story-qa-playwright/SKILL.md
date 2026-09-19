---
name: story-qa-playwright
description: "Use for story-to-test conversion, manual-case coverage, Playwright validation, and GitHub PR creation when a change needs end-to-end QA without merging. Trigger when the task is to derive cases from a story, map a manual checklist to a spec, run focused validation, find GitHub check status, or open a review-ready PR after local tests pass."
disable-model-invocation: true
---

# Story QA Playwright

Turn manual test cases or a story into Playwright coverage and a review-ready GitHub pull request. Do not merge. Finish only when local validation and GitHub checks are complete, then leave the PR waiting for reviewer approval.

## Preconditions

Before implementation, verify:

- The project root contains `package.json` and `playwright.config.*`.
- The required Playwright dependency and browsers are available.
- The repository has a Git remote and the GitHub CLI is authenticated (`gh auth status`).
- The working tree is clean before the workflow starts. Existing user changes must be committed or stashed by the user; never discard them.
- The manual case has steps and an expected result, or the story has enough acceptance criteria to derive cases.

Use the portable runner from the project root:

```bash
node <skill-path>/scripts/run-story-qa.mjs <case-id> --dry-run
```

The dry run checks the project, manual case, and spec paths without changing Git state or requiring GitHub authentication.

## Decision Framework

Before choosing a case set or changing product code, reason in this order:

1. Start from the actual evidence: manual steps, acceptance criteria, and the existing UI contract. Do not infer requirements that are not present.
2. Derive the minimum meaningful scenarios. For a story, prefer the happy path plus the smallest set of alternate/validation/boundary cases that can fail for the real business reason. A case is justified only if it tests a distinct user decision, state transition, validation rule, or regression risk.
3. Preserve explicit user-provided case lists. If the user already enumerated cases, do not broaden the scope by inventing additional scenarios unless a missing failure mode is clearly required to validate the same stated behavior.
4. Decide whether product code changes are truly necessary. Only change product code when the application is blocking an honest test because of a real defect, missing accessibility hook, or state that the app should expose but does not. If the test can be written against the intended behavior without changing production code, do not change it.
5. If a requirement is ambiguous, state the assumption and keep the test anchored to observable behavior rather than implementation details.

## Inputs And Mapping

- If manual cases are supplied, preserve their IDs and titles. Implement one Playwright test per case or clearly separable scenario.
- If only a story is supplied, derive cases for the happy path, alternate path, validation, empty/boundary state, persistence, permissions, destructive confirmation, regression, and keyboard/focus behavior when relevant.
- Do not invent extra cases when the user supplied an explicit case list.
- Inspect the existing Playwright config, test directory, fixtures, and page objects before adding files. Follow local conventions.
- If no convention exists, use `tests/e2e/` for specs and `tests/pages/` for page objects.

## Implementation Rules

- Keep test specs focused on the manual-case flow and expected assertions. Keep locators and reusable interactions in page objects.
- Isolate data and keep tests independent; do not rely on test order or leftover UI state.
- Never add `waitForTimeout`; it hides the real condition you should be waiting for and makes the test flaky. Wait on locators, assertions, or project-defined network signals instead.
- Add the exact manual step comment and exact expected-result comment on separate lines directly above the assertion they describe.
- Change product code only when needed to make an honest test possible, and call out that change in the PR.
- Ask only when a required step cannot be automated, such as a CAPTCHA, physical device action, or inaccessible email.
- Use the project’s existing conventions for locators and assertions. Prefer semantic queries and existing test IDs when they already exist; do not add redundant, generic guidance that the model already knows.

## Failure Recovery And Escalation

Treat the workflow as a sequence of checkpoints. If a step fails, stop and recover before moving on.

### Local failure (before push)

- Read the failing assertion and fix the root cause in the test or product behavior; do not weaken the assertion to force a pass.
- If the failure is caused by a genuine product bug, report it explicitly and ask how the team wants to proceed before continuing.
- Re-run the focused test, then the full suite, before moving on to the PR workflow.

### Branch or remote conflicts

- If `git pull --no-edit origin develop` or the equivalent base-branch sync reports conflicts, stop immediately and resolve the conflict without discarding user work.
- If the branch already exists, either switch to it if it is the correct branch for this work or create a new branch name only after confirming the current branch is not accidentally reused.
- If the repo has unrelated uncommitted changes, do not overwrite them; stash, commit, or ask the user to preserve them before proceeding.

### Post-push or CI failure

- If `gh pr checks --watch` shows a failing, timed-out, cancelled, or still-pending check, do not claim success. Investigate the failing job and fix the cause before leaving the PR open.
- If the pipeline fails after a clean local run, re-check the exact job log, compare the branch against the base, and look for environment-specific drift, missing fixtures, or config differences.
- If the PR is blocked by a red check but the issue is unrelated to the QA work, document that clearly and do not mark the task complete.

### Required stop conditions

- Stop and ask for manual input when a test requires a CAPTCHA, physical device interaction, inaccessible email, or other non-automatable prerequisite.
- Stop if the user has not explicitly approved a product-code change or if a branch conflict risks destroying unrelated work.
- Do not merge. Leave the PR open for reviewer approval after all checks are green.

## Required Workflow

Track every step and stop on the first failure:

```text
Story QA:
- [ ] Parse input and map existing coverage
- [ ] Lock the case list
- [ ] Implement Playwright tests and page objects
- [ ] Run the focused test locally
- [ ] Run the full local Playwright suite
- [ ] Create branch, commit, push, and open PR
- [ ] Wait for every GitHub check to complete successfully
- [ ] Stop with the PR open for reviewer approval
```

Run the focused test first, then the full suite:

```bash
node <skill-path>/scripts/run-local-playwright.mjs <spec-or-test-filter>
node <skill-path>/scripts/run-local-playwright.mjs
```

Run the repository gates directly when diagnosing lifecycle readiness:

```bash
npm run qa:preflight   # project, dependency, config, and Playwright checks
npm run qa:full        # preflight plus the complete existing automated suite
npm run qa:coverage    # every manual case must have a matching spec
```

`qa:coverage` is intentionally allowed to fail while manual cases are not automated. It is the completion gate for claiming full manual-case coverage; do not replace it with the ordinary suite result.

Fix test failures before committing. Do not hide an application bug by weakening an assertion. If the user did not request a failing test, report the bug and ask how it should be handled.

Run the complete PR workflow only after local tests pass:

```bash
node <skill-path>/scripts/run-story-qa.mjs <case-id>
```

The runner discovers the remote default branch, uses `test/<case-slug>` by default, validates required files, checks a clean tree, runs Playwright, commits QA files, pushes, opens the PR, and watches checks. Override values when the project differs:

```bash
node <skill-path>/scripts/run-story-qa.mjs <case-id> \
  --case-dir qa/manual \
  --spec-dir test/e2e \
  --base main \
  --config qa.config.json
```

## Optional Project Configuration

Place `qa.config.json` at the project root when CLI overrides are not enough:

```json
{
  "manualCaseDir": "manual-test-cases",
  "specDir": "tests/e2e",
  "baseBranch": "main",
  "branchPrefix": "test"
}
```

CLI options take precedence over this file. The case and spec can also be set explicitly with `--case` and `--spec`.

## Pull Request Contract

- Title: `test: cover <case-or-story> with Playwright`
- Include the source, exact local commands and results, case IDs, and any product-code changes.
- Keep the PR open. Never merge or request reviewers unless explicitly asked.
- A successful workflow requires every check to be completed with `SUCCESS`, `SKIPPED`, or `NEUTRAL`; pending, cancelled, timed out, or failed checks are not success.

## Transfer To Another Project

Copy this skill directory into the other project’s `.cursor/skills/` directory. Then:

1. Confirm its Playwright config, manual-case path, spec path, and page-object conventions.
2. Add `qa.config.json` only for paths or branch rules that differ from the defaults.
3. Run the dry run with a real case ID.
4. Run the focused test and full suite.
5. Confirm the project’s GitHub Actions workflow reports the same test command before opening a PR.

The skill does not assume this repository’s case IDs, branch name, directory layout, operating system, or shell path.

## Scripts

- `scripts/preflight.mjs`: validates project prerequisites and, with `--all`, audits manual cases against matching specs.
- `scripts/run-local-playwright.mjs`: validates a Playwright config exists in the current project and forwards arguments to `npx playwright test`.
- `scripts/run-story-qa.mjs`: validates, tests, branches, commits, pushes, opens a PR, and watches checks.
- `scripts/wait-pr-pipeline.mjs`: independently watches a PR and fails unless all checks finish successfully.
