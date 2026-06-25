import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Alloy Addition Calculator", page_icon="⚙️", layout="centered")

st.title("⚙️ Alloy Addition Calculator")
st.caption(
    "Calculate exactly how much of each alloying element to add — and how much "
    "dilution material is needed for over-limit elements — to hit your target "
    "spec, accounting for melt recovery and the fact that every addition (or "
    "dilution) changes the bath weight and therefore everything else's %."
)
unit = st.radio("Weight unit", ["kg", "tons (metric)"], horizontal=True)
unit_factor = 1.0 if unit == "kg" else 1000.0  # multiply by this to get kg

-------------------------------------------------------------------
STEP 1 — Main ingredients (charge materials)
-------------------------------------------------------------------
st.header("1. Main Ingredients (Charge)")
st.caption(
    "List every raw material you charged — Casting, TT, Wheels, Ingot, etc — "
    "with its weight and expected melting recovery. The bath weight is the sum "
    "of each material's retained (recovered) weight."
)

if "ingredients_df" not in st.session_state:
    st.session_state.ingredients_df = pd.DataFrame(
        [{"Material": "Casting", "Weight": 10000.0 if unit == "kg" else 10.0, "Recovery %": 80.0}]
    )

ingredients_df = st.data_editor(
    st.session_state.ingredients_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Material": st.column_config.TextColumn(required=True),
        "Weight": st.column_config.NumberColumn(format="%.3f", min_value=0.0),
        "Recovery %": st.column_config.NumberColumn(format="%.1f", min_value=0.1, max_value=100.0),
    },
    key="ingredients_editor",
)

ing = ingredients_df.dropna(subset=["Material"])
ing = ing[ing["Material"].astype(str).str.strip() != ""]
ing = ing.fillna(0)
bath_weight_kg = float((ing["Weight"] * unit_factor * ing["Recovery %"] / 100).sum())
bath_weight_display = bath_weight_kg / unit_factor

st.success(f"**Molten bath weight ≈ {bath_weight_display:,.3f} {unit}** ({bath_weight_kg:,.1f} kg)")

# -------------------------------------------------------------------
# STEP 2 — Elements table
# -------------------------------------------------------------------
st.header("2. Alloying Elements")
st.caption(
    "Enter **Current %** from your test report and the **Target %** you need. "
    "If Current % is *below* target, the app calculates an addition. If Current % "
    "is *above* target (e.g. 12% vs a 10% limit), the app treats it as an "
    "over-limit element and works out the dilution needed in Step 3 — no need "
    "to set anything differently yourself, it's detected automatically."
)

if "elements_df" not in st.session_state:
    st.session_state.elements_df = pd.DataFrame(
        [
            {"Element": "Silicon (Si)", "Current %": 5.0, "Target %": 10.0,
             "Mode": "Adjust to Target", "Addition Recovery %": 100.0},
            {"Element": "Manganese (Mn)", "Current %": 0.0, "Target %": 10.0,
             "Mode": "Adjust to Target", "Addition Recovery %": 100.0},
        ]
    )

edited_df = st.data_editor(
    st.session_state.elements_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Element": st.column_config.TextColumn(required=True),
        "Current %": st.column_config.NumberColumn(format="%.3f", min_value=0.0, max_value=100.0),
        "Target %": st.column_config.NumberColumn(format="%.3f", min_value=0.0, max_value=100.0),
        "Mode": st.column_config.SelectboxColumn(options=["Adjust to Target", "Track Only"]),
        "Addition Recovery %": st.column_config.NumberColumn(
            format="%.1f", min_value=0.1, max_value=100.0,
            help="Used only when this element needs ADDING (current below target). "
                 "Expected yield of the addition itself — pure Si/Cu/Fe/Mn are usually "
                 "~98-100%, Mg/Zn additions are often lower (~85-95%). Ignored for "
                 "over-limit (dilution) rows.",
        ),
    },
    key="elements_editor",
)

