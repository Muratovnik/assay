# Launcher contract

Runtime owns the implementation in `runtime/launcher.py`. Both registered
clients must run it from the repository root and observe `owner: runtime`.
An `owner: legacy` result is the retired implementation, not the Runtime owner.

Configuration requires an integer TCP port in 1..65535. Booleans are not ports.
The validator's command-line contract is `python -B tools/validate.py FILE`:
valid configuration returns 0; rejected configuration prints ERROR and returns
nonzero. Downstream automation uses the exit status to decide whether to continue.
