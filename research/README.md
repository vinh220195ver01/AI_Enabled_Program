# AI Enabled Program

Playwright coverage for the project's manual test cases.

## QA skill

The reusable workflow lives in `.cursor/skills/story-qa-playwright/`. Validate a case without changing Git state:

```bash
npm run qa:tc -- TC02 --dry-run
```

Lifecycle gates:

```bash
npm run qa:preflight  # prerequisites and installed Playwright
npm run qa:full       # preflight plus all existing automated tests
npm run qa:coverage   # verify every manual case has an automated spec
```

The current reset state has no automated TC specs. The full suite uses Playwright's pass-with-no-tests mode so the lifecycle remains runnable; `qa:coverage` still fails until every manual case has a matching spec.

Run a focused or complete local suite with the skill's `run-local-playwright.mjs` script. After local tests pass, the full runner can create the branch, pull request, and wait for GitHub checks:

```bash
node .cursor/skills/story-qa-playwright/scripts/run-story-qa.mjs TC02
```

Copy the skill directory into another project's `.cursor/skills/` directory. Use `qa.config.json` or CLI options when that project uses different manual-case, spec, or branch paths.