# -------------------------------------------------------------------
# STEP 3 — Dilution material (only used if any element is over-limit)
# -------------------------------------------------------------------
st.header("3. Dilution Material (only if any element is over-limit)")
# st.caption(
#     "If any element's Current % is above its Target % above, fill this in — the "
#     "app will calculate exactly how much of this material to add to bring the "
#     "*worst* over-limit element down to its target (other over-limit elements "
#     "will land at-or-below their own targets too, as a side effect). "
#     "**Assumption:** this material is treated as containing ~0% of every tracked "
#     "element — i.e. it's a clean diluent like primary aluminium, low-alloy ingot, "
#     "or clean low-content scrap. If your chosen material actually carries "
#     "meaningful amounts of a tracked element, list it as a Main Ingredient in "
#     "Step 1 instead, with its known weight."
# )

dc1, dc2 = st.columns(2)
with dc1:
    diluent_name = st.text_input("Dilution material name", value="Casting / TT")
with dc2:
    diluent_recovery = st.number_input(
        "Dilution material recovery %", min_value=0.1, max_value=100.0, value=90.0, step=0.5
    )

with st.expander("ℹ️ How the calculation works"):
    st.markdown(
        "- **Additions** (current % below target) for multiple elements are "
        "solved **simultaneously**, since adding one dilutes the bath and "
        "therefore changes every other element's %.\n"
        "- **Over-limit elements** (current % above target) can't be fixed by "
        "adding more of themselves — they need dilution. If several elements "
        "are over-limit at once, you generally can't hit every one's exact "
        "target with a single shared dilution batch, so the app dilutes based "
        "on whichever element needs the **most** dilution (the *driver*). The "
        "others will end up at or below their own target automatically.\n"
        "- The dilution material's weight and any simultaneous additions are "
        "solved together, since the diluent also adds bath weight that dilutes "
        "the additions too.\n"
        "- **Gross mass to weigh** = retained mass ÷ recovery — the real amount "
        "to weigh out on the floor, accounting for burn-off / melting loss."
    )

calc_btn = st.button("🧮 Calculate", type="primary", use_container_width=True)

