import csv
from dataclasses import dataclass
from math import pi
from pathlib import Path


class ValidationError(ValueError):
    """Input validation error for O-ring calculations."""


IN_TO_MM = 25.4

CROSS_SECTION_FAMILIES = {
    "0xx": {"label": "0.070 in (-0XX)", "cross_section": 0.070},
    "1xx": {"label": "0.103 in (-1XX)", "cross_section": 0.103},
    "2xx": {"label": "0.139 in (-2XX)", "cross_section": 0.139},
    "3xx": {"label": "0.210 in (-3XX)", "cross_section": 0.210},
}

GLAND_STANDARDS = {
    "static": {
        0.070: {
            "cs_tol": 0.003,
            "depth_range": (0.050, 0.052),
            "squeeze_range_pct": (22.0, 32.0),
            "groove_width_no_backup_range": (0.093, 0.098),
        },
        0.103: {
            "cs_tol": 0.003,
            "depth_range": (0.081, 0.083),
            "squeeze_range_pct": (17.0, 24.0),
            "groove_width_no_backup_range": (0.140, 0.145),
        },
        0.139: {
            "cs_tol": 0.004,
            "depth_range": (0.111, 0.113),
            "squeeze_range_pct": (16.0, 23.0),
            "groove_width_no_backup_range": (0.187, 0.192),
        },
        0.210: {
            "cs_tol": 0.005,
            "depth_range": (0.170, 0.173),
            "squeeze_range_pct": (15.0, 21.0),
            "groove_width_no_backup_range": (0.281, 0.286),
        },
        0.275: {
            "cs_tol": 0.006,
            "depth_range": (0.226, 0.229),
            "squeeze_range_pct": (15.0, 20.0),
            "groove_width_no_backup_range": (0.375, 0.380),
        },
    },
    "dynamic": {
        0.070: {
            "cs_tol": 0.003,
            "depth_range": (0.055, 0.057),
            "squeeze_range_pct": (15.0, 25.0),
            "groove_width_no_backup_range": (0.093, 0.098),
        },
        0.103: {
            "cs_tol": 0.003,
            "depth_range": (0.088, 0.090),
            "squeeze_range_pct": (10.0, 17.0),
            "groove_width_no_backup_range": (0.140, 0.145),
        },
        0.139: {
            "cs_tol": 0.004,
            "depth_range": (0.121, 0.123),
            "squeeze_range_pct": (9.0, 16.0),
            "groove_width_no_backup_range": (0.187, 0.192),
        },
        0.210: {
            "cs_tol": 0.005,
            "depth_range": (0.185, 0.188),
            "squeeze_range_pct": (8.0, 14.0),
            "groove_width_no_backup_range": (0.281, 0.286),
        },
        0.275: {
            "cs_tol": 0.006,
            "depth_range": (0.237, 0.240),
            "squeeze_range_pct": (11.0, 16.0),
            "groove_width_no_backup_range": (0.375, 0.380),
        },
    },
}


@dataclass(frozen=True)
class ORingInputs:
    seal_type: str
    service_type: str
    o_ring_id: float
    o_ring_cs: float
    groove_width: float
    bore_diameter: float | None = None
    rod_diameter: float | None = None
    groove_diameter: float | None = None
    groove_width_tol: float = 0.0
    groove_diameter_tol: float = 0.0
    o_ring_cs_tol: float = 0.003
    reference_diameter_tol: float = 0.0


@dataclass(frozen=True)
class ORingResult:
    radial_gland_depth: float
    squeeze_percent: float
    stretch_percent: float
    effective_o_ring_area: float
    gland_area: float
    fill_percent: float
    squeeze_min_percent: float
    squeeze_max_percent: float
    stretch_min_percent: float
    stretch_max_percent: float
    fill_min_percent: float
    fill_max_percent: float
    target_squeeze_percent: float
    target_fill_percent: float
    recommended_gland_depth: float
    recommended_groove_width_min: float
    recommended_groove_diameter: float
    warnings: list[str]


def _pct(value: float) -> float:
    return round(value * 100.0, 2)


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValidationError(f"{name} must be > 0")


def _validate_non_negative(name: str, value: float) -> None:
    if value < 0:
        raise ValidationError(f"{name} must be >= 0")


