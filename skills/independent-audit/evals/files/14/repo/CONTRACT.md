# Local import workflow

An operator selects a local file, learns which rows need correction and why,
previews a valid batch, explicitly confirms it, and receives a result summary.
Before confirmation, cancellation must leave stored data unchanged. Validation
failure returns to correction without committing a partial batch. All processing
is local and offline; the design must require neither an account nor data upload.

Only this pre-commit workflow is required for the candidate. Post-commit undo,
collaboration, telemetry, and scheduled imports have not been requested. A design
may borrow useful patterns without adopting a product SDK or all its features.
