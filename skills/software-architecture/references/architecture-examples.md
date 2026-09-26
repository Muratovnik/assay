# Contrasting architecture decisions

Read only the example relevant to the disputed decision. These are synthetic
teaching scenarios, not observed deployments or evaluation answers. Paths are
illustrative: an accepted project contract can require different placement.
The core method owns the rules; examples introduce no additional requirements.

## A. A small site grows a real responsibility

**Starting point:** three pages and one contact form, one deployment, no shared
business process. Keep framework entry points and colocate form behavior with
its page, for example `pages/contact/ContactForm.vue`. A component library can
own genuinely shared visual primitives. Empty domain/feature/package layers
protect no identified constraint here.

**Changed condition:** the form becomes a reusable approval process with the
same eligibility rules on two journeys. Give that process a named owner and
contract; move only the shared responsibility. A small internal module may be
enough. A separate package requires its own distribution or ownership reason.

**Alternative/control:** a project already committed to layers can retain its
small compliant structure. This is not a universal ban on layers. Check that
page copy changes stay local, submission has an owner and framework discovery
still works; a proposed check is not an executed check.

## B. Similar presentation versus one business invariant

**Starting point:** catalog and search cards happen to look alike. One displays
pricing tiers, the other highlights matching terms. Their reasons to change are
different. Do not force them into a universal card with unrelated flags.

**Changed condition:** both actions must obey the same product-eligibility
policy. Give that policy one owner now; do not wait for duplicated rules to
produce a bug. A possible non-FSD arrangement is:

```text
src/pages/catalog/CatalogCard.vue
src/pages/search/SearchCard.vue
src/domain/product/eligibility.ts
```

Both callers pass the minimum policy input, not their whole page state. Keep
presentation independent while policy updates apply consistently.

**Alternative/control:** similar expressions for purchasing and archiving have
different meanings and may need separate owners. Another folder name can be
correct. Check both consumers against the agreed invariant and their distinct
UI contracts, rather than asserting this particular tree.

## C. One consumer can justify extraction

**Starting point:** an editor owns an upload operation with progress, cancellation,
temporary resources and stale completions. A local `useUploadSession.ts` beside
`EditorPage.vue` can own that lifecycle even without a second caller.

**Decision:** expose start/cancel/dispose and the necessary state. Keep it local;
extracting a coherent operation does not require global `composables/` or a
package. Moving setters while the page still coordinates every transition merely
splits the same responsibility across files.

**Alternative/control:** a trivial pure expression can stay inline or become an
ordinary function. Validate cancellation, replacement and disposal at the owned
boundary. [Vue permits composables for code organization](https://vuejs.org/guide/reusability/composables.html#extracting-composables-for-code-organization),
not only reuse; verify the installed version's lifecycle behavior before coding.

## D. The same state declaration has different lifetimes

**Starting point:** a module exports mutable session state. In a browser-only
application it may deliberately belong to that application instance.

**Changed condition:** the module is cached by a server process and now serves
requests from different users. Trace who creates and mutates the session; do not
infer isolation from separate route directories. Use the framework's supported
per-request/app-instance owner when user-specific state must not cross requests.

**Alternative/control:** an immutable shared country table is not a session leak.
Do not ban module scope indiscriminately. Check two distinct request identities
and the supported client case. [Vue documents cross-request state pollution](https://vuejs.org/guide/scaling-up/ssr.html#cross-request-state-pollution);
a walkthrough alone does not establish execution isolation.

## E. A file move changes a package contract

**Starting point:** a published library supports `package/legacy-entry`. Internal
files move and a new `exports` map exposes only the main entry. Local tests import
source directly and remain green.

**Decision:** inventory supported external entry points, preserve the legacy
entry through a facade/export mapping or include the compatibility change in
the authorized scope. Test a consumer against the built distributable, not just
updated local source imports. A facade can be the correct long-lived boundary.

**Alternative/control:** a genuinely private unsupported path is different, but
zero repository imports alone does not establish that status. [Node documents
entry-point encapsulation](https://nodejs.org/api/packages.html#package-entry-points).
Verify the target runtime and package version before prescribing a mapping.

## F. Green after relocation can mean missing coverage

**Starting point:** `src/widget.test.ts` moves to `packages/widget/widget.test.ts`;
the active runner selects only `src/**/*.test.ts`. Its remaining tests pass.

**Decision:** compare selected tests and required lint/type-check coverage before
and after. Update the owning configuration where the preservation contract
requires it. In authorized scratch resources, use an intended failure and a
nearby valid case through the actual affected path; a configuration error is not
the desired diagnostic.

**Alternative/control:** a fixture intentionally outside production type-checking
may have a separate effective checker. Preserve that distinction instead of
imposing one glob on every file. Discovery, static checks and execution are
separate guarantees.

## G. Framework discovery is a real consumer

**Starting point:** no user-code import targets `app/catalog/page.tsx`. In a
Next.js App Router project the framework discovers that special file. A sibling
`Card.tsx` is not independently a public route merely because of its directory.

**Decision:** inspect the actual framework/version and discovery chain before
calling a file dead or moving a route. [Next.js describes special files and
colocation](https://nextjs.org/docs/app/getting-started/project-structure).

**Alternative/control:** a helper without imports, registration, discovery or
supported external consumers may really be dead. Establish those facts inside
the authorized scope. Verify the exposed route after an authorized move; absent
runtime access limits the conclusion rather than proving failure.

## H. Domain modules are not automatically services

**Starting point:** three business areas, one team, one release cadence, no
requirement for independent deployment. Compare an explicit modular structure
inside the current process with distribution. Three folders do not justify
three network services, databases and deployment pipelines.

**Changed condition:** one area needs independent release or failure isolation.
Reconsider deployment boundaries and their cost: contracts across versions,
data consistency, partial failure, diagnostics and rollback. A process boundary
must protect a concrete requirement, not an architectural label.

**Alternative/control:** keeping everything together can be wrong when that
operating constraint is binding. Explain the decision with scenarios and cost;
do not replace "always microservices" with "always monolith". Check the promised
independence and explicitly qualify any scenario not actually exercised.