def _as568_rows_by_family() -> dict[str, list[dict]]:
    csv_path = Path(__file__).resolve().parents[2] / "data" / "as568" / "as568_sizes.csv"
    if not csv_path.exists():
        raise ValidationError(f"AS568 data file not found: {csv_path}")

    grouped: dict[str, list[dict]] = {"0xx": [], "1xx": [], "2xx": [], "3xx": []}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            family = (row.get("family") or "").strip().lower()
            if family not in grouped:
                continue
            dash_size = (row.get("dash_size") or "").strip()
            id_actual_str = (row.get("id_actual_in") or "").strip()
            cs_actual_str = (row.get("cs_actual_in") or "").strip()
            id_tol_str = (row.get("id_tol_in") or "").strip()
            cs_tol_str = (row.get("cs_tol_in") or "").strip()

            if not dash_size or not id_actual_str or not cs_actual_str:
                continue

            try:
                id_actual = float(id_actual_str)
                cs_actual = float(cs_actual_str)
            except ValueError:
                continue

            id_tol = float(id_tol_str) if id_tol_str else None
            cs_tol = float(cs_tol_str) if cs_tol_str else None
            grouped[family].append(
                {
                    "dash_size": dash_size,
                    "id_actual_in": id_actual,
                    "id_tol_in": id_tol,
                    "cs_actual_in": cs_actual,
                    "cs_tol_in": cs_tol,
                }
            )

    for family in grouped:
        grouped[family].sort(key=lambda row: row["id_actual_in"])

    return grouped


def cross_section_for_family(family: str) -> float:
    key = family.strip().lower()
    if key not in CROSS_SECTION_FAMILIES:
        raise ValidationError("crossSectionFamily must be one of: 0xx, 1xx, 2xx, 3xx")
    return float(CROSS_SECTION_FAMILIES[key]["cross_section"])


def suggested_groove_width(o_ring_cs: float, service_type: str) -> float:
    if service_type == "dynamic":
        factor = 1.22
    elif service_type == "static":
        factor = 1.30
    else:
        raise ValidationError("service_type must be 'static' or 'dynamic'")
    return o_ring_cs * factor


def suggested_tolerances(o_ring_cs: float) -> dict:
    if o_ring_cs <= 0.103:
        dim_tol = 0.002
    elif o_ring_cs <= 0.139:
        dim_tol = 0.003
    else:
        dim_tol = 0.004

    return {
        "groove_width_tol": dim_tol,
        "groove_diameter_tol": dim_tol,
        "o_ring_cs_tol": 0.003,
        "reference_diameter_tol": dim_tol,
    }


def _recommended_targets(service_type: str) -> tuple[float, float]:
    if service_type == "dynamic":
        return 12.0, 75.0
    if service_type == "static":
        return 20.0, 85.0
    raise ValidationError("service_type must be 'static' or 'dynamic'")


def _gland_standard_band(service_type: str, o_ring_cs: float) -> dict | None:
    standards = GLAND_STANDARDS.get(service_type)
    if standards is None:
        raise ValidationError("service_type must be 'static' or 'dynamic'")

    for nominal_cs, row in standards.items():
        if abs(o_ring_cs - nominal_cs) <= float(row["cs_tol"]):
            return {
                "nominal_cs": nominal_cs,
                "cs_tol": float(row["cs_tol"]),
                "depth_range": tuple(row["depth_range"]),
                "squeeze_range_pct": tuple(row["squeeze_range_pct"]),
                "groove_width_no_backup_range": tuple(row["groove_width_no_backup_range"]),
            }
    return None


def _recommended_gland_depth(service_type: str, o_ring_cs: float, target_squeeze: float) -> float:
    band = _gland_standard_band(service_type, o_ring_cs)
    if band is not None:
        depth_min, depth_max = band["depth_range"]
        return (depth_min + depth_max) / 2.0
    return o_ring_cs * (1.0 - target_squeeze / 100.0)


def _recommended_starting_point(service_type: str, o_ring_cs: float) -> tuple[float, float, float]:
    target_squeeze, target_fill = _recommended_targets(service_type)
    rec_depth = _recommended_gland_depth(service_type, o_ring_cs, target_squeeze)

    # Keep displayed squeeze target consistent with the selected recommended depth.
    implied_squeeze = ((o_ring_cs - rec_depth) / o_ring_cs) * 100.0
    return implied_squeeze, target_fill, rec_depth


