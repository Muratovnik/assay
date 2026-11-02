"""Tell a scratch path, which no hook check reads as the user's code or documents, from a checkout.

A scratch directory (tmp, temp, scratchpad, .private, .tmp) holds one-off files and notes.
A task worktree below tmp/worktrees/<name> is a real checkout, so its files are not scratch.
The branch check and the mid-turn note both ask this question, so it is defined once here.
"""
from __future__ import annotations

import re

# A scratch directory is no one's code, but a task worktree below tmp/worktrees holds a real checkout.
WORKTREE = re.compile(r"(?:^|[\\/])tmp[\\/]worktrees[\\/][^\\/]+(?=[\\/])", re.I)
SCRATCH = re.compile(r"(?:^|[\\/])(?:tmp|temp|scratchpad|\.private|\.tmp)[\\/]", re.I)


def is_scratch(path):
    """Whether a path (a str) lies in a scratch directory outside any task worktree's checkout."""
    return bool(SCRATCH.search(WORKTREE.sub("", path)))
