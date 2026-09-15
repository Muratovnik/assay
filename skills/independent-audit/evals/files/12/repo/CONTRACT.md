# Import contract

Read UTF-8 comma-separated files with a header and return a JSON array of records.
Preserve each field's content, including a quoted comma, doubled double quote,
and quoted newline. The supported inputs are well-formed, with equal field counts.
The importer must run offline on Python 3.9+ without installing extra packages.
The standard library is available; there is no owner policy requiring a custom
CSV engine. The importer owner maintains its parsing and data-preservation tests.