def _recommended_groove_width_no_backup(service_type: str, o_ring_cs: float) -> float:
    band = _gland_standard_band(service_type, o_ring_cs)
    if band is not None:
        width_min, width_max = band["groove_width_no_backup_range"]
        return (width_min + width_max) / 2.0
    return suggested_groove_width(o_ring_cs, service_type)


def recommend_groove_geometry(
    *,
    seal_type: str,
    service_type: str,
    reference_diameter: float,
    o_ring_cs: float,
) -> dict:
    _validate_positive("reference_diameter", reference_diameter)
    _validate_positive("o_ring_cs", o_ring_cs)

    target_squeeze, target_fill, rec_depth = _recommended_starting_point(service_type, o_ring_cs)

    if seal_type == "piston":
        rec_groove_diameter = reference_diameter - 2.0 * rec_depth
    elif seal_type == "rod":
        rec_groove_diameter = reference_diameter + 2.0 * rec_depth
    else:
        raise ValidationError("seal_type must be 'piston' or 'rod'")

    return {
        "target_squeeze_percent": target_squeeze,
        "target_fill_percent": target_fill,
        "recommended_gland_depth": rec_depth,
        "recommended_groove_diameter": rec_groove_diameter,
        "suggested_groove_width": _recommended_groove_width_no_backup(service_type, o_ring_cs),
    }


def suggest_standard_sizes(
    *,
    seal_type: str,
    service_type: str,
    reference_diameter: float,
    cross_section_family: str,
) -> dict:
    family_key = cross_section_family.strip().lower()
    o_ring_cs = cross_section_for_family(family_key)

    rows_by_family = _as568_rows_by_family()
    rows = rows_by_family.get(family_key, [])
    if not rows:
        raise ValidationError(f"No AS568 rows available for family '{family_key}'")

    geometry = recommend_groove_geometry(
        seal_type=seal_type,
        service_type=service_type,
        reference_diameter=reference_diameter,
        o_ring_cs=o_ring_cs,
    )
    rec_groove_dia = geometry["recommended_groove_diameter"]
    stretch_basis = rec_groove_dia if seal_type == "piston" else reference_diameter

    candidates: list[dict] = []
    for row in rows:
        nominal_id = row["id_actual_in"]
        stretch_pct = ((stretch_basis - nominal_id) / nominal_id) * 100.0
        candidates.append(
            {
                "dash_size": row["dash_size"],
                "nominal_id": round(nominal_id, 3),
                "cross_section": round(row["cs_actual_in"], 3),
                "predicted_stretch_percent": round(stretch_pct, 2),
                "id_delta_to_recommended": round(nominal_id - stretch_basis, 5),
            }
        )

    best_idx = min(
        range(len(candidates)),
        key=lambda i: abs(candidates[i]["id_delta_to_recommended"]),
    )
    window_indices = sorted({max(0, best_idx - 1), best_idx, min(len(candidates) - 1, best_idx + 1)})
    suggestions = [candidates[i] for i in window_indices]

    return {
        "cross_section_family": family_key,
        "cross_section": round(o_ring_cs, 3),
        "reference_diameter": round(reference_diameter, 5),
        "recommended_geometry": {
            "target_squeeze_percent": geometry["target_squeeze_percent"],
            "target_fill_percent": geometry["target_fill_percent"],
            "recommended_gland_depth": round(geometry["recommended_gland_depth"], 5),
            "recommended_groove_diameter": round(geometry["recommended_groove_diameter"], 5),
            "suggested_groove_width": round(geometry["suggested_groove_width"], 5),
        },
        "suggested_tolerances": {
            k: round(v, 5) for k, v in suggested_tolerances(o_ring_cs).items()
        },
        "suggestions": suggestions,
    }


def _radial_depth(
    inputs: ORingInputs,
    groove_diameter: float | None = None,
    reference_diameter: float | None = None,
) -> float:
    gd = inputs.groove_diameter if groove_diameter is None else groove_diameter
    if gd is None:
        raise ValidationError("groove_diameter is required")

    if inputs.seal_type == "piston":
        bd = inputs.bore_diameter if reference_diameter is None else reference_diameter
        if bd is None:
            raise ValidationError("Piston seal requires bore_diameter")
        return (bd - gd) / 2.0

    if inputs.seal_type == "rod":
        rd = inputs.rod_diameter if reference_diameter is None else reference_diameter
        if rd is None:
            raise ValidationError("Rod seal requires rod_diameter")
        return (gd - rd) / 2.0

    raise ValidationError("seal_type must be 'piston' or 'rod'")


