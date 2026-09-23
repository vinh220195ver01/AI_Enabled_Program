# Default project layout and conventions

Loaded by `SKILL.md` step 1. These are fallback defaults — an existing, different project convention always takes precedence; check before applying any of this.

## Directory layout

```
tests/
├── e2e/            # one .spec.ts per test case, named <case-id-slug>.spec.ts
├── pages/          # one page object per screen/component, PascalCase class, matching file name
├── actions/         # Business Action functions, grouped by domain (auth.ts, checkout.ts, ...)
└── fixtures/        # Playwright fixtures (custom test() extensions), only if the project already uses fixtures
```

## Spec file conventions

- Import business actions and page objects; a spec should read as a sequence of action calls and assertions, not raw Playwright API calls.
- Comment format directly above the assertion it describes, on separate lines:
  ```ts
  // Step 4: Verify displayed price
  // Expected: Price matches catalog price
  expect(await productPage.getDisplayedPrice()).toBe(catalogPrice);
  ```
- Keep one `test()` block per manual case scenario; if the design lists multiple scenarios for one case (e.g. happy path + validation), one `test()` per scenario inside a shared `test.describe()` for the case.

## Business action file conventions

- Group by domain, not by test case — `actions/auth.ts` holds `login`, `logout`; not `actions/tc001.ts`.
- Export named functions, not a class with static methods, unless the project already uses classes for actions (check existing files first).
- A business action receives a `Page` (or the project's existing fixture type) as its first parameter, per `references/page-object-pattern.md`.

## Naming

- Spec file: `<case-id-slug>.spec.ts` (e.g. `TC001` → `tc001.spec.ts`).
- Page object class: `<ScreenName>Page` (e.g. `ProductDetailPage`).
- Business action function: matches exactly the `finalSignature` approved by `business-action-designer` — do not adjust casing or naming during implementation.
