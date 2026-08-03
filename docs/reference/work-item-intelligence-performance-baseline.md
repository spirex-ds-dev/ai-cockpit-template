---
author: Ray
title: "Work Item Intelligence performance characterization baseline"
description: "Local-only WIII V2 benchmark protocol and environment-bound evidence."
status: reference
authority: supporting
---

# Work Item Intelligence performance characterization baseline

This baseline is a reproducible local observation, not a performance budget or
service-level objective. It uses temporary fixture roots and never writes the
repository `.ai/work-items/runtime` tree.

## Protocol

The benchmark runs each combination of the following profile:

- W: `1`, `100` active Work Items
- F: `1`, `1000`, `2000` fixture facts per active Work Item
- concurrency: `1`, `8`, `32`, `64` simultaneous V2 active-list readers
- mode: `cold`, `warm`
- samples: `30` per case

Each case records Python and filesystem identifiers, p50/p95/p99 query-wave
latency, timeout count, lock wait, and fixture bytes written. Cold mode creates
a new reader pool for each query wave; warm mode reuses one reader pool across
the case. Both modes query the same already-built temporary V2 projections, so
the reported read evidence is not conflated with projection rebuild cost.

## Result artifact

Run `scripts/ai_work_item_intelligence_benchmark.py --root <temporary-root>
--output <report.json>` to produce the 48-case JSON artifact. Keep a generated
report with the Work Item evidence rather than treating numbers copied from a
different machine as comparable. No enforcement threshold follows from this
document; later Work Items must compare their measured profile explicitly.

## 2026-08-03 local observation

The full 48-case protocol above completed on Python `3.14.4`, platform
`macOS-26.6-arm64-arm-64bit-Mach-O`, filesystem `Darwin:/`. All cases recorded
30 samples, zero query timeouts, and zero lock wait. The temporary fixture size
ranged from 2,753 bytes (W=1, F=1) to 45,906,169 bytes (W=100, F=2,000).

| W | F | concurrency | mode | p50 ms | p95 ms | p99 ms |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | 1 | 1 | warm | 0.132 | 0.227 | 0.339 |
| 1 | 2,000 | 64 | warm | 8.912 | 9.283 | 9.594 |
| 100 | 1 | 1 | warm | 4.191 | 4.816 | 5.001 |
| 100 | 1 | 64 | warm | 431.227 | 463.685 | 480.852 |
| 100 | 2,000 | 1 | warm | 4.034 | 4.338 | 4.588 |
| 100 | 2,000 | 64 | warm | 437.756 | 463.804 | 495.664 |

The complete generated report is retained with this Work Item's archived
evidence. The displayed rows are representative readings, not a ceiling or an
adopted budget.
