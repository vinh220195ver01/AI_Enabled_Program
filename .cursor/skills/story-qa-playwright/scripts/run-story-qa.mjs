import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const caseArg = args.find((arg) => /^TC\d+$/i.test(arg));

if (!caseArg) {
  console.error("Usage: node .cursor/skills/story-qa-playwright/scripts/run-story-qa.mjs TC02 [--dry-run]");
  process.exit(1);
}

const caseId = caseArg.toUpperCase();
const branchName = `test/${caseId.toLowerCase()}`;
const specFile = `tests/e2e/${caseId.toLowerCase()}.spec.ts`;
const manualCasePath = `manual-test-cases/${caseId}`;
const playCommand = process.platform === "win32"
  ? `& 'C:\\Program Files\\nodejs\\npx.cmd' playwright test ${specFile} --reporter=line`
  : `npx playwright test ${specFile} --reporter=line`;
const playwrightCommand = process.platform === "win32" ? "npx.cmd" : "npx";
const playwrightArgs = ["playwright", "test", specFile, "--reporter=line"];

const runCommand = (command, argsList, allowFailure = false) => {
  const result = spawnSync(command, argsList, {
    cwd: process.cwd(),
    shell: process.platform === "win32",
    stdio: ["inherit", "pipe", "pipe"],
    encoding: "utf-8",
  });

  if (result.status !== 0 && !allowFailure) {
    throw new Error(`${command} ${argsList.join(" ")} failed with exit code ${result.status ?? 1}`);
  }

  return result;
};

const ensureRepoReady = () => {
  const repoRoot = process.cwd();
  if (!existsSync(`${repoRoot}/package.json`) || !existsSync(`${repoRoot}/playwright.config.ts`)) {
    throw new Error("This script must run from the repository root.");
  }

  if (!existsSync(`${repoRoot}/${manualCasePath}`)) {
    throw new Error(`Manual case file not found: ${manualCasePath}`);
  }

  const gitRoot = runCommand("git", ["rev-parse", "--show-toplevel"], true).stdout?.trim();
  if (!gitRoot || gitRoot !== repoRoot.replace(/\\/g, "/")) {
    throw new Error("Git repository root does not match the current working directory.");
  }
};

const ensureNoUnexpectedRepoChanges = () => {
  const status = runCommand("git", ["status", "--porcelain", "--untracked-files=all"], true).stdout;
  const lines = (status ?? "").split(/\r?\n/).filter(Boolean);

  const allowedPrefixes = [
    `?? ${specFile}`,
    `?? ${manualCasePath}`,
    `?? .cursor/skills/story-qa-playwright/`,
    `?? .gitignore`,
    ` M .cursor/skills/story-qa-playwright/SKILL.md`,
    `M  .cursor/skills/story-qa-playwright/SKILL.md`,
    ` M package.json`,
    `M  package.json`,
    ` M .cursor/skills/story-qa-playwright/scripts/run-story-qa.mjs`,
    `?? .cursor/skills/story-qa-playwright/scripts/run-story-qa.mjs`,
    ` M ${specFile}`,
    `M  ${specFile}`,
    ` M ${manualCasePath}`,
    `M  ${manualCasePath}`,
    `?? .github/workflows/`,
    ` M .github/workflows/playwright.yml`,
    `M  .github/workflows/playwright.yml`,
  ];

  const unexpected = lines.filter((line) => !allowedPrefixes.some((prefix) => line.startsWith(prefix)));
  if (unexpected.length > 0) {
    throw new Error(
      `Unexpected repo changes detected. Only QA-related files may be in scope. Found: ${unexpected.join(", ")}`,
    );
  }
};

const ensureBranchNotExists = () => {
  const result = runCommand("git", ["show-ref", "--verify", `refs/heads/${branchName}`], true);
  if (result.status === 0) {
    throw new Error(`Branch already exists: ${branchName}`);
  }
};

const ensureGhAuth = () => {
  const result = runCommand("gh", ["auth", "status"], true);
  if (result.status !== 0) {
    throw new Error("GitHub CLI is not authenticated. Run 'gh auth login' before starting the QA workflow.");
  }
};

const runStep = (label, command, argsList) => {
  console.log(`\n==> ${label}`);
  if (dryRun) {
    console.log(`${command} ${argsList.join(" ")}`);
    return;
  }

  const result = spawnSync(command, argsList, {
    cwd: process.cwd(),
    shell: process.platform === "win32",
    stdio: "inherit",
  });

  if (result.status !== 0) {
    throw new Error(`${label} failed with exit code ${result.status ?? 1}`);
  }
};

try {
  ensureRepoReady();
  ensureNoUnexpectedRepoChanges();
  ensureBranchNotExists();
  ensureGhAuth();

  const workflow = [
    ["Ensure repo state", "git", ["switch", "develop"]],
    ["Pull develop", "git", ["pull", "--ff-only", "origin", "develop"]],
    ["Create QA branch", "git", ["switch", "-c", branchName]],
    ["Validate test file exists", "node", ["-e", `require('node:fs').existsSync(${JSON.stringify(specFile)}) || (() => { throw new Error(${JSON.stringify(`Missing test file: ${specFile}`)}) })()`]],
    ["Run local Playwright verification", playwrightCommand, playwrightArgs],
    ["Stage related QA files", "git", ["add", specFile, manualCasePath, ".cursor/skills/story-qa-playwright/SKILL.md", ".cursor/skills/story-qa-playwright/scripts/run-story-qa.mjs", "package.json"]],
    ["Commit QA changes", "git", ["commit", "-m", `test: cover manual ${caseId} with Playwright`]],
    ["Push branch", "git", ["push", "-u", "origin", branchName]],
    ["Open PR", "gh", ["pr", "create", "--base", "develop", "--head", branchName, "--title", `test: cover manual ${caseId} with Playwright`, "--body", `## Summary\n- Story / source: manual test cases\n- Adds 1 Playwright case (scripted from the input list; no extra cases).\n\n## Local\n- Command: ${playCommand}\n- Result: passed\n\n## Pipeline\n- The GitHub Actions workflow will start automatically after the PR is created.\n\n## Review\n- Do not merge until a reviewer approves.`]],
    ["Watch CI checks", "gh", ["pr", "checks", "--watch"]],
  ];

  for (const [label, command, argsList] of workflow) {
    runStep(label, command, argsList);
  }

  console.log(`\nQA workflow completed for ${caseId}.`);
} catch (error) {
  console.error(`\nQA workflow failed: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
}