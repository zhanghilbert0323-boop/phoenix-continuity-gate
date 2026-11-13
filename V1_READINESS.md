# 1.0 release gates / 1.0 放行清单

This is a current engineering and evidence checklist, not a completion percentage,
release-date promise, customer claim or replacement for actual CI results.

Verified candidate: [v1.0.0-rc1](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/releases/tag/v1.0.0-rc1),
fixed source `a914df4c78e6206007f975fee879beb7c0b64658`. Its exact ZIP passed 91
tests on Windows/Python 3.14.4; the wheel built from that ZIP passed fresh-environment,
cross-directory installation checks. All three public downloads matched local
SHA-256 hashes. See the [four-matrix hosted run](https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/actions/runs/43391438621).

## Candidate scope

A local Python/Git evidence gate with named reviewed checks, stable CLI/JSON,
one same-job GitHub Actions adapter, fixed artifacts and a documented MIT/service
business boundary. Not a hosted team dashboard or authenticated evidence service.

| Gate | Candidate work / remaining evidence |
| --- | --- |
| Named check configuration and isolation | Candidate verified: command/config changes, separate checks, unknown input and no implicit refresh; 91 tests in the final source ZIP |
| Actual workflow adapter | Candidate verified in all four hosted matrix jobs: actual composite refresh/PASS/stale-BLOCK and negative-control assertion passed |
| Recovery | Real child-exit/PENDING regression passed; residue requires reviewed manual recovery; detached processes and hardware-failure durability are not guaranteed |
| Interface/upgrade boundary | CLI contract and separate-environment rollback documented; installed candidate/legacy examples verified. No automatic in-place migration is promised |
| Distribution and license | Owner-selected MIT verified in wheel metadata and bundled LICENSE; fixed ZIP/wheel installed and public download hashes verified |
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
