# Preservation input fixtures

The .txt files are test inputs, not documents to publish. Some are deliberately
empty or malformed. The .bin pair contains deliberately invalid UTF-8. Local
.gitattributes keeps their exact bytes across checkout, including CRLF and the
invalid byte, rather than normalizing them as repository prose.

The tests read them as inputs to scripts/text_check.py; no command inside a
fixture is run. The scanner checks preservation, not link existence, so linked
application pages are not needed here. Expected outcomes are in the evaluator
unittest, never in a runtime instruction file.

These pairs came from the supplied private preservation-fixture snapshot and
are moved into the public skill-local regression suite. They are not heldout.
