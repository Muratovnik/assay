# Migrate renamed skills without duplicate discovery

This revision changes three canonical names and paths:

| Previous name | Current name | Reason |
| --- | --- | --- |
| `code-maintenance` | `code-change` | New implementation, repairs and refactoring share the same authorized change boundary |
| `operations-ui-delivery` | `ui-delivery` | Product UI delivery is not limited to operations screens |
| `skill-design` | `skill-evaluation` | The method diagnoses and evaluates behavior; it is not a general authoring tool |

All active references, catalog entries and client metadata move together. There
are no old-name shim skills: two discoverable copies would compete for the same
task. Historical release records remain unchanged. Update explicit invocations,
bookmarks and downstream integration references to the names above.

## Linked checkout

Before switching the installed checkout to the new revision, keep the existing
revision identifier, selected clients, adapter bytes and link destinations in an
authorized location outside the managed roots. With the **old revision still in
the original installed checkout path**, preview and remove its owned entries:

```text
python tools/assay.py plan
python tools/assay.py uninstall-links
```

Retain the same `--home` and `--client` selection used for that installation.
A different checkout or worktree has different source destinations and is not an
equivalent removal source. Modified adapters and foreign targets are preserved
and reported; do not delete them to make the migration pass.

Then switch that checkout to the selected new revision, set up its declared
isolated tooling environment, inspect the new plan and install:

```text
python tools/assay.py plan
python tools/assay.py install-links
```

Unrelated source-format errors no longer block uninstall, but catalog identity,
exact owned targets, safe parents and reproducible profile bytes still matter.
When rollback is needed, remove exact new entries from the new revision first,
restore the old checkout revision and use the retained external snapshot and old
installer. Do not merge old and new skill directories.

## Plugin or copied skills

Use the same client/installer and scope that created the old installation to
remove or update it. Assay's link installer does not own third-party copied
files. Review the installer's removal preview and do not remove unrelated skills.
Confirm that the old names are no longer discoverable before enabling the new
ones. A plugin update is not assumed to clean separate manual copies.

For composed methods, select the full collection with the skills CLI's
`--skill '*'`. Select individual new names only for their documented bounded
core. Check the reported destination against the current client documentation.

Start a fresh session and verify the new names and actual loading in the client.
An installation receipt is not a behavior result. No migration changes user
permissions, registers an advisor or enables paid services.

Open changes based on an earlier revision must reconcile these paths rather
than reintroduce old-name copies. In particular, lifecycle and flow-mapping
proposals remain separate changes and retain their own scopes.
