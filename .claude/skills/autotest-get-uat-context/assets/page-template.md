# Page: <Page Name>

- **URL:** <https://example.com/path>
- **Purpose:** <what this page is for, in one or two sentences>
- **Last verified:** <YYYY-MM-DD>
- **WebMCP tools:** <none, or list tool names with a one-line description each — see the
  playwright-cli SKILL.md's WebMCP section for how to call them>

## Key elements

| Element | Locator | Notes |
|---|---|---|
| Search input | `getByRole('textbox', { name: 'Search' })` | <required, validation, etc.> |
| Submit button | `getByTestId('submit-button')` | <disabled until X, etc.> |

Locators come from `playwright-cli generate-locator <ref> --raw` — never record raw snapshot refs
(`e15` etc.), they don't survive a new snapshot.

## Forms

### <Form name, e.g. "Contact form">

| Field | Type | Required | Validation |
|---|---|---|---|
| Email | text | yes | must be a valid email format |

## Notable states

<Loading, empty, and error states you actually observed — skip states you didn't check rather than
guessing.>

## Stale / unverified

<Anything previously documented here that no longer matches the live page. Remove this section if
everything above is current.>
