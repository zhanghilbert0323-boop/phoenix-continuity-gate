# 1.0 release gates / 1.0 放行清单

This is a current engineering and evidence checklist, not a completion percentage,
release-date promise, customer claim or replacement for actual CI results.

## Candidate scope

A local Python/Git evidence gate with named reviewed checks, stable CLI/JSON,
one same-job GitHub Actions adapter, fixed artifacts and a documented MIT/service
business boundary. Not a hosted team dashboard or authenticated evidence service.

| Gate | Candidate work / remaining evidence |
| --- | --- |
| Named check configuration and isolation | Implemented; verify command/config changes, separate checks, unknown input and no implicit refresh in tests |
| Actual workflow adapter | Composite action and same-job fixture lifecycle added; hosted refresh/PASS/stale-BLOCK execution must pass, not merely YAML review |
| Recovery | Real child-exit/PENDING test added; residue requires reviewed manual recovery; detached processes and hardware-failure durability are not guaranteed |
| Interface/upgrade boundary | CLI contract, separate-environment rollback and current schema support documented; validate installed package |
| Distribution and license | MIT chosen by owner; fixed candidate ZIP/wheel must contain correct version/license and pass installation checks |
| Scale observation | Internal synthetic probe: 1000 tracked 1 KiB files, five unchanged inspections; median 0.603 s on one Windows/Python 3.14.4 environment. See the saved report below; no customer-scale or supported-size claim |
| Independent use | No independent team result recorded in this checklist; require an external authorized workflow observation before calling it externally validated |
| Paid team value | No verified buyer/payment; a scoped paid pilot and repeated product demand remain commercial gates, not coding tasks |

The [saved probe](experiments/results/scale-probe-1.0rc1.json) can be reproduced
with `python -B experiments/scale_probe.py --files 1000 --repeats 5`. No output
record paths or raw command logs are included in that report.

Engineering evidence may justify an explicitly labeled `1.0.0rc1` candidate. A final
paid team 1.0 readiness claim must not silently mark external/commercial gates as
passed. If existing workflows already suffice or blocking is too noisy, revise the
scope before expanding the product. Source changes and artifact versions remain
separate from claims about adoption or revenue.

中文：工程实现能由我们推进，外部团队试用、购买理由和付款不能由内部测试代替。
候选版不是正式商用成熟版。每项以对应提交、测试和实际观察为准。