def _stretch_percent(o_ring_id: float, groove_diameter: float) -> float:
    stretch = (groove_diameter - o_ring_id) / o_ring_id
    return _pct(stretch)


def _stretch_basis_diameter(
    inputs: ORingInputs,
    *,
    groove_diameter: float | None = None,
    reference_diameter: float | None = None,
) -> float:
    if inputs.seal_type == "piston":
        gd = inputs.groove_diameter if groove_diameter is None else groove_diameter
        if gd is None:
            raise ValidationError("groove_diameter is required for piston stretch calculation")
        return gd

    if inputs.seal_type == "rod":
        rd = inputs.rod_diameter if reference_diameter is None else reference_diameter
        if rd is None:
            raise ValidationError("rod_diameter is required for rod stretch calculation")
        return rd

    raise ValidationError("seal_type must be 'piston' or 'rod'")


def _warnings(
    seal_type: str,
    service_type: str,
    o_ring_cs: float,
    radial_depth: float,
    groove_width: float,
    groove_width_min: float,
    groove_width_max: float,
    squeeze_percent: float,
    stretch_percent: float,
    fill_percent: float,
    squeeze_min: float,
    squeeze_max: float,
    fill_max: float,
) -> list[str]:
    notes: list[str] = []
    standard_band = _gland_standard_band(service_type, o_ring_cs)

    if standard_band is not None:
        std_sq_min, std_sq_max = standard_band["squeeze_range_pct"]
        std_depth_min, std_depth_max = standard_band["depth_range"]
        std_width_min, std_width_max = standard_band["groove_width_no_backup_range"]
        nominal_cs = standard_band["nominal_cs"]

        if not (std_depth_min <= radial_depth <= std_depth_max):
            notes.append(
                f"Nominal gland depth is outside the project standard L range ({std_depth_min:.3f}-{std_depth_max:.3f} in) for CS {nominal_cs:.3f} in."
            )
        if not (std_sq_min <= squeeze_percent <= std_sq_max):
            notes.append(
                f"Nominal squeeze is outside the project standard range ({std_sq_min:.0f}-{std_sq_max:.0f}%) for CS {nominal_cs:.3f} in."
            )
        if squeeze_min < std_sq_min or squeeze_max > std_sq_max:
            notes.append(
                f"Tolerance stack drives squeeze outside the project standard range ({std_sq_min:.0f}-{std_sq_max:.0f}%) for CS {nominal_cs:.3f} in."
            )
        if not (std_width_min <= groove_width <= std_width_max):
            notes.append(
                f"Nominal groove width is outside the project no-backup-ring range ({std_width_min:.3f}-{std_width_max:.3f} in) for CS {nominal_cs:.3f} in."
            )
        if groove_width_min < std_width_min or groove_width_max > std_width_max:
            notes.append(
                f"Tolerance stack drives groove width outside the project no-backup-ring range ({std_width_min:.3f}-{std_width_max:.3f} in) for CS {nominal_cs:.3f} in."
            )
    else:
        if service_type == "dynamic":
            if not (8.0 <= squeeze_percent <= 16.0):
                notes.append("Dynamic nominal squeeze is outside the common 8-16% starting range.")
            if squeeze_min < 8.0 or squeeze_max > 16.0:
                notes.append("Tolerance stack drives dynamic squeeze outside 8-16%.")
        else:
            if not (10.0 <= squeeze_percent <= 30.0):
                notes.append("Static nominal squeeze is outside the common 10-30% starting range.")
            if squeeze_min < 10.0 or squeeze_max > 30.0:
                notes.append("Tolerance stack drives static squeeze outside 10-30%.")

    if service_type == "dynamic":
        if fill_percent > 75.0:
            notes.append("Dynamic nominal gland fill is above the common 75% starting limit.")
        if fill_max > 75.0:
            notes.append("Tolerance stack drives dynamic gland fill above 75%.")
    else:
        if fill_percent > 85.0:
            notes.append("Static nominal gland fill is above the common 85% starting limit.")
        if fill_max > 85.0:
            notes.append("Tolerance stack drives static gland fill above 85%.")

    if service_type == "dynamic" and stretch_percent > 5.0:
        if standard_band is not None:
            notes.append("O-ring stretch is above the project standard dynamic limit (5%).")
        else:
            notes.append("O-ring stretch is above the common 5% dynamic starting limit.")
    if service_type == "static" and stretch_percent > 8.0:
        if standard_band is not None:
            notes.append("O-ring stretch is above the project standard static limit (8%).")
        else:
            notes.append("O-ring stretch is above the common 8% static starting limit.")

    if stretch_percent < 0:
        if seal_type == "piston":
            notes.append("Negative stretch indicates O-ring interference; verify assembly method.")
        else:
            notes.append("Negative stretch indicates O-ring compression on installation; verify fit.")

    if squeeze_percent <= 0:
        notes.append("Computed squeeze is <= 0%; seal is unlikely to function.")

    return notes


