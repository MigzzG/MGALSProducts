from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from trimline_engine import (
    DEFAULT_PARAMETERS,
    CalculationResult,
    calculate_profile,
    generate_dxf,
)


st.set_page_config(
    page_title="Parametric Gutter DXF Generator",
    layout="wide",
)

st.title("Parametric Gutter DXF Generator")
st.caption(
    "Enter the profile and manufacturing values, check the calculated "
    "section, then generate and download the DXF."
)


def number_field(
    label: str,
    key: str,
    *,
    step: float = 1.0,
    help_text: str | None = None,
    min_value: float | None = None,
) -> float:
    kwargs = {
        "label": label,
        "value": float(DEFAULT_PARAMETERS[key]),
        "step": float(step),
        "format": "%.3f",
        "key": key,
        "help": help_text,
    }

    if min_value is not None:
        kwargs["min_value"] = float(min_value)

    return float(st.number_input(**kwargs))


def draw_profile(result: CalculationResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    front_x = [point[0] for point in result.front_chain]
    front_y = [point[1] for point in result.front_chain]
    rear_x = [point[0] for point in result.rear_chain]
    rear_y = [point[1] for point in result.rear_chain]

    ax.plot(front_x, front_y, linewidth=1.8)
    ax.plot(rear_x, rear_y, linewidth=1.8)

    depth_start, depth_end = result.gutter_arm_line
    ax.plot(
        [depth_start[0], depth_end[0]],
        [depth_start[1], depth_end[1]],
        linestyle="--",
        linewidth=1.0,
    )

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("mm")
    ax.set_ylabel("mm")
    ax.grid(True, linewidth=0.35)
    fig.tight_layout()

    return fig


with st.form("profile_form"):
    main_tab, geometry_tab, manufacturing_tab, stop_end_tab = st.tabs(
        [
            "Main profile",
            "Roof geometry",
            "Manufacturing",
            "Stop end",
        ]
    )

    with main_tab:
        st.subheader("Main profile dimensions")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            a = number_field("A (mm)", "A", min_value=0.001)
            e = number_field("E (mm)", "E", min_value=0.001)

        with c2:
            b = number_field("B (mm)", "B", min_value=0.001)
            g = number_field("G (mm)", "G", min_value=0.001)

        with c3:
            c = number_field("C (mm)", "C", min_value=0.001)
            h = number_field("H (mm)", "H", min_value=0.001)

        with c4:
            d = number_field("D (mm)", "D", min_value=0.001)
            hem_gap = number_field(
                "A/B hem gap (mm)",
                "HEM_GAP_AB",
                step=0.1,
                min_value=0.0,
            )

        gutter_length = number_field(
            "Flat-pattern length (mm)",
            "GUTTER_LENGTH",
            min_value=0.001,
        )

    with geometry_tab:
        st.subheader("Roof and profile geometry")
        c1, c2 = st.columns(2)

        with c1:
            roof_pitch = number_field(
                "Roof pitch (degrees)",
                "ROOF_PITCH",
                step=0.5,
                help_text=(
                    "Controls B and G. These two flanges remain parallel."
                ),
            )
            gutter_arm_depth = number_field(
                "Gutter arm depth (mm)",
                "GUTTER_ARM_DEPTH",
                step=0.1,
                min_value=0.001,
                help_text=(
                    "Measured perpendicular to G, from F/G to the "
                    "extension of B."
                ),
            )

        with c2:
            angle_cd = number_field(
                "C/D angle (degrees)",
                "ANGLE_CD",
                step=0.5,
            )
            angle_de = number_field(
                "D/E angle (degrees)",
                "ANGLE_DE",
                step=0.5,
            )
            angle_ef = number_field(
                "E/F angle (degrees)",
                "ANGLE_EF",
                step=0.5,
            )

        with st.expander("Small / male-end adjustments"):
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                a_small_extra = number_field(
                    "A extra (mm)",
                    "A_SMALL_EXTRA",
                    step=0.1,
                )
                e_small_reduction = number_field(
                    "E reduction (mm)",
                    "E_SMALL_REDUCTION",
                    step=0.1,
                )

            with c2:
                b_small_reduction = number_field(
                    "B reduction (mm)",
                    "B_SMALL_REDUCTION",
                    step=0.1,
                )
                f_small_reduction = number_field(
                    "F reduction (mm)",
                    "F_SMALL_REDUCTION",
                    step=0.1,
                )

            with c3:
                c_small_reduction = number_field(
                    "C reduction (mm)",
                    "C_SMALL_REDUCTION",
                    step=0.1,
                )
                g_small_reduction = number_field(
                    "G reduction (mm)",
                    "G_SMALL_REDUCTION",
                    step=0.1,
                )

            with c4:
                d_small_reduction = number_field(
                    "D reduction (mm)",
                    "D_SMALL_REDUCTION",
                    step=0.1,
                )

    with manufacturing_tab:
        st.subheader("Joint, wheel forming and holes")
        c1, c2, c3 = st.columns(3)

        with c1:
            overlap = number_field(
                "Overlap (mm)",
                "OVERLAP",
                min_value=0.001,
            )
            wheel_form = number_field(
                "Wheel-form line from right (mm)",
                "WHEEL_FORM_FROM_RIGHT",
                min_value=0.001,
            )
            left_relief = number_field(
                "Left-end relief (mm)",
                "LEFT_END_RELIEF",
                min_value=0.001,
            )

        with c2:
            notch_length = number_field(
                "Notch safety length (mm)",
                "NOTCH_LENGTH",
                min_value=0.001,
            )
            hole_diameter = number_field(
                "Hole diameter (mm)",
                "HOLE_DIAMETER",
                step=0.5,
                min_value=0.001,
            )
            hole_x = number_field(
                "Hole centre from left (mm)",
                "HOLE_X_FROM_LEFT",
                min_value=0.0,
            )

        with c3:
            hole_from_fold = number_field(
                "First/last hole from fold (mm)",
                "HOLE_DISTANCE_FROM_FOLD",
                min_value=0.0,
            )
            maximum_hole_spacing = number_field(
                "Maximum hole spacing (mm)",
                "MAX_HOLE_SPACING",
                min_value=0.001,
            )
            section_gap = number_field(
                "Section gap from flat (mm)",
                "SECTION_GAP_FROM_FLAT",
                min_value=0.0,
            )

    with stop_end_tab:
        st.subheader("Stop-end settings")
        c1, c2, c3 = st.columns(3)

        with c1:
            stop_lap = number_field(
                "Lap (mm)",
                "STOP_END_LAP",
                min_value=0.001,
            )
            stop_c_reduction = number_field(
                "C reduction (mm)",
                "STOP_C_REDUCTION",
                step=0.1,
            )
            stop_d_reduction = number_field(
                "D reduction (mm)",
                "STOP_D_REDUCTION",
                step=0.1,
            )

        with c2:
            stop_e_reduction = number_field(
                "E reduction (mm)",
                "STOP_E_REDUCTION",
                step=0.1,
            )
            stop_f_reduction = number_field(
                "F reduction (mm)",
                "STOP_F_REDUCTION",
                step=0.1,
            )
            stop_cut_angle = number_field(
                "C/D cut angle (degrees)",
                "STOP_CD_CUT_ANGLE",
                step=0.5,
            )

        with c3:
            stop_min_angle = number_field(
                "Minimum tool angle (degrees)",
                "STOP_CD_MIN_CUT_ANGLE",
                step=0.5,
                min_value=30.0,
            )
            stop_gap = number_field(
                "Gap to right of flat (mm)",
                "STOP_END_GAP_FROM_FLAT",
                min_value=0.0,
            )

    output_name = st.text_input(
        "DXF file name",
        value="parametric_gutter.dxf",
    )

    submitted = st.form_submit_button(
        "Generate DXF",
        type="primary",
        use_container_width=True,
    )


parameters = {
    "A": a,
    "B": b,
    "C": c,
    "D": d,
    "E": e,
    "G": g,
    "H": h,
    "HEM_GAP_AB": hem_gap,
    "GUTTER_LENGTH": gutter_length,
    "ROOF_PITCH": roof_pitch,
    "GUTTER_ARM_DEPTH": gutter_arm_depth,
    "ANGLE_CD": angle_cd,
    "ANGLE_DE": angle_de,
    "ANGLE_EF": angle_ef,
    "A_SMALL_EXTRA": a_small_extra,
    "B_SMALL_REDUCTION": b_small_reduction,
    "C_SMALL_REDUCTION": c_small_reduction,
    "D_SMALL_REDUCTION": d_small_reduction,
    "E_SMALL_REDUCTION": e_small_reduction,
    "F_SMALL_REDUCTION": f_small_reduction,
    "G_SMALL_REDUCTION": g_small_reduction,
    "OVERLAP": overlap,
    "WHEEL_FORM_FROM_RIGHT": wheel_form,
    "LEFT_END_RELIEF": left_relief,
    "NOTCH_LENGTH": notch_length,
    "HOLE_DIAMETER": hole_diameter,
    "HOLE_X_FROM_LEFT": hole_x,
    "HOLE_DISTANCE_FROM_FOLD": hole_from_fold,
    "MAX_HOLE_SPACING": maximum_hole_spacing,
    "STOP_END_LAP": stop_lap,
    "STOP_C_REDUCTION": stop_c_reduction,
    "STOP_D_REDUCTION": stop_d_reduction,
    "STOP_E_REDUCTION": stop_e_reduction,
    "STOP_F_REDUCTION": stop_f_reduction,
    "STOP_CD_CUT_ANGLE": stop_cut_angle,
    "STOP_CD_MIN_CUT_ANGLE": stop_min_angle,
    "STOP_END_GAP_FROM_FLAT": stop_gap,
    "SECTION_GAP_FROM_FLAT": section_gap,
}


try:
    preview = calculate_profile(parameters)

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Calculated F", f"{preview.f:.2f} mm")
    metric_2.metric("Girth", f"{preview.girth:.2f} mm")
    metric_3.metric("Calculated BC", f"{preview.angle_bc:.2f}°")
    metric_4.metric("Calculated FG", f"{preview.angle_fg:.2f}°")

    preview_col, small_end_col = st.columns([1.6, 1.0])

    with preview_col:
        st.subheader("Section preview")
        figure = draw_profile(preview)
        st.pyplot(figure, clear_figure=True)

    with small_end_col:
        st.subheader("Calculated small end")
        st.dataframe(
            {
                "Face": list(preview.small_end.keys()),
                "Dimension (mm)": [
                    round(value, 3)
                    for value in preview.small_end.values()
                ],
            },
            hide_index=True,
            use_container_width=True,
        )

except Exception as exc:
    preview = None
    st.error(str(exc))


if submitted:
    if preview is None:
        st.error("Correct the invalid parameters before generating the DXF.")
    else:
        try:
            with st.spinner("Generating DXF..."):
                dxf_bytes, generated, safe_name = generate_dxf(
                    parameters,
                    output_name,
                )

            st.session_state["generated_dxf"] = dxf_bytes
            st.session_state["generated_name"] = safe_name
            st.success("DXF generated successfully.")

        except ModuleNotFoundError as exc:
            st.error(
                "A required Python package is missing. Install the packages "
                "listed in requirements.txt."
            )
            st.exception(exc)

        except Exception as exc:
            st.error(f"DXF generation failed: {exc}")
            st.exception(exc)


if "generated_dxf" in st.session_state:
    st.download_button(
        "Download generated DXF",
        data=st.session_state["generated_dxf"],
        file_name=st.session_state["generated_name"],
        mime="application/dxf",
        type="primary",
        use_container_width=True,
    )


with st.expander("Deployment and file information"):
    st.markdown(
        """
        This application requires the following files in the same folder:

        - `app.py`
        - `trimline_engine.py`
        - `trimline_generator_template.py`
        - `requirements.txt`

        Run locally with:

        ```bash
        python -m pip install -r requirements.txt
        python -m streamlit run app.py
        ```
        """
    )
