from __future__ import annotations

from dataclasses import dataclass
from math import cos, hypot, isfinite, radians, sin
from pathlib import Path
import re
import runpy
import tempfile
from typing import Any


TEMPLATE_FILENAME = "trimline_generator_template.py"


DEFAULT_PARAMETERS: dict[str, float] = {
    # Main profile
    "A": 10.0,
    "B": 29.0,
    "C": 96.0,
    "D": 96.0,
    "E": 189.0,
    "G": 25.0,
    "H": 10.0,
    "HEM_GAP_AB": 1.0,
    "GUTTER_LENGTH": 300.0,

    # Roof and section geometry
    "ROOF_PITCH": 5.0,
    "GUTTER_ARM_DEPTH": 35.482907044268764,
    "ANGLE_CD": 160.0,
    "ANGLE_DE": 100.0,
    "ANGLE_EF": 90.0,

    # Small / male end
    "A_SMALL_EXTRA": 5.0,
    "B_SMALL_REDUCTION": 2.0,
    "C_SMALL_REDUCTION": 1.0,
    "D_SMALL_REDUCTION": 1.0,
    "E_SMALL_REDUCTION": 2.0,
    "F_SMALL_REDUCTION": 2.0,
    "G_SMALL_REDUCTION": 2.0,

    # Joint and machining
    "OVERLAP": 50.0,
    "WHEEL_FORM_FROM_RIGHT": 55.0,
    "LEFT_END_RELIEF": 55.0,
    "NOTCH_LENGTH": 55.0,
    "HOLE_DIAMETER": 5.0,
    "HOLE_X_FROM_LEFT": 25.0,
    "HOLE_DISTANCE_FROM_FOLD": 17.0,
    "MAX_HOLE_SPACING": 75.0,

    # Stop end
    "STOP_END_LAP": 50.0,
    "STOP_C_REDUCTION": 1.0,
    "STOP_D_REDUCTION": 1.0,
    "STOP_E_REDUCTION": 2.0,
    "STOP_F_REDUCTION": 1.0,
    "STOP_CD_CUT_ANGLE": 44.0,
    "STOP_CD_MIN_CUT_ANGLE": 30.0,
    "STOP_END_GAP_FROM_FLAT": 250.0,

    # Drawing layout
    "SECTION_GAP_FROM_FLAT": 200.0,
}


@dataclass(frozen=True)
class CalculationResult:
    f: float
    angle_bc: float
    angle_fg: float
    girth: float
    small_end: dict[str, float]
    front_chain: list[tuple[float, float]]
    rear_chain: list[tuple[float, float]]
    gutter_arm_line: tuple[tuple[float, float], tuple[float, float]]


def _point_from(
    point: tuple[float, float],
    length: float,
    angle_degrees: float,
) -> tuple[float, float]:
    angle = radians(angle_degrees)
    return (
        point[0] + length * cos(angle),
        point[1] + length * sin(angle),
    )


def _unit_from_angle(angle_degrees: float) -> tuple[float, float]:
    angle = radians(angle_degrees)
    return cos(angle), sin(angle)


def _dot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _normalise_parameters(values: dict[str, Any]) -> dict[str, float]:
    result = DEFAULT_PARAMETERS.copy()

    for name, value in values.items():
        if name not in result:
            continue

        number = float(value)

        if not isfinite(number):
            raise ValueError(f"{name} must be a finite number.")

        result[name] = number

    return result


