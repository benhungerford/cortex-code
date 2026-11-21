# Browser verification

The rules for checking Shopify and WordPress theme work in a browser. They bind `/build`, its checker, `/qa`, and the `/auto` builder, checker and QA helpers equally. A checker is handed this file verbatim.

Theme work has no test runner and no type checker, so the browser is the feedback loop. On the pilot it caught four real bugs that no test suite would plausibly have caught, and in every case the code read correctly.

## Use a real rendering browser

Use Playwright, not an embedded preview pane, for anything involving scroll, `IntersectionObserver`, or animation. Panes often stop producing frames when nothing is capturing them, and observer delivery is tied to frame production, so a pane that has stopped painting reports a new observer as never firing. Nothing errors. On the pilot the same code got a false pass and then a false fail from this.

Embedded panes also clamp the viewport. Asking for 320px and getting 362px means 320px was not tested. Say which widths you actually used.

## Treat the browser as expensive

Automated request volume against a live storefront trips bot protection, not just rate limiting. On the pilot it returned `429` with `cf-mitigated: challenge` and did not clear across four minutes of polling. Automated `shopify theme dev` traffic has tripped Cloudflare the same way. Bot protection is never worked around, so a tripped challenge ends verification for the session: stop, report it, and name what was not checked.

So:

- One page load per state, then one `evaluate` that runs every assertion for that state and returns them together.
- Don't poll in a loop waiting for a service. Wait once, generously.
- Don't reload a page to check one more thing that could have gone in the same pass.
- Several checkers hitting one live storefront at once is the surest way to trip it. That is why parallel builds are not the default.

## Capture the request, not the appearance

For anything transactional (a cart add, a form post, a checkout step), wrap `XMLHttpRequest.prototype.send` and `window.fetch`, record the payload, and let it through. That proves what the server received rather than what the page seemed to do, in one page load instead of a dozen clicks. Then read the resulting state once from the platform's own JSON endpoint (for Shopify, `/cart.js`) and compare it with what the UI claimed.

## Suspect anything a third-party app owns

Third-party widgets are the most common source of bugs that survive review.

- They write properties, not attributes. `MutationObserver` does not report a property write, and a `div` styled as a control emits no `change` event. If a widget can change state, assume you will not be told.
- Their updates are asynchronous. A single recompute after an interaction races them and fails intermittently. Re-check over a bounded window instead of guessing one delay. On the pilot the subscription app rewrote the price node after a variant change, and the first recompute raced it.
- They render their own values. Mirroring the theme's element can be faithful and still wrong, because the app never updated it.

## Look at the page, not just the assertions

Criteria can all pass while the screen is wrong. On the pilot the cart was always correct (right variant, right selling plan, right price) and the sticky bar displayed $22.00 while the shopper was about to pay $18.70. Every written criterion was satisfiable in that state.

- Take a screenshot at each real viewport width the criteria name, and read it.
- Read rendered values against what the system will actually do.
- Open the drawers, modals, overlays and banners the feature can collide with. Use `elementFromPoint` to find what is actually on top. A `z-index` comparison means nothing across stacking contexts, and raising the number looks like a fix while changing nothing.
- In QA, walk the flow end to end once as a customer, not as a list.

## Verdicts

Each item gets a verdict and the observation behind it. A verdict with no observation is not a check.

| Verdict | Means |
|---|---|
| Pass | Observed true in the browser, this round. |
| Fail | Exercised, and it was false. Say what was on the page, not what the code suggests. |
| Blocked | Could not be exercised, with the reason (no sold-out variant on the store, 2FA on checkout, bot protection). |

"The cart line came back with `selling_plan` set and a price of $18.70" is an observation. "The form carries the selling plan, so it must work" is a deduction, and deductions don't pass items. Reviewing the diff is not looking at the screen, and is never recorded as if it were.
