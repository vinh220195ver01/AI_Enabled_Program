# AI Enabled Program

Playwright coverage for the project's manual test cases.

## QA skills

The workflow is split across 8 skills in `.cursor/skills/`, each owning one step so it can be reused or replaced independently:

| Skill | Responsibility |
|---|---|
| `excel-testcase-reader` | Parse manual test-case workbooks into structured test cases |
| `testcase-analyzer` | Judge a case ready/ambiguous/not-automatable before design starts |
| `auto-testcase-designer` | Convert a ready case (or a story) into an Auto Test Case design |
| `business-action-designer` | Decide reusable Business Action boundaries, names, and signatures |
| `automation-script-generator` | Implement the design as Playwright specs, actions, and page objects |
| `automation-debugger` | Triage and fix a failing or flaky run |
| `git-workflow` | Sync, branch, and commit the change |
| `github-pr` | Push, open the PR, and watch checks — never merges |

Lifecycle gates:

```bash
npm run qa:preflight  # prerequisites and installed Playwright
npm run qa:full       # preflight plus all existing automated tests
npm run qa:coverage   # verify every manual case has an automated spec
```

The current reset state has no automated TC specs. The full suite uses Playwright's pass-with-no-tests mode so the lifecycle remains runnable; `qa:coverage` still fails until every manual case has a matching spec.

Run a focused or complete local suite with `automation-script-generator`'s `run-local-playwright.mjs` script (also used by `automation-debugger` to reproduce/verify a fix):

```bash
node .cursor/skills/automation-script-generator/scripts/run-local-playwright.mjs tests/e2e/tc02.spec.ts
```

Once local tests pass, `git-workflow` branches and commits, then `github-pr` pushes, opens the PR, and watches checks:

```bash
npm run qa:branch -- --branch test/tc02-<slug> --message "test: cover TC02 with Playwright" --file tests/e2e/tc02.spec.ts
git push -u origin test/tc02-<slug>
npm run qa:pr -- --branch test/tc02-<slug> --base develop --title "test: cover TC02 with Playwright" --body-file pr-body.md
npm run qa:pr:watch
```

Copy the whole `.cursor/skills/` directory into another project's `.cursor/skills/` directory to reuse the same workflow there. `git-workflow` and `github-pr` are general-purpose and work for any coding task, not just QA.