def _compute_range_metrics(inputs: ORingInputs) -> dict:
    cs_values = [inputs.o_ring_cs - inputs.o_ring_cs_tol, inputs.o_ring_cs + inputs.o_ring_cs_tol]
    gw_values = [inputs.groove_width - inputs.groove_width_tol, inputs.groove_width + inputs.groove_width_tol]
    gd_values = [
        (inputs.groove_diameter or 0) - inputs.groove_diameter_tol,
        (inputs.groove_diameter or 0) + inputs.groove_diameter_tol,
    ]

    if inputs.seal_type == "piston":
        if inputs.bore_diameter is None:
            raise ValidationError("bore_diameter is required for piston seals")
        ref_values = [
            inputs.bore_diameter - inputs.reference_diameter_tol,
            inputs.bore_diameter + inputs.reference_diameter_tol,
        ]
    else:
        if inputs.rod_diameter is None:
            raise ValidationError("rod_diameter is required for rod seals")
        ref_values = [
            inputs.rod_diameter - inputs.reference_diameter_tol,
            inputs.rod_diameter + inputs.reference_diameter_tol,
        ]

    if min(cs_values) <= 0:
        raise ValidationError("O-ring cross-section tolerance too large for selected cross-section")
    if min(gw_values) <= 0:
        raise ValidationError("Groove width tolerance too large for selected width")
    if min(gd_values) <= 0:
        raise ValidationError("Groove diameter tolerance too large for selected diameter")
    if min(ref_values) <= 0:
        raise ValidationError("Reference diameter tolerance too large for selected bore/shaft")

    squeeze_vals: list[float] = []
    stretch_vals: list[float] = []
    fill_vals: list[float] = []

    for cs in cs_values:
        for gw in gw_values:
            for gd in gd_values:
                for ref in ref_values:
                    depth = _radial_depth(inputs, groove_diameter=gd, reference_diameter=ref)
                    if depth <= 0:
                        continue

                    squeeze = ((cs - depth) / cs) * 100.0
                    stretch_dia = _stretch_basis_diameter(
                        inputs,
                        groove_diameter=gd,
                        reference_diameter=ref,
                    )
                    stretch = ((stretch_dia - inputs.o_ring_id) / inputs.o_ring_id) * 100.0
                    stretch_ratio = 1.0 + (stretch / 100.0)
                    if stretch_ratio <= 0:
                        continue

                    effective_area = (pi * (cs / 2.0) ** 2) / stretch_ratio
                    fill = (effective_area / (depth * gw)) * 100.0

                    squeeze_vals.append(squeeze)
                    stretch_vals.append(stretch)
                    fill_vals.append(fill)

    if not squeeze_vals or not stretch_vals or not fill_vals:
        raise ValidationError("Unable to compute tolerance range metrics with provided inputs")

    return {
        "squeeze_min_percent": round(min(squeeze_vals), 2),
        "squeeze_max_percent": round(max(squeeze_vals), 2),
        "stretch_min_percent": round(min(stretch_vals), 2),
        "stretch_max_percent": round(max(stretch_vals), 2),
        "fill_min_percent": round(min(fill_vals), 2),
        "fill_max_percent": round(max(fill_vals), 2),
    }


