import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 1. CORE MATH & CONVERSIONS ---
def dms_to_decimal(d, m, s):
    return d + (m / 60) + (s / 3600)

def decimal_to_dms(decimal_deg):
    degrees = int(decimal_deg)
    remainder = abs(decimal_deg - degrees)
    minutes_full = remainder * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60
    return degrees, minutes, seconds

def calculate_adjustment(a_deg, b_deg, c_deg, earth_r, side_bc, wa=1, wb=1, wc=1):
    alpha = math.radians(b_deg)
    beta = math.radians(c_deg)
    f_area = 0.5 * (side_bc**2) * (math.sin(alpha) * math.sin(beta)) / math.sin(alpha + beta)
    E_rad = f_area / (earth_r**2 * math.sin(math.radians(a_deg)))
    E_sec = E_rad * 3600
    sum_angles = a_deg + b_deg + c_deg
    theoretical_sum = 180 + (E_sec / 3600)
    misclosure_deg = sum_angles - theoretical_sum
    inv_wt_sum = (1/wa) + (1/wb) + (1/wc)
    corr_deg = -misclosure_deg
    adj_a = a_deg + ((1/wa) / inv_wt_sum) * corr_deg
    adj_b = b_deg + ((1/wb) / inv_wt_sum) * corr_deg
    adj_c = c_deg + ((1/wc) / inv_wt_sum) * corr_deg
    return f_area, E_sec, misclosure_deg * 3600, adj_a, adj_b, adj_c

# --- 2. SESSION STATE INITIALIZATION ---
# This ensures the app doesn't crash if you go to the Sketch tab before entering data
if 'sk_a' not in st.session_state:
    st.session_state.sk_a = 60.0
    st.session_state.sk_b = 60.0
    st.session_state.sk_c = 60.0
    st.session_state.sk_sbc = 1000.0

# --- 3. UI CONFIGURATION ---
st.set_page_config(page_title="Geodetic Pro + Batch Sketch", layout="wide")
st.title("📐 Geodetic Triangle Adjustment & Batch Visualizer")

tab1, tab2, tab3 = st.tabs(["Manual DMS Input", "Batch Upload & Select", "Spherical Sketch"])

# --- TAB 1: MANUAL INPUT ---
with tab1:
    col_in, col_res = st.columns([2, 1])
    with col_in:
        st.subheader("Field Measurements")
        def dms_row(label, key_prefix, def_val):
            st.write(f"**{label}**")
            c1, c2, c3 = st.columns(3)
            d = c1.number_input("Deg", key=f"{key_prefix}_d", value=def_val)
            m = c2.number_input("Min", key=f"{key_prefix}_m", value=0.0, max_value=59.0)
            s = c3.number_input("Sec", key=f"{key_prefix}_s", value=0.0, max_value=59.99)
            return dms_to_decimal(d, m, s)

        a_dec = dms_row("Angle A", "ma", 60.0)
        b_dec = dms_row("Angle B", "mb", 60.0)
        c_dec = dms_row("Angle C", "mc", 60.0)
        
        st.divider()
        c_s1, c_s2 = st.columns(2)
        s_bc = c_s1.number_input("Side BC (m)", value=1000.0)
        r_e = c_s2.number_input("Earth Radius (m)", value=6371000.0)
        
        if st.button("Update Sketch with Manual Data"):
            st.session_state.sk_a = a_dec
            st.session_state.sk_b = b_dec
            st.session_state.sk_c = c_dec
            st.session_state.sk_sbc = s_bc
            st.toast("Sketch Updated!")

    f, e, m, aa, ab, ac = calculate_adjustment(a_dec, b_dec, c_dec, r_e, s_bc)
    with col_res:
        st.subheader("Results")
        st.metric("Misclosure", f"{m:.3f}\"")
        st.write(f"**Area:** {f:.2f} m²")
        for l, v in zip(["A'", "B'", "C'"], [aa, ab, ac]):
            deg, mn, sec = decimal_to_dms(v)
            st.success(f"**{l}:** {deg}° {mn}' {sec:.2f}\"")

