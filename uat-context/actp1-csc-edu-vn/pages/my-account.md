# Page: My account

- **URL:** <https://actp1.csc.edu.vn/my-account/>
- **Purpose:** Combined login + registration page (WooCommerce default). Logged-out view shows both
  forms side by side.
- **Last verified:** 2026-09-24
- **WebMCP tools:** none observed

## Key elements

| Element | Locator | Notes |
|---|---|---|
| Login username/email | `getByRole('textbox', { name: 'Username or email address *' })` | |
| Login password | `locator('#password')` | Accessible name is ambiguous with the register password field ("Password Required"); `generate-locator` fell back to the WooCommerce standard `#password` ID |
| Remember me | `getByRole('checkbox', { name: 'Remember me' })` | |
| Login submit | `getByRole('button', { name: 'Logg in' })` | Site copy typo — button label is literally "Logg in", not "Log in" |
| Lost your password link | `getByRole('link', { name: 'Lost your password?' })` | → `/my-account/lost-password/`, not explored |
| Register email | `getByRole('textbox', { name: 'Email address  Required' })` | Note: double space in accessible name (site markup artifact) |
| Register password | `locator('#reg_password')` | Same ambiguous-name situation as login password; use the ID |
| Register submit | `getByRole('button', { name: 'Register' })` | |

## Forms

### Login

| Field | Type | Required | Validation |
|---|---|---|---|
| Username or email | text | yes | not tested |
| Password | password | yes | not tested |

### Register

| Field | Type | Required | Validation |
|---|---|---|---|
| Email address | text | yes | not tested |
| Password | password | yes | not tested |

## Notable states

- No test credentials were available this pass, so successful login, failed login, and successful
  registration states are all unverified.

## Stale / unverified

- Post-login "My account" dashboard (orders, addresses, account details tabs) is entirely
  undocumented — requires a logged-in session to explore.
