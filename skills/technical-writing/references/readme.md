# README and the first working step

Start with what the intended reader obtains: a package, CLI, library, hosted
service or reusable assets. A monorepo is a source layout, not a delivery route.
Apply this procedure to installation/quickstart work or a whole README, not to
an unrelated local wording review.

## Select a supported route

1. Identify the audience: product user, contributor, operator or someone running
   an unreleased checkout. Infer from the request and sources; ask only if the
   distinction changes the instructions.
2. Establish which delivery routes are available. A manifest supplies the package
   and entry-point declarations. Release/registry evidence establishes publication
   within its scope. Repository code can support a checkout route.
3. Choose the primary route for that reader. Preserve working alternatives when
   relevant; do not call an alternative broken without evidence.
4. Verify prerequisites, command names, working directory and the first observable
   result to the extent the task permits.

Keep published installation and checkout execution distinct. A successful
checkout does not prove the published wheel works; an available wheel does not
prove the checkout is broken. `python -m` may coexist with a console script.
Editable installation can be correct for development or an unreleased project.

If the user is consuming a released package and publication is supported, lead
with that route instead of repairing a contributor-only setup. If publication
is unknown, do not fabricate it or force a registry command. A planned image or
package stays planned. Do not present a route as personally tested when only
source or release documentation was inspected.

## Quickstart

Give the needed starting conditions, ordered commands and an observable result.
A runtime requirement in the manifest is useful when it was not already stated
in the reader's starting environment. Use the actual name of the installed
command, which may differ from the distribution name.

Credentials and user-controlled paths may be placeholders when explained. Keep
them labelled and do not invent real credentials or reachable accounts. Treat
explicitly anonymized contacts as fixture values rather than publication bugs;
a real unresolved production placeholder still deserves attention.

Use separate platform paths when they differ. Do not force one package-manager
command when the product requires alternatives. Separate supported, documented
and actually exercised claims; no blanket downgrade of documented support solely
because this editor did not test every platform.

## Include only useful sections

There is no required line count, heading list, badge row or section quota. Keep
orientation, useful limitations and the first working step visible. Move long
reference or contributor material only when doing so helps the chosen reader,
and retain links to it. Do not delete relevant warnings to shorten the README.

A feature-list review need not invent a Quickstart. An installation edit need
not rewrite the overview. If the request is a whole-document publication audit,
check the load-bearing path and readiness explicitly rather than merely filling
headings. Resolve local links from their actual source path, not a packet alias.

Return usable Markdown. An actual README file is not enclosed in a code fence.
When showing its literal source in a reply, choose an outer fence longer than
any matching fence in the content.
