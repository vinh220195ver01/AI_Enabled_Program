import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const option = (name, fallback) => {
  const index = args.indexOf(`--${name}`);
  return index >= 0 ? args[index + 1] : fallback;
};
const caseArg = args.find((arg) => !arg.startsWith("--"));

if (!caseArg) {
  console.error("Usage: node <skill>/scripts/run-story-qa.mjs <case-id> [--dry-run] [--base <branch>]");
  process.exit(1);
}

const configFile = option("config", "qa.config.json");
const configPath = resolve(process.cwd(), configFile);
const config = existsSync(configPath) ? JSON.parse(readFileSync(configPath, "utf8")) : {};
const caseId = caseArg.toUpperCase();
const slug = caseId.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const caseDir = option("case-dir", config.manualCaseDir || "manual-test-cases");
const specDir = option("spec-dir", config.specDir || "tests/e2e");
const manualCasePath = option("case", config.manualCasePath || `${caseDir}/${caseId}`);
const specFile = option("spec", config.specFile || `${specDir}/${slug}.spec.ts`);
const detectBaseBranch = () => {
  for (const branch of ["develop", "main", "master"]) {
    const branchResult = spawnSync("git", ["show-ref", "--verify", `refs/remotes/origin/${branch}`], { encoding: "utf8" });
    if (branchResult.status === 0) return branch;
  }
  const result = spawnSync("git", ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], { encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim().replace(/^origin\//, "") : "main";
};
const baseBranch = option("base", config.baseBranch || process.env.BASE_BRANCH || detectBaseBranch());
const branchName = option("branch", config.branchPrefix ? `${config.branchPrefix}/${slug}` : `test/${slug}`);
const ghCommand = process.platform === "win32" ? "gh.exe" : "gh";
const playwrightCommand = process.platform === "win32" ? "npx.cmd" : "npx";
const playwrightArgs = ["playwright", "test", specFile, "--reporter=line"];
const playCommand = `${playwrightCommand} ${playwrightArgs.join(" ")}`;
let temporaryStashCreated = false;

const runCommand = (command, argsList, allowFailure = false) => {
  const result = spawnSync(command, argsList, {
    cwd: process.cwd(),
    shell: process.platform === "win32" && command.endsWith(".cmd"),
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
  const configNames = ["playwright.config.ts", "playwright.config.js", "playwright.config.mts", "playwright.config.mjs"];
  if (!existsSync(`${repoRoot}/package.json`) || !configNames.some((name) => existsSync(`${repoRoot}/${name}`))) {
    throw new Error("Run this script from a project root containing package.json and playwright.config.*.");
  }

  if (!existsSync(`${repoRoot}/${manualCasePath}`)) {
    throw new Error(`Manual case file not found: ${manualCasePath}`);
  }

  const gitRoot = runCommand("git", ["rev-parse", "--show-toplevel"], true).stdout?.trim();
  if (!gitRoot || gitRoot !== repoRoot.replace(/\\/g, "/")) {
    throw new Error("Git repository root does not match the current working directory.");
  }
};

const getUnexpectedRepoChanges = () => {
  const status = runCommand("git", ["status", "--porcelain", "--untracked-files=all"], true).stdout;
  const allowedExactPaths = new Set([specFile, manualCasePath, "package.json", "package-lock.json", configFile]);
  const allowedDirectories = ["tests/pages/", "tests/fixtures/", ".github/workflows/"];
  const allowedWorkflowFiles = [".cursor/skills/story-qa-playwright/scripts/run-story-qa.mjs"];
  const unexpected = (status ?? "").split(/\r?\n/).filter(Boolean).map((line) => line.slice(3).replace(/\\/g, "/"))
    .filter((path) => !allowedExactPaths.has(path) && !allowedWorkflowFiles.includes(path) && !allowedDirectories.some((directory) => path.startsWith(directory)));
  return unexpected;
};

const preserveUnexpectedRepoChanges = () => {
  const unexpected = getUnexpectedRepoChanges();
  if (unexpected.length === 0) return;

  console.log(`Preserving unrelated worktree changes: ${unexpected.join(", ")}`);
  const result = runCommand("git", ["stash", "push", "-u", "-m", `story-qa unrelated changes ${caseId}`, "--", ...unexpected], true);
  if (result.status !== 0) {
    throw new Error(`Unable to preserve unrelated worktree changes: ${unexpected.join(", ")}`);
  }
  temporaryStashCreated = true;
};

const restoreUnexpectedRepoChanges = () => {
  if (!temporaryStashCreated) return;

  console.log("Restoring unrelated worktree changes.");
  const result = runCommand("git", ["stash", "pop"], true);
  if (result.status !== 0) {
    throw new Error("Unrelated changes were preserved in the stash but could not be restored cleanly.");
  }
  temporaryStashCreated = false;
};

const ensureBranchNotExists = () => {
  const result = runCommand("git", ["show-ref", "--verify", `refs/heads/${branchName}`], true);
  if (result.status === 0) {
    throw new Error(`Branch already exists: ${branchName}`);
  }
};

const ensureGhAuth = () => {
  const result = runCommand(ghCommand, ["auth", "status"], true);
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
    shell: process.platform === "win32" && command.endsWith(".cmd"),
    stdio: "inherit",
  });

  if (result.status !== 0) {
    throw new Error(`${label} failed with exit code ${result.status ?? 1}`);
  }
};

try {
  ensureRepoReady();

  if (dryRun) {
    console.log(`Case: ${caseId}`);
    console.log(`Manual case: ${manualCasePath}`);
    console.log(`Spec: ${specFile}`);
    console.log(`Base branch: ${baseBranch}`);
    console.log(`QA branch: ${branchName}`);
    console.log(`Local command: ${playCommand}`);
    console.log("Dry run passed: project, manual case, and Playwright spec were found.");
    process.exit(0);
  }

  preserveUnexpectedRepoChanges();
  ensureBranchNotExists();
  ensureGhAuth();

  const workflow = [
    ["Ensure repo state", "git", ["switch", baseBranch]],
    ["Pull base branch", "git", ["pull", "--ff-only", "origin", baseBranch]],
    ["Create QA branch", "git", ["switch", "-c", branchName]],
    ["Validate test file exists", "node", ["-e", `require('node:fs').existsSync(${JSON.stringify(specFile)}) || (() => { throw new Error(${JSON.stringify(`Missing test file: ${specFile}`)}) })()`]],
    ["Run local Playwright verification", playwrightCommand, playwrightArgs],
    ["Stage related QA files", "git", ["add", specFile, manualCasePath, "tests/pages", ...(existsSync("tests/fixtures") ? ["tests/fixtures"] : []), ".github/workflows", ".cursor/skills/story-qa-playwright/scripts/run-story-qa.mjs", "package.json", "package-lock.json", ...(existsSync(configPath) ? [configFile] : [])]],
    ["Commit QA changes", "git", ["commit", "-m", `test: cover manual ${caseId} with Playwright`]],
    ["Pull target branch and verify conflicts", "git", ["pull", "--no-edit", "origin", "develop"]],
    ["Push branch", "git", ["push", "-u", "origin", branchName]],
    ["Open PR", ghCommand, ["pr", "create", "--base", baseBranch, "--head", branchName, "--title", `test: cover manual ${caseId} with Playwright`, "--body", `## Summary\n- Story / source: manual test cases\n- Adds 1 Playwright case (scripted from the input list; no extra cases).\n\n## Local\n- Command: ${playCommand}\n- Result: passed\n\n## Pipeline\n- The GitHub Actions workflow will start automatically after the PR is created.\n\n## Review\n- Do not merge until a reviewer approves.`]],
    ["Watch CI checks", ghCommand, ["pr", "checks", "--watch"]],
  ];

  for (const [label, command, argsList] of workflow) {
    runStep(label, command, argsList);
  }

  console.log(`\nQA workflow completed for ${caseId}.`);
} catch (error) {
  console.error(`\nQA workflow failed: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
} finally {
  try {
    restoreUnexpectedRepoChanges();
  } catch (error) {
    console.error(`\nQA workflow cleanup failed: ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 1;
  }
}