# AS568 Reference Data

This folder stores maintainable AS568 size reference data for the O-ring calculator.

## Files
- `data/as568/as568_sizes.csv`: human-editable tabular source.
- `data/as568/as568_sizes.json`: machine-readable mirror used by tooling.
- `docs/as568/as568_reference_raw.txt`: raw pasted reference text for audit traceability.

## CSV Columns
- `dash_size`: AS568 dash number (example: `-234`).
- `family`: Cross-section family (`0xx`, `1xx`, `2xx`, `3xx`).
- `id_actual_in`: actual ID in inches.
- `id_tol_in`: ID tolerance in inches (half-range, ±).
- `cs_actual_in`: cross-section width in inches.
- `cs_tol_in`: cross-section tolerance in inches (half-range, ±).
- `nominal_id_in`: nominal ID in inches when provided.
- `nominal_od_in`: nominal OD in inches when provided.
- `nominal_width_in`: nominal width in inches when provided.
- `source`: where this row came from (`seed` or reference source tag).
- `reviewed`: `true/false` flag for engineering review.

## Notes
- Current dataset is seeded from the calculator's existing nominal series and family widths.
- Use the raw text file and source standard to replace/update values.
- The O-ring calculator suggestion engine reads `data/as568/as568_sizes.csv` directly.
