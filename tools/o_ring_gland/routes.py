from dataclasses import asdict
import base64
from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template, request

from .calculations import (
    CROSS_SECTION_FAMILIES,
    IN_TO_MM,
    ORingInputs,
    ValidationError,
    calculate_o_ring_gland,
    cross_section_for_family,
    suggest_standard_sizes,
)

bp = Blueprint(
    "o_ring_gland",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/tool-static/o_ring_gland",
)


@bp.route("/tools/o-ring-gland-calculator")
def page():
    return render_template("o_ring_gland/index.html")


@bp.route("/api/tools/o-ring-gland-calculator/cross-sections")
def cross_sections():
    payload = {}
    for key, value in CROSS_SECTION_FAMILIES.items():
        cs_in = float(value["cross_section"])
        payload[key] = {
            "label": value["label"],
            "cross_section_in": round(cs_in, 3),
            "cross_section_mm": round(cs_in * IN_TO_MM, 3),
        }
    return jsonify(payload)


@bp.route("/api/tools/o-ring-gland-calculator/suggest-sizes", methods=["POST"])
def suggest_sizes():
    try:
        payload = request.get_json(force=True) or {}
        unit = _unit(payload)
        seal_type = str(payload.get("sealType", "")).strip().lower()
        service_type = str(payload.get("serviceType", "")).strip().lower()
        cross_section_family = str(payload.get("crossSectionFamily", "")).strip().lower()

        if seal_type == "piston":
            reference_diameter_in = _to_in(float(payload.get("boreDiameter")), unit)
        elif seal_type == "rod":
            reference_diameter_in = _to_in(float(payload.get("rodDiameter")), unit)
        else:
            raise ValidationError("sealType must be 'piston' or 'rod'")

        result = suggest_standard_sizes(
            seal_type=seal_type,
            service_type=service_type,
            reference_diameter=reference_diameter_in,
            cross_section_family=cross_section_family,
        )

        converted = _convert_suggest_result(result, unit)
        return jsonify({"success": True, "result": converted})
    except (ValidationError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/api/tools/o-ring-gland-calculator/calculate", methods=["POST"])
def calculate():
    try:
        payload = request.get_json(force=True) or {}
        unit = _unit(payload)

        o_ring_cs = payload.get("oRingCs")
        if o_ring_cs in (None, ""):
            o_ring_cs = _from_in(cross_section_for_family(str(payload.get("crossSectionFamily", ""))), unit)

        inputs = ORingInputs(
            seal_type=str(payload.get("sealType", "")).strip().lower(),
            service_type=str(payload.get("serviceType", "")).strip().lower(),
            o_ring_id=_to_in(float(payload.get("oRingId")), unit),
            o_ring_cs=_to_in(float(o_ring_cs), unit),
            groove_width=_to_in(float(payload.get("grooveWidth")), unit),
            bore_diameter=_to_in(_float_or_none(payload.get("boreDiameter")), unit),
            rod_diameter=_to_in(_float_or_none(payload.get("rodDiameter")), unit),
            groove_diameter=_to_in(float(payload.get("grooveDiameter")), unit),
            groove_width_tol=_to_in(float(payload.get("grooveWidthTol", 0.0)), unit),
            groove_diameter_tol=_to_in(float(payload.get("grooveDiameterTol", 0.0)), unit),
            o_ring_cs_tol=_to_in(float(payload.get("oRingCsTol", 0.003)), unit),
            reference_diameter_tol=_to_in(float(payload.get("referenceDiameterTol", 0.0)), unit),
        )
        result = calculate_o_ring_gland(inputs)
        converted = _convert_calculation_result(asdict(result), unit)
        return jsonify({"success": True, "result": converted})
    except (ValidationError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/api/tools/o-ring-gland-calculator/report", methods=["POST"])
def report():
    try:
        report_meta = {
            "report_id": (request.form.get("reportId") or "").strip(),
            "analyst": (request.form.get("analyst") or "").strip(),
            "report_date": (request.form.get("reportDate") or "").strip(),
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
        }

        context = {
            "meta": report_meta,
            "inputs": _json_field("inputsJson"),
            "results": _json_field("resultsJson"),
            "suggestions": _json_field("suggestionsJson"),
            "unit": (request.form.get("unit") or "in").strip(),
            "image_data_url": _image_to_data_url(request.files.get("reportImage")),
        }

        return render_template("o_ring_gland/report.html", **context)
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Failed to generate report: {exc}"}), 400


def _float_or_none(value):
    if value in (None, ""):
        return None
    return float(value)


def _unit(payload) -> str:
    unit = str(payload.get("unit", "in")).strip().lower()
    if unit not in {"in", "mm"}:
        raise ValidationError("unit must be 'in' or 'mm'")
    return unit


def _to_in(value, unit: str):
    if value is None:
        return None
    return value / IN_TO_MM if unit == "mm" else value


def _from_in(value: float, unit: str) -> float:
    return value * IN_TO_MM if unit == "mm" else value


def _round_dim(value: float, unit: str, *, groove_dia: bool = False) -> float:
    if unit == "in":
        return round(value, 3)
    return round(value, 2)


def _convert_suggest_result(result: dict, unit: str) -> dict:
    converted = {
        "cross_section_family": result["cross_section_family"],
        "cross_section": _round_dim(_from_in(result["cross_section"], unit), unit),
        "reference_diameter": _round_dim(_from_in(result["reference_diameter"], unit), unit),
        "recommended_geometry": {
            "target_squeeze_percent": result["recommended_geometry"]["target_squeeze_percent"],
            "target_fill_percent": result["recommended_geometry"]["target_fill_percent"],
            "recommended_gland_depth": _round_dim(_from_in(result["recommended_geometry"]["recommended_gland_depth"], unit), unit),
            "recommended_groove_diameter": _round_dim(_from_in(result["recommended_geometry"]["recommended_groove_diameter"], unit), unit, groove_dia=True),
            "suggested_groove_width": _round_dim(_from_in(result["recommended_geometry"]["suggested_groove_width"], unit), unit),
        },
        "suggested_tolerances": {
            "groove_width_tol": _round_dim(_from_in(result["suggested_tolerances"]["groove_width_tol"], unit), unit),
            "groove_diameter_tol": _round_dim(_from_in(result["suggested_tolerances"]["groove_diameter_tol"], unit), unit),
            "o_ring_cs_tol": _round_dim(_from_in(result["suggested_tolerances"]["o_ring_cs_tol"], unit), unit),
            "reference_diameter_tol": _round_dim(_from_in(result["suggested_tolerances"]["reference_diameter_tol"], unit), unit),
        },
        "suggestions": [],
    }

    for item in result["suggestions"]:
        converted["suggestions"].append(
            {
                "dash_size": item["dash_size"],
                "nominal_id": _round_dim(_from_in(item["nominal_id"], unit), unit),
                "cross_section": _round_dim(_from_in(item["cross_section"], unit), unit),
                "predicted_stretch_percent": item["predicted_stretch_percent"],
                "id_delta_to_recommended": _round_dim(_from_in(item["id_delta_to_recommended"], unit), unit),
            }
        )

    return converted


def _json_field(name: str):
    import json

    raw = request.form.get(name, "").strip()
    if not raw:
        return {}
    return json.loads(raw)


def _image_to_data_url(file_storage):
    if file_storage is None or not file_storage.filename:
        return None

    content = file_storage.read()
    if not content:
        return None

    mimetype = file_storage.mimetype or "image/png"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mimetype};base64,{encoded}"


def _convert_calculation_result(result: dict, unit: str) -> dict:
    dim_keys = {
        "radial_gland_depth",
        "recommended_gland_depth",
        "recommended_groove_width_min",
        "recommended_groove_diameter",
    }

    converted = {}
    for key, value in result.items():
        if key in dim_keys:
            converted[key] = _round_dim(_from_in(float(value), unit), unit, groove_dia=(key == "recommended_groove_diameter"))
        else:
            converted[key] = value

    return converted
