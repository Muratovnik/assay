# A POSIX alias for the gates. Windows contributors run the same commands
# directly; see CONTRIBUTING.md.
PYTHON ?= python

.PHONY: check render audit

check:
	$(PYTHON) -B tools/check.py --all

render:
	$(PYTHON) -B tools/assay.py render

audit:
	$(PYTHON) .github/relkit.pyz audit
