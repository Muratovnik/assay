# Runtime launcher

Python 3.9+; no external dependencies. From this directory:

```text
python -B runtime/launcher.py
python -B legacy/launcher.py
python -B -m unittest discover -s tests
```

Both launchers print the Runtime owner and exit. `clients/` registers the editor
and supported partner; `python` means the available Python interpreter.
See [the compatibility contract](CONTRACT.md), [historical layout](docs/archive.md),
and [security training example](docs/security-training.md).
