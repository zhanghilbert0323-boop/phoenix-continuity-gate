# Candidate public interface and compatibility contract

Status: proposed for 1.0; exercised by candidate tests, not a claim of production
adoption. The supported machine interface is the installed CLI, not every Python
module/private helper. Python helpers and `managed` remain documented examples.

| Interface | Structured contract |
| --- | --- |
| `phoenix-gate inspect --repo ... --record ... --json` | `report_schema_version: 1`, assessment status, verdict, execution, freshness, findings, scope and error |
| `phoenix-gate team validate --config ...` | `team_schema_version: 1`, operation, valid flag; project/check IDs on success, BLOCK/error on failure |
| `phoenix-gate team status --config ... --state ... [--check ...]` | Team schema 1, overall verdict and per-check workflow schema 1 assessments/decisions |
| `phoenix-gate team refresh --config ... --state ... --check ...` | Same team schema; exactly one explicit configured command attempt |
| `phoenix-gate --version` | Package version, without repository inspection or command execution |

Existing `record`, `inspect`, `check`, `demo` and `demo-record` invocations remain.
`check` reads a handoff claim, not observed command execution. Human-readable output,
English finding/reason wording, ordering of findings, private state directory
layout and internal helper functions are not stable machine contracts.

## Consumer rules

- Exit 0 = PASS, 1 = REVIEW, 2 = BLOCK or handled input/state error. Only exit 0
  with a recognized, consistent completed report can be considered limited READY.
- CLI argument syntax errors use argparse stderr and may not be JSON. Non-JSON,
  unknown schema, contradictory fields, abnormal process termination or missing
  output must stop the consuming workflow. Do not treat an empty result as PASS.
- Each valid machine invocation emits one JSON object; it does not echo stored
  stdout/stderr or command argv. Error text and findings can still expose paths.
- Consumers may ignore unknown additive report fields. Config schema 1 instead
  rejects unknown keys to catch typos. Never infer new enum semantics.
- A failed historical command is not proof current code fails. A stale historical
  success is not evidence current code passed. A timeout is not a success.
- READY is an evidence result, not operation permission, proof of coverage or an
  authorization to merge/deploy. The caller separately owns that decision.

## Upgrade and rollback

1. Keep the previous package/venv, config and private state. Do not copy raw
   evidence into public tickets or overwrite older execution records.
2. Install a fixed candidate in a separate virtual environment. Run its version,
   disposable demo and config validation before pointing it at a real project.
3. Use a new outside state root for the candidate. Do not mix candidate and older
   writers in one state tree. `{python}` changes when the interpreter path changes,
   so fresh evidence is expected; old results are never silently converted.
4. If validation fails, return to the previous environment and its own state root.
   Check freshness again; rollback does not make old evidence current by itself.

Evidence schema 1 and unbound managed-state schema 1 remain readable by their
original interfaces. New bound-check state is intentionally rejected by the
unconfigured managed interface. No in-place downgrade or cross-machine record
migration is promised. Published artifact bytes are not replaced in place.

For a final 1.0, incompatible changes to the declared public contract require a
major version; compatible additions a minor version; compatible fixes a patch.
Candidate versions may change before final 1.0 and must be identified as such.