# -------------------------------------------------------------------
# STEP 4 — Calculation
# -------------------------------------------------------------------
if calc_btn:
    df = edited_df.copy()
    df = df.dropna(subset=["Element"])
    df = df[df["Element"].astype(str).str.strip() != ""]
    df[["Current %", "Target %", "Addition Recovery %"]] = df[
        ["Current %", "Target %", "Addition Recovery %"]
    ].fillna(0)

    if df.empty:
        st.error("Add at least one element first.")
        st.stop()
    if bath_weight_kg <= 0:
        st.error("Bath weight is zero — check your Main Ingredients in Step 1.")
        st.stop()

    W0 = bath_weight_kg
    adjust = df[df["Mode"] == "Adjust to Target"].reset_index(drop=True)
    track = df[df["Mode"] == "Track Only"].reset_index(drop=True)

    add_rows = adjust[adjust["Current %"] < adjust["Target %"]].reset_index(drop=True)
    dil_rows = adjust[adjust["Current %"] > adjust["Target %"]].reset_index(drop=True)
    noop_rows = adjust[adjust["Current %"] == adjust["Target %"]].reset_index(drop=True)

    notes = []
    diluent_retained_kg = 0.0
    diluent_gross_kg = 0.0
    driver_name = None
    y = {}  # element name -> retained added mass (kg)
    solved_ok = True

    if len(dil_rows) > 0:
        ratios = dil_rows["Current %"] / dil_rows["Target %"]
        driver_idx = ratios.idxmax()
        driver_name = dil_rows.loc[driver_idx, "Element"]
        driver_ratio = ratios.loc[driver_idx]
        W_final = W0 * driver_ratio

        for _, row in add_rows.iterrows():
            m0_i = W0 * row["Current %"] / 100.0
            p_i = row["Target %"] / 100.0
            y[row["Element"]] = p_i * W_final - m0_i

        sumY = sum(y.values())
        D = W_final - W0 - sumY
        if D < -1e-6:
            notes.append(
                "Your other additions alone already provide enough dilution — "
                f"no separate {diluent_name or 'dilution material'} is needed."
            )
            D = 0.0
            W_final = W0 + sumY
        diluent_retained_kg = D
        diluent_gross_kg = D / (diluent_recovery / 100.0) if diluent_recovery > 0 else D
    else:
        n = len(add_rows)
        y_arr = np.zeros(n)
        if n > 0:
            p = add_rows["Target %"].values / 100.0
            m0 = W0 * add_rows["Current %"].values / 100.0
            A = np.eye(n) - np.outer(p, np.ones(n))
            b = p * W0 - m0
            try:
                y_arr = np.linalg.solve(A, b)
            except np.linalg.LinAlgError:
                solved_ok = False
                st.error(
                    "Couldn't solve this system — the target percentages create a "
                    "degenerate/contradictory setup (e.g. they sum to ≥100%, or two "
                    "rows are identical). Please review the targets."
                )
        for i in range(n):
            y[add_rows.loc[i, "Element"]] = y_arr[i]
        W_final = W0 + sum(y.values())

    if solved_ok:
        rows = []

        for _, row in add_rows.iterrows():
            name = row["Element"]
            m0_i = W0 * row["Current %"] / 100.0
            y_i = y.get(name, 0.0)
            recov = max(row["Addition Recovery %"], 0.1) / 100.0
            x_gross_i = y_i / recov
            final_mass = m0_i + y_i
            final_pct = final_mass / W_final * 100
            achievable = y_i >= -1e-6
            rows.append({
                "Element": name, "Current %": row["Current %"], "Target %": row["Target %"],
                "Final %": round(final_pct, 4),
                f"Retained Add ({unit})": round(y_i / unit_factor, 4),
                f"Gross Add to Weigh ({unit})": round(x_gross_i / unit_factor, 4) if achievable else None,
                "Type": "Addition" if achievable else "⚠️ Unreachable by addition",
            })

        for _, row in dil_rows.iterrows():
            name = row["Element"]
            m0_i = W0 * row["Current %"] / 100.0
            final_pct = m0_i / W_final * 100
            is_driver = (name == driver_name)
            rows.append({
                "Element": name, "Current %": row["Current %"], "Target %": row["Target %"],
                "Final %": round(final_pct, 4),
                f"Retained Add ({unit})": 0.0,
                f"Gross Add to Weigh ({unit})": 0.0,
                "Type": "Dilution driver" if is_driver else "Dilution (satisfied)",
            })

        for _, row in noop_rows.iterrows():
            name = row["Element"]
            m0_i = W0 * row["Current %"] / 100.0
            final_pct = m0_i / W_final * 100
            rows.append({
                "Element": name, "Current %": row["Current %"], "Target %": row["Target %"],
                "Final %": round(final_pct, 4),
                f"Retained Add ({unit})": 0.0,
                f"Gross Add to Weigh ({unit})": 0.0,
                "Type": "Already at target",
            })

        for _, row in track.iterrows():
            name = row["Element"]
            m0_i = W0 * row["Current %"] / 100.0
            final_pct = m0_i / W_final * 100
            rows.append({
                "Element": name, "Current %": row["Current %"], "Target %": row["Target %"],
                "Final %": round(final_pct, 4),
                f"Retained Add ({unit})": 0.0,
                f"Gross Add to Weigh ({unit})": 0.0,
                "Type": "Tracked only",
            })

        result_df = pd.DataFrame(rows)

        st.header("4. Results")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        for n in notes:
            st.info(n)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(f"Final bath weight ({unit})", f"{W_final/unit_factor:,.3f}")
        with m2:
            st.metric("Balance / Al & untracked (%)", f"{100 - result_df['Final %'].sum():,.3f}")
        with m3:
            if driver_name:
                st.metric("Dilution driven by", driver_name)

        if len(dil_rows) > 0:
            st.subheader(f"Dilution material to add: {diluent_name or '(unnamed)'}")
            dc1, dc2 = st.columns(2)
            with dc1:
                st.metric(f"Retained ({unit})", f"{diluent_retained_kg/unit_factor:,.4f}")
            with dc2:
                st.metric(f"Gross to weigh ({unit})", f"{diluent_gross_kg/unit_factor:,.4f}")

        if (result_df["Type"] == "⚠️ Unreachable by addition").any():
            st.warning(
                "One or more addition rows came out unreachable — double-check "
                "those rows are actually below target; if current % is already "
                "at/above target, they should be left as-is and dilution will "
                "handle them automatically."
            )

        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download results as CSV", data=csv,
            file_name="alloy_addition_results.csv", mime="text/csv",
            use_container_width=True,
        )

st.divider()
# st.caption(
#     "Built for melt-shop floor use — works on desktop and mobile browsers. "
#     "Double-check critical charges against your standard lab/QA procedure."
)
