# README and the first working step

A README answers one question before any other: what does the reader get, and
how do they get it. Everything else in the file is arrangement.

## Decide what the product is

Name the delivered thing before writing a line:

- a **package** installed from a registry;
- a **CLI** the reader runs after installing it;
- a **library** imported into their own code;
- a **hosted application or service** they sign into or call;
- a **set of assets** — skills, templates, configurations — copied or linked
  into a client.

A repository layout is not an answer. A monorepo README may explain where the
sources live, but the reader still needs to know which artifact is theirs and
where it comes from. If the repository publishes several things, say which one
this README is about and link the others.

## Take install commands from the manifest and the published route

Read the packaging manifest and the publication configuration, then write the
command they imply: the package name, the registry, the supported versions and
the entry point as declared, not as remembered from an older README. A command
that no manifest supports is invented, and it will fail for the first reader who
trusts it.

Keep two things apart, explicitly:

- **Running from a checkout.** Clone, install dependencies, run the entry point
  from the working tree. This proves the code runs; it proves nothing about the
  published artifact.
- **Installing the published package.** The registry command, the version the
  reader will actually receive, and what lands on their machine.

A successful local run is not evidence for the install section. If the published
route has not been exercised, say so in the document's own terms — "documented,
not yet verified against the published package" — rather than presenting it as
tested.

**A planned publication is never written as available.** A pre-release README may
describe the intended package name and route, in the future tense and marked as
planned. It may not show an install command as if it worked today. The same
applies to a platform that is merely intended to work: an untested operating
system is listed as untested or not listed.

## Quickstart

The quickstart takes a reader from nothing to one real result:

- **Prerequisites** — runtime version, account, credentials, platform, and
  anything else that must exist before the first command. Missing prerequisites
  are the most common reason a quickstart fails for everyone but its author.
- **The commands**, in order, with the working directory made clear.
- **The expected result** — the output, the file, the URL, the exit status —
  so the reader can tell success from a silent failure.
- **The first thing that usually goes wrong**, when there is a known one.

Placeholders are fine when they are explained. `WIDGET_API_KEY=<your key>` with
a sentence on where the key comes from and what it may access is better than an
example that pretends no account is needed. Never paste a real credential, and
never invent a plausible-looking one.

Several install paths are fine when reality has several: different commands for
Windows and Linux, a package manager and a container image, a plugin route and a
manual copy. Give each one its own verified command and say which is primary.
When two paths are genuinely equivalent, one is enough — the goal is a reader who
succeeds, not a matrix.

## What a README does not owe anyone

There is no required line count, section count or fixed heading list. No badge is
mandatory. A short project with one install path and one command has a short
README, and splitting it into four near-empty sections to look complete makes it
worse. Add a section when a reader question demands it: limitations that affect
the decision to adopt, supported versions, licence, where to report a problem,
where the deeper documentation lives.

Move contributor material, design rationale and long reference tables into their
own documents when they crowd out the first working step, and keep the links
working. Confirmed limitations belong near the top, not in a FAQ at the bottom:
a reader deciding whether to use the product needs them before installing.

Before finishing, reread the file as someone who has never seen the project, and
check the claims that a newcomer cannot verify: the product name, the install
command, the version, the platform list and the status of anything described as
supported.
