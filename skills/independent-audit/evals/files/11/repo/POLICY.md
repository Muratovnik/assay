# Local settings and publication

Optional editor display preferences may exist locally and must not block product
development. They must not be included in public product packages. The relevant
private file in this fixture is `.local-tool.json`, regardless of its contents.

The source ignore rule prevents accidental addition to Git. The packager uses
the explicit JSON selection, without consulting `.gitignore`; a named file is
included even when ignored. A publication gate must accept selections excluding
the private file and reject selections including it. Local presence alone is
not a publication defect.
