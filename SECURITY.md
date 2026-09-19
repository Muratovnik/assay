# Security

**English** · [Русский](SECURITY.ru.md) · [简体中文](SECURITY.zh-CN.md)

## What you are installing

A skill is a set of instructions an agent will follow, and some skills here ship
scripts an agent can execute. Installing this library gives an agent in your
environment new instructions, and in some cases new code it may run with your
permissions.

That is true of every skill library, including this one. Read what you install.
The gates in this repository check structure and consistency; they cannot tell
you whether a method is right for your work.

What this library does not do:

- It does not call home. There is no telemetry, no account and no usage
  reporting.
- It does not install anything into your environment on its own. The tools take
  explicit paths and refuse to guess.
- It does not read or write your client's settings. The installer reports a
  missing prerequisite rather than fixing it for you.

The one network path is opt-in: `route-subagents` can consult public benchmark
sources through a local MCP server you register yourself, caching results in a
directory you name. Without that registration the skill works and reaches nothing.

## Prompt injection

These skills read repositories, documentation and, in the research method, web
pages. Content from those sources is data, not instruction. The methods say so,
but no instruction is a guarantee: a sufficiently determined page can still try
to steer an agent that reads it.

Treat an agent session that has read untrusted content the way you would treat a
program that parsed it. Review what it proposes before acting on it, and do not
grant an agent permissions you would not grant that content.

## Reporting a vulnerability

Report privately through GitHub's vulnerability reporting on this repository,
rather than opening a public issue. Please include what you found, how to
reproduce it and what an attacker would gain.

This is a single-maintainer project. There is no response-time commitment; you
will get an acknowledgement and an honest estimate rather than a service level.

## Scope

In scope: a script here that executes something the caller did not ask for, an
installer that writes outside its declared targets, a method that instructs an
agent to exfiltrate or destroy data, a dependency pinned to something it should
not be.

Out of scope: a model producing a poor answer, a skill activating when you would
rather it had not, and anything about a client's own sandbox or permission model.
Those are worth an issue, not a private report.
