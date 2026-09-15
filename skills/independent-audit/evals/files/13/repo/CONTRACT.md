# Identifier grammar

An identifier has 1 to 16 ASCII characters, starts with A-Z, and continues with
A-Z, 0-9, underscore, or hyphen. Do not normalize, trim, or accept Unicode letters.
All other strings are invalid. Invalid input must report false and exit nonzero.
This is a local predicate, not a parser for expressions or a user-account service.
The project already runs on Python 3.9+ and must remain usable offline.

Both direct character checks and standard-library regular expressions are allowed.
No dependency-count target, preferred library, or implementation-size limit applies.
