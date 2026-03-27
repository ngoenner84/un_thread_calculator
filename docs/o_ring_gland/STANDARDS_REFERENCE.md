# O-Ring Gland Standards Reference

This project uses a project-standard gland table for recommended gland depth (`L`) and squeeze ranges by cross-section.

## How the calculator uses this table

- Recommended gland depth is the midpoint of the `L` range for the selected service type and matching cross-section.
- Suggested groove width is the midpoint of the no-backup-ring (`G`) range for the selected service type and matching cross-section.
- Cross-section matching uses nominal `W` values with their stated actual tolerance (for example, `0.139 ± 0.004`).
- If a cross-section does not match a standard row, the calculator falls back to the legacy squeeze-target formula.
- Warnings are emitted when nominal depth/squeeze/width or tolerance-stack squeeze/width are outside the project-standard ranges.

## Static sealing reference (AS568B ranges)

| Nominal CS (in) | Actual tolerance (in) | L gland depth range (in) | L midpoint used (in) | Squeeze range (%) | G width range, no backup ring (in) | G midpoint used (in) |
|---|---:|---:|---:|---:|
| 0.070 | ±0.003 | 0.050 to 0.052 | 0.0510 | 22 to 32 | 0.093 to 0.098 | 0.0955 |
| 0.103 | ±0.003 | 0.081 to 0.083 | 0.0820 | 17 to 24 | 0.140 to 0.145 | 0.1425 |
| 0.139 | ±0.004 | 0.111 to 0.113 | 0.1120 | 16 to 23 | 0.187 to 0.192 | 0.1895 |
| 0.210 | ±0.005 | 0.170 to 0.173 | 0.1715 | 15 to 21 | 0.281 to 0.286 | 0.2835 |
| 0.275 | ±0.006 | 0.226 to 0.229 | 0.2275 | 15 to 20 | 0.375 to 0.380 | 0.3775 |

## Dynamic sealing reference (AS568A ranges)

| Nominal CS (in) | Actual tolerance (in) | L gland depth range (in) | L midpoint used (in) | Squeeze range (%) | G width range, no backup ring (in) | G midpoint used (in) |
|---|---:|---:|---:|---:|
| 0.070 | ±0.003 | 0.055 to 0.057 | 0.0560 | 15 to 25 | 0.093 to 0.098 | 0.0955 |
| 0.103 | ±0.003 | 0.088 to 0.090 | 0.0890 | 10 to 17 | 0.140 to 0.145 | 0.1425 |
| 0.139 | ±0.004 | 0.121 to 0.123 | 0.1220 | 9 to 16 | 0.187 to 0.192 | 0.1895 |
| 0.210 | ±0.005 | 0.185 to 0.188 | 0.1865 | 8 to 14 | 0.281 to 0.286 | 0.2835 |
| 0.275 | ±0.006 | 0.237 to 0.240 | 0.2385 | 11 to 16 | 0.375 to 0.380 | 0.3775 |