# --- TAB 2: BATCH PROCESSING ---
with tab2:
    st.subheader("CSV Batch Processing")
    up_file = st.file_uploader("Upload CSV (A_d, A_m, A_s, B_d, B_m, B_s, C_d, C_m, C_s, Radius, SideBC)", type="csv")
    if up_file:
        df = pd.read_csv(up_file)
        # Process Data
        df['A_dec'] = df.apply(lambda r: dms_to_decimal(r['A_d'], r['A_m'], r['A_s']), axis=1)
        df['B_dec'] = df.apply(lambda r: dms_to_decimal(r['B_d'], r['B_m'], r['B_s']), axis=1)
        df['C_dec'] = df.apply(lambda r: dms_to_decimal(r['C_d'], r['C_m'], r['C_s']), axis=1)
        
        results = df.apply(lambda r: calculate_adjustment(r['A_dec'], r['B_dec'], r['C_dec'], r['Radius'], r['SideBC']), axis=1)
        df[['Area', 'Excess', 'Misclosure', 'Adj_A', 'Adj_B', 'Adj_C']] = pd.DataFrame(results.tolist(), index=df.index)
        
        st.dataframe(df)
        
        st.divider()
        st.subheader("🔍 Select a Row to Sketch")
        selected_index = st.selectbox("Choose a triangle from the list:", options=df.index)
        
        if st.button("Load Selected Triangle into Sketcher"):
            row = df.loc[selected_index]
            st.session_state.sk_a = row['A_dec']
            st.session_state.sk_b = row['B_dec']
            st.session_state.sk_c = row['C_dec']
            st.session_state.sk_sbc = row['SideBC']
            st.success(f"Row {selected_index} loaded. Move to the Sketch tab!")

# --- TAB 3: SPHERICAL SKETCH ---
with tab3:
    st.subheader("Spherical Geometry Visualization")
    # Retrieve from Session State
    cur_a, cur_b, cur_c, cur_sbc = st.session_state.sk_a, st.session_state.sk_b, st.session_state.sk_c, st.session_state.sk_sbc
    
    # Trig for plotting
    angle_b_rad = math.radians(cur_b)
    angle_c_rad = math.radians(cur_c)
    # Law of Sines to get side AB (c_side)
    # c/sin(C) = a/sin(A)
    side_ab = (cur_sbc * math.sin(angle_c_rad)) / math.sin(math.radians(cur_a))
    
    A = np.array([side_ab * math.cos(angle_b_rad), side_ab * math.sin(angle_b_rad)])
    B = np.array([0, 0])
    C = np.array([cur_sbc, 0])

    def get_arc_points(p1, p2, bulge=0.08):
        mid = (p1 + p2) / 2
        dist = np.linalg.norm(p2-p1)
        perp = np.array([-(p2[1]-p1[1]), p2[0]-p1[0]])
        perp = (perp / np.linalg.norm(perp)) * (dist * bulge)
        t = np.linspace(0, 1, 50)
        curve = (1-t)**2 * p1[:,None] + 2*(1-t)*t*(mid + perp)[:,None] + t**2 * p2[:,None]
        return curve[0], curve[1]

    fig, ax = plt.subplots(figsize=(10, 7))
    # Draw arcs
    for p1, p2, b in [(B, C, -0.05), (C, A, 0.05), (A, B, 0.05)]:
        x_p, y_p = get_arc_points(p1, p2, b)
        ax.plot(x_p, y_p, color='#1f77b4', linewidth=3)
        
    ax.scatter([A[0], B[0], C[0]], [A[1], B[1], C[1]], color='red', s=100, zorder=5)
    ax.text(A[0], A[1], '  Station A', fontweight='bold')
    ax.text(B[0], B[1], ' B', verticalalignment='top')
    ax.text(C[0], C[1], ' C', verticalalignment='top')
    
    ax.set_aspect('equal')
    plt.axis('off')
    st.pyplot(fig)
    st.info(f"Currently Sketching: A={cur_a:.4f}°, B={cur_b:.4f}°, Side BC={cur_sbc}m")
