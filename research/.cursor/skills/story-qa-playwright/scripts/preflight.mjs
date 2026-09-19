import { existsSync, readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import process from "node:process";

const args = process.argv.slice(2);
const allCases = args.includes("--all");
const cwd = process.cwd();
const configNames = ["playwright.config.ts", "playwright.config.js", "playwright.config.mts", "playwright.config.mjs"];
const failures = [];

const requirePath = (relativePath, message) => {
  if (!existsSync(resolve(cwd, relativePath))) failures.push(message || `Missing ${relativePath}`);
};

requirePath("package.json", "Missing package.json");
requirePath("package-lock.json", "Missing package-lock.json; npm ci will not be reproducible");
if (!configNames.some((name) => existsSync(resolve(cwd, name)))) failures.push("Missing playwright.config.*");

const packageJsonPath = resolve(cwd, "package.json");
if (existsSync(packageJsonPath)) {
  const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8"));
  if (!packageJson.devDependencies?.["@playwright/test"] && !packageJson.dependencies?.["@playwright/test"]) {
    failures.push("@playwright/test is not declared in package.json");
  }
}

const manualCaseDir = resolve(cwd, "manual-test-cases");
const specDir = resolve(cwd, "tests/e2e");
if (allCases) {
  if (!existsSync(manualCaseDir)) {
    failures.push("manual-test-cases directory is missing");
  } else {
    const manualCases = readdirSync(manualCaseDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() || entry.isFile())
      .map((entry) => entry.name.match(/^TC\d+/i)?.[0]?.toUpperCase())
      .filter(Boolean);
    for (const caseId of [...new Set(manualCases)].sort()) {
      const slug = caseId.toLowerCase();
      if (!existsSync(resolve(specDir, `${slug}.spec.ts`))) {
        failures.push(`${caseId} has no matching tests/e2e/${slug}.spec.ts`);
      }
    }
  }
}

const playwrightCli = resolve(cwd, "node_modules/playwright/cli.js");
const hasLocalPlaywright = existsSync(playwrightCli);
const playwrightCommand = hasLocalPlaywright ? process.execPath : (process.platform === "win32" ? "npx.cmd" : "npx");
const playwrightArgs = hasLocalPlaywright ? [playwrightCli, "--version"] : ["playwright", "--version"];
const playwrightVersion = spawnSync(playwrightCommand, playwrightArgs, {
  cwd,
  shell: !hasLocalPlaywright && process.platform === "win32",
  encoding: "utf8",
});
if (playwrightVersion.status !== 0) failures.push("Playwright is not installed; run npm ci");

if (failures.length > 0) {
  console.error("QA preflight failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`QA preflight passed${allCases ? " for all manual cases" : " for the project"}.`);
if (playwrightVersion.stdout?.trim()) console.log(playwrightVersion.stdout.trim());