def calculate_profile(values: dict[str, Any]) -> CalculationResult:
    p = _normalise_parameters(values)

    for name in ("A", "B", "C", "D", "E", "G", "H"):
        if p[name] <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if p["HEM_GAP_AB"] < 0:
        raise ValueError("Hem gap A/B cannot be negative.")

    if not -45.0 < p["ROOF_PITCH"] < 45.0:
        raise ValueError("Roof pitch must be between -45° and +45°.")

    if p["GUTTER_ARM_DEPTH"] <= 0:
        raise ValueError("Gutter arm depth must be greater than zero.")

    direction_c = p["ANGLE_DE"] - (180.0 - p["ANGLE_CD"])
    direction_b = p["ROOF_PITCH"]
    direction_g = p["ROOF_PITCH"] + 180.0

    angle_bc = 180.0 - (direction_c - direction_b)
    angle_fg = direction_g - p["ANGLE_EF"]

    if not 0.0 < angle_bc < 180.0:
        raise ValueError(
            "The calculated BC angle is outside the valid 0–180° range."
        )

    if not 0.0 < angle_fg < 180.0:
        raise ValueError(
            "The calculated FG angle is outside the valid 0–180° range."
        )

    p_de = (0.0, 0.0)
    p_cd = _point_from(p_de, p["D"], p["ANGLE_DE"])
    p_bc = _point_from(p_cd, p["C"], direction_c)
    p_ef = _point_from(p_de, p["E"], 0.0)

    b_unit = _unit_from_angle(direction_b)
    f_unit = _unit_from_angle(p["ANGLE_EF"])
    normal_to_g = (b_unit[1], -b_unit[0])

    base_vector = (p_ef[0] - p_bc[0], p_ef[1] - p_bc[1])
    base_signed_distance = _dot(base_vector, normal_to_g)
    f_normal_component = _dot(f_unit, normal_to_g)

    if abs(f_normal_component) < 1e-9:
        raise ValueError(
            "Changing F cannot alter gutter arm depth with the selected angles."
        )

    f = (
        p["GUTTER_ARM_DEPTH"] - base_signed_distance
    ) / f_normal_component

    if f <= 0:
        raise ValueError(
            "The selected gutter arm depth produces a zero or negative F."
        )

    girth = (
        p["A"] + p["B"] + p["C"] + p["D"]
        + p["E"] + f + p["G"] + p["H"]
    )

    small_end = {
        "A1": p["A"] + p["A_SMALL_EXTRA"],
        "B1": p["B"] - p["B_SMALL_REDUCTION"],
        "C1": p["C"] - p["C_SMALL_REDUCTION"],
        "D1": p["D"] - p["D_SMALL_REDUCTION"],
        "E1": p["E"] - p["E_SMALL_REDUCTION"],
        "F1": f - p["F_SMALL_REDUCTION"],
        "G1": p["G"] - p["G_SMALL_REDUCTION"],
    }
    small_end["H1"] = girth - sum(small_end.values())

    if any(value <= 0 for value in small_end.values()):
        raise ValueError(
            "The derived small-end dimensions are invalid. "
            "Review the small-end adjustments."
        )

    if p["GUTTER_LENGTH"] <= p["WHEEL_FORM_FROM_RIGHT"]:
        raise ValueError(
            "Gutter length must exceed the wheel-form distance from the right."
        )

    if p["LEFT_END_RELIEF"] + p["NOTCH_LENGTH"] >= p["GUTTER_LENGTH"]:
        raise ValueError(
            "Left-end relief plus notch length must be smaller than "
            "the gutter length."
        )

    if p["STOP_CD_MIN_CUT_ANGLE"] < 30.0:
        raise ValueError(
            "The minimum C/D cut angle cannot be below 30°."
        )

    p_b_free = _point_from(p_bc, p["B"], direction_b)
    p_a_at_fold = _point_from(
        p_b_free,
        p["HEM_GAP_AB"],
        direction_b - 90.0,
    )
    p_a_free = _point_from(
        p_a_at_fold,
        p["A"],
        direction_b + 180.0,
    )

    p_fg = _point_from(p_ef, f, p["ANGLE_EF"])
    p_gh = _point_from(p_fg, p["G"], direction_g)
    p_h_free = _point_from(p_gh, p["H"], -90.0)

    fg_from_bc = (p_fg[0] - p_bc[0], p_fg[1] - p_bc[1])
    along_b = _dot(fg_from_bc, b_unit)
    p_on_b = (
        p_bc[0] + along_b * b_unit[0],
        p_bc[1] + along_b * b_unit[1],
    )

    measured_depth = hypot(
        p_on_b[0] - p_fg[0],
        p_on_b[1] - p_fg[1],
    )

    if abs(measured_depth - p["GUTTER_ARM_DEPTH"]) > 1e-7:
        raise ValueError(
            "Internal calculation error: gutter arm depth was not achieved."
        )

    front_chain = [
        p_a_free,
        p_a_at_fold,
        p_b_free,
        p_bc,
        p_cd,
        p_de,
    ]
    rear_chain = [
        p_de,
        p_ef,
        p_fg,
        p_gh,
        p_h_free,
    ]

    return CalculationResult(
        f=f,
        angle_bc=angle_bc,
        angle_fg=angle_fg,
        girth=girth,
        small_end=small_end,
        front_chain=front_chain,
        rear_chain=rear_chain,
        gutter_arm_line=(p_fg, p_on_b),
    )


def _replace_assignment(
    source: str,
    name: str,
    value: float | str,
) -> str:
    pattern = re.compile(
        rf"(?m)^{re.escape(name)}\s*=\s*.*$"
    )

    replacement_value = repr(value)
    replacement = f"{name} = {replacement_value}"

    updated, count = pattern.subn(replacement, source, count=1)

    if count != 1:
        raise RuntimeError(
            f"Could not update parameter {name} in the DXF template."
        )

    return updated


def _safe_output_filename(file_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", file_name.strip())
    cleaned = cleaned.strip("._")

    if not cleaned:
        cleaned = "parametric_gutter"

    if not cleaned.lower().endswith(".dxf"):
        cleaned += ".dxf"

    return cleaned


def generate_dxf(
    values: dict[str, Any],
    output_filename: str = "parametric_gutter.dxf",
) -> tuple[bytes, CalculationResult, str]:
    parameters = _normalise_parameters(values)
    calculated = calculate_profile(parameters)
    safe_filename = _safe_output_filename(output_filename)

    template_path = Path(__file__).resolve().with_name(TEMPLATE_FILENAME)

    if not template_path.exists():
        raise FileNotFoundError(
            f"DXF template not found: {template_path.name}"
        )

    source = template_path.read_text(encoding="utf-8")

    for name, value in parameters.items():
        source = _replace_assignment(source, name, float(value))

    source = _replace_assignment(
        source,
        "OUTPUT_FILENAME",
        safe_filename,
    )

    with tempfile.TemporaryDirectory(prefix="trimline_dxf_") as temp_folder:
        run_script = Path(temp_folder) / "generate_dxf.py"
        output_path = Path(temp_folder) / safe_filename

        run_script.write_text(source, encoding="utf-8")
        runpy.run_path(str(run_script), run_name="__main__")

        if not output_path.exists():
            raise RuntimeError(
                "The generator completed without creating the DXF."
            )

        return output_path.read_bytes(), calculated, safe_filename
