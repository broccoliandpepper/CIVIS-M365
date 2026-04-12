# Versioning and Tags Policy

## Goal
Keep V2 history clean with predictable release points and easy rollback.

## Branching (simple)
- `main`: stable integration branch.
- Short-lived feature branches: `feat/<topic>`.
- Optional fix branches: `fix/<topic>`.

## Commit style
Use concise conventional prefixes:
- `feat:` new functionality
- `fix:` bug fix
- `refactor:` internal restructuring
- `docs:` documentation update
- `chore:` tooling, CI, scripts
- `test:` tests only

Example:
- `feat: add SOC anomalies pagination`

## Semantic Versioning
Use `MAJOR.MINOR.PATCH`:
- MAJOR: breaking changes
- MINOR: backward-compatible features
- PATCH: backward-compatible fixes

Current baseline suggestion:
- `v2.0.0` for first stable V2 baseline

## Tagging workflow
1. Ensure main is clean and tests pass.
2. Commit pending changes.
3. Create annotated tag:

```bash
git tag -a v2.0.0 -m "SIEM M365 V2 baseline"
```

4. List tags:

```bash
git tag --list
```

## Suggested cadence
- Patch every bugfix batch: `v2.0.x`
- Minor every completed feature set: `v2.x.0`
- Major only for architecture/API breaks.

## Backup alignment
After each tag, run source snapshot backup:

```bash
python scripts/backup_snapshot.py --keep 30
```

This keeps version control and backup archives aligned at key milestones.
