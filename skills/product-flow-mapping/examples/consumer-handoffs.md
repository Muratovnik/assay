# Two handoffs from the same map

These use `source-only-map.json`, a synthetic collection-editor example. They
are concrete views of the same state/action contract, not Routevane observations
or evidence that an agent has executed either workflow successfully.

## UI redesign acceptance

Consumer: operations-ui-delivery. Scenario `EDIT_FLOW`, transition `FAILURE`,
action/system event `FAIL`, before `PENDING`, after `ERROR`, requirement `REQ`.

Retain the entered draft when saving fails and provide a route back to submission
through `RETRY_SAVE`. `ABANDON` intentionally leaves committed data unchanged.
A designer can replace or combine panels; neither the old layout nor a new modal
is a requirement. Show the failure and retry states in the redesign and keep the
same result/scope contract. The map contains no captures or runtime observations,
so behavior still requires a real application check when available.

## Regression-test design

Consumer: test-writing. Use exactly the same `FAILURE` link, but obtain the
expected retained input from `REQ`, not from a handler or the map author's verdict.
Set up a valid local draft, start Save through the actual relevant boundary,
cause the existing fixture's save failure, and assert retained input plus the
supported retry path. Then exercise the successful or cancelled nearby case as
appropriate to the chosen test boundary. Do not write a test that expects input
loss just because a defective implementation does it.

Reuse the project's test runner and fixtures; this example adds neither. A code
reading or missing screenshot does not become an executed test. The test-writing
method chooses the smallest boundary that actually exposes the promised behavior.

## Reverse lookup

`VIEW` belongs to both `EDIT_FLOW` and `EXPORT_FLOW`. `COPY` and `DOWNLOAD` both
leave it unchanged but have different external results. Their steps must survive
state deduplication. A shared-state redesign review must inspect both scenarios;
a test for successful Save alone does not cover downloads or clipboard effects.
