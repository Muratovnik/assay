# Upgrading a linked install

**English** · [Русский](../ru/how-to/upgrade-linked-install.md) · [简体中文](../zh-CN/how-to/upgrade-linked-install.md)

This page is for you if you installed assay in a checkout with the symlink
installer — `python tools/assay.py install-links` — and now want to move that
same installation to a newer revision of the checkout. It assumes you can use
`git` and a terminal and know where your checkout lives. It does not cover the
plugin or skills-CLI install routes; see [Installing assay](../install.md) for
those, and [How assay is put together](../architecture.md) for how the linked
install works underneath.

**Before you touch anything:** copy the existing adapter bytes and link
destinations somewhere outside the managed roots. That copy is your only way
back if the upgrade goes wrong. A state file sitting beside the installation
is not a backup of it.

## Starting state

- assay is installed in this checkout via `install-links`, at the revision
  currently checked out.
- The managed targets are the ones `install-links` created:
  ```text
  ~/.agents/skills/<name>
  ~/.claude/skills/<name>
  ~/.codex/agents/<profile>.toml
  ~/.claude/agents/<profile>.md
  ```
- You want to move to a newer revision of the same checkout, end up with none
  of the old adapter files left behind, and be able to undo the change if
  something goes wrong.

## Steps

### 1. Save a copy of the current adapters

Before running any command below, copy the current contents of the four
target locations above to a location outside those trees — for example
another directory on the same machine. Keep both the file bytes and the link
destinations; this is the snapshot you'll restore from if you need to roll
back.

### 2. Uninstall from the revision you're currently on

Still on the current revision (do not pull yet), run:

```text
python tools/assay.py uninstall-links
```

This removes only entries whose link target or rendered bytes still exactly
match what this revision would install. Anything you changed by hand is left
alone and reported, not overwritten. Run this step *before* switching
revisions: `uninstall-links` only recognizes the bytes its own revision
produced, so running it from the new revision instead would leave the old
adapters in place for you to clean up by hand.

### 3. Move the checkout to the new revision

Pull or check out the revision you want, the way you normally would with
`git`. If `requirements-tools.txt` changed, re-run
`python -m pip install -r requirements-tools.txt` as described in the install
guide.

### 4. Install from the new revision

```text
python tools/assay.py install-links
```

If you want to preview what this will do first, `python tools/assay.py plan`
writes nothing — it only reports what each target would become — and
`--home` can point a whole plan at an isolated directory for a dry run.

`install-links` preflights the whole plan before writing anything. For each
of four cases — a real directory where a link should go, a foreign link, a
modified adapter, or a reparse-point parent — it stops the entire run before
the first write. That check covers those named cases; a clean exit from it
is not a general guarantee that nothing elsewhere was written.

**On Windows**, creating a directory symlink requires the permission for it
(normally Developer Mode or an elevated terminal). If that permission is
missing, the installer fails closed — it does not fall back to a shell
command to work around it.

## Result

After step 4, the four target locations hold the links and rendered adapters
for the new revision, and none of the previous revision's adapter files
remain. The full inventory of what gets created is in
[How assay is put together](../architecture.md#inventory).

## If something goes wrong

Restore the files and link destinations you saved in step 1 to their original
locations. Don't mix bytes from the old snapshot with a registration from the
new revision — restore the whole snapshot as a unit.

## Limits

- The preflight in step 4 only refuses the four named conditions above; it
  doesn't promise that every possible failure mode leaves nothing written.
- Manual edits you made to a link or adapter (drift) are preserved and
  reported by both `uninstall-links` and `install-links`, not silently
  discarded — but that also means drift can cause a preflight refusal you'll
  need to resolve by hand.