def calculate_o_ring_gland(inputs: ORingInputs) -> ORingResult:
    _validate_positive("o_ring_id", inputs.o_ring_id)
    _validate_positive("o_ring_cs", inputs.o_ring_cs)
    _validate_positive("groove_width", inputs.groove_width)
    if inputs.groove_diameter is None:
        raise ValidationError("groove_diameter is required")
    _validate_positive("groove_diameter", inputs.groove_diameter)

    if inputs.bore_diameter is not None:
        _validate_positive("bore_diameter", inputs.bore_diameter)
    if inputs.rod_diameter is not None:
        _validate_positive("rod_diameter", inputs.rod_diameter)

    _validate_non_negative("groove_width_tol", inputs.groove_width_tol)
    _validate_non_negative("groove_diameter_tol", inputs.groove_diameter_tol)
    _validate_non_negative("o_ring_cs_tol", inputs.o_ring_cs_tol)
    _validate_non_negative("reference_diameter_tol", inputs.reference_diameter_tol)

    radial_depth = _radial_depth(inputs)
    if radial_depth <= 0:
        raise ValidationError("Computed radial gland depth must be > 0")

    squeeze_ratio = (inputs.o_ring_cs - radial_depth) / inputs.o_ring_cs
    squeeze_percent = _pct(squeeze_ratio)
    stretch_basis = _stretch_basis_diameter(inputs)
    stretch_percent = _stretch_percent(inputs.o_ring_id, stretch_basis)

    o_ring_area = pi * (inputs.o_ring_cs / 2.0) ** 2
    stretch_ratio = 1.0 + (stretch_percent / 100.0)
    if stretch_ratio <= 0:
        raise ValidationError("Stretch ratio must stay > 0")

    effective_o_ring_area = o_ring_area / stretch_ratio
    gland_area = radial_depth * inputs.groove_width
    fill_percent = _pct(effective_o_ring_area / gland_area)

    target_squeeze, target_fill, rec_depth = _recommended_starting_point(inputs.service_type, inputs.o_ring_cs)
    rec_width_min = effective_o_ring_area / (rec_depth * (target_fill / 100.0))

    if inputs.seal_type == "piston":
        if inputs.bore_diameter is None:
            raise ValidationError("bore_diameter is required for piston seals")
        rec_groove_diameter = inputs.bore_diameter - 2.0 * rec_depth
    else:
        if inputs.rod_diameter is None:
            raise ValidationError("rod_diameter is required for rod seals")
        rec_groove_diameter = inputs.rod_diameter + 2.0 * rec_depth

    range_metrics = _compute_range_metrics(inputs)

    notes = _warnings(
        seal_type=inputs.seal_type,
        service_type=inputs.service_type,
        o_ring_cs=inputs.o_ring_cs,
        radial_depth=radial_depth,
        groove_width=inputs.groove_width,
        groove_width_min=inputs.groove_width - inputs.groove_width_tol,
        groove_width_max=inputs.groove_width + inputs.groove_width_tol,
        squeeze_percent=squeeze_percent,
        stretch_percent=stretch_percent,
        fill_percent=fill_percent,
        squeeze_min=range_metrics["squeeze_min_percent"],
        squeeze_max=range_metrics["squeeze_max_percent"],
        fill_max=range_metrics["fill_max_percent"],
    )

    return ORingResult(
        radial_gland_depth=round(radial_depth, 5),
        squeeze_percent=round(squeeze_percent, 2),
        stretch_percent=round(stretch_percent, 2),
        effective_o_ring_area=round(effective_o_ring_area, 6),
        gland_area=round(gland_area, 6),
        fill_percent=round(fill_percent, 2),
        squeeze_min_percent=range_metrics["squeeze_min_percent"],
        squeeze_max_percent=range_metrics["squeeze_max_percent"],
        stretch_min_percent=range_metrics["stretch_min_percent"],
        stretch_max_percent=range_metrics["stretch_max_percent"],
        fill_min_percent=range_metrics["fill_min_percent"],
        fill_max_percent=range_metrics["fill_max_percent"],
        target_squeeze_percent=target_squeeze,
        target_fill_percent=target_fill,
        recommended_gland_depth=round(rec_depth, 5),
        recommended_groove_width_min=round(rec_width_min, 5),
        recommended_groove_diameter=round(rec_groove_diameter, 5),
        warnings=notes,
    )
