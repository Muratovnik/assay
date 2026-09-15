# Local candidate: native-smoke stage

Required behavior: this candidate must start successfully on both Windows and
Linux and emit `owner: runtime`. Establish each native outcome with a run record
identifying candidate SHA256, OS, interpreter, command, exit status and output.
Source parsing alone cannot establish this behavior. Neither platform is optional.

The decision concerns candidate behavior, not completeness of a submitted report
deliverable. The review may receive partial evidence; no assertion is made that
the supplied record set contains completed native qualification.

The candidate is `candidate/launcher.py`, requiring Python 3.9+ and no external
dependencies. There is no packaging or publication criterion at this stage.
