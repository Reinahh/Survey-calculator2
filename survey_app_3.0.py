import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

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
    # Area (f)
    f_area = 0.5 * (side_bc**2) * (math.sin(alpha) * math.sin(beta)) / math.sin(alpha + beta)
    # Spherical Excess (E)
    E_rad = f_area / (earth_r**2 * math.sin(math.radians(a_deg)))
    E_sec = E_rad * 3600
    # Misclosure
    sum_angles = a_deg + b_deg + c_deg
    theoretical = 180 + (E_sec / 3600)
    mis_deg = sum_angles - theoretical
    # Weighted Correction
    inv_wt_sum = (1/wa) + (1/wb) + (1/wc)
    corr_deg = -mis_deg
    adj_a = a_deg + ((1/wa) / inv_wt_sum) * corr_deg
    adj_b = b_deg + ((1/wb) / inv_wt_sum) * corr_deg
    adj_c = c_deg + ((1/wc) / inv_wt_sum) * corr_deg
    return f_area, E_sec, mis_deg * 3600, adj_a, adj_b, adj_c

# --- 2. UI SETUP ---
st.set_page_config(page_title="Survey Pro DMS", layout="wide")
st.title("📐 Geodetic Triangle Adjustment (DMS Version)")

t1, t2, t3 = st.tabs(["Manual DMS Input", "Batch Upload (CSV)", "Triangle Sketch"])

with t1:
    col_input, col_result = st.columns([2, 1])
    
    with col_input:
        st.subheader("Field Measurements (DMS)")
        
        # Helper function for DMS UI rows
        def dms_input_row(label):
            st.write(f"**{label}**")
            c1, c2, c3 = st.columns(3)
            d = c1.number_input("Deg", key=f"{label}_d", value=60.0, step=1.0)
            m = c2.number_input("Min", key=f"{label}_m", value=0.0, step=1.0, max_value=59.0)
            s = c3.number_input("Sec", key=f"{label}_s", value=0.0, step=0.1, max_value=59.99)
            return dms_to_decimal(d, m, s)

        a_dec = dms_input_row("Angle A")
        b_dec = dms_input_row("Angle B")
        c_dec = dms_input_row("Angle C")
        
        st.divider()
        c_side_1, c_side_2 = st.columns(2)
        s_bc = c_side_1.number_input("Side BC (meters)", value=1000.0)
        r_earth = c_side_2.number_input("Earth Radius (m)", value=6371000.0)
    
    # Run Calculation
    f, e, m, aa, ab, ac = calculate_adjustment(a_dec, b_dec, c_dec, r_earth, s_bc)
    
    with col_result:
        st.subheader("Results")
        st.metric("Misclosure", f"{m:.4f} sec", delta_color="inverse")
        
        st.write("### Adjusted Angles")
        for label, val in zip(["A'", "B'", "C'"], [aa, ab, ac]):
            deg, mn, sec = decimal_to_dms(val)
            st.success(f"**{label}:** {deg}° {mn}' {sec:.3f}\"")

with t2:
    st.subheader("CSV Batch Processing (DMS)")
    st.info("CSV should have columns: A_d, A_m, A_s, B_d, B_m, B_s, C_d, C_m, C_s, Radius, SideBC")
    up = st.file_uploader("Upload DMS CSV", type="csv")
    if up:
        df = pd.read_csv(up)
        # Convert DMS columns to Decimal for the math engine
        df['A_dec'] = df.apply(lambda r: dms_to_decimal(r['A_d'], r['A_m'], r['A_s']), axis=1)
        df['B_dec'] = df.apply(lambda r: dms_to_decimal(r['B_d'], r['B_m'], r['B_s']), axis=1)
        df['C_dec'] = df.apply(lambda r: dms_to_decimal(r['C_d'], r['C_m'], r['C_s']), axis=1)
        
        results = df.apply(lambda r: calculate_adjustment(r['A_dec'], r['B_dec'], r['C_dec'], r['Radius'], r['SideBC']), axis=1)
        df[['Area', 'Excess', 'Misclosure_Sec', 'Adj_A', 'Adj_B', 'Adj_C']] = pd.DataFrame(results.tolist(), index=df.index)
        st.dataframe(df)

with t3:
    st.subheader("Geometric Sketch")
    # Coordinates for Point A relative to B(0,0) and C(side_bc, 0)
    angle_b_rad = math.radians(b_dec)
    c_side = (s_bc * math.sin(math.radians(c_dec))) / math.sin(math.radians(a_dec))
    ax_x = c_side * math.cos(angle_b_rad)
    ax_y = c_side * math.sin(angle_b_rad)
    
    fig, ax = plt.subplots()
    x_coords = [0, s_bc, ax_x, 0]
    y_coords = [0, 0, ax_y, 0]
    ax.plot(x_coords, y_coords, marker='o', color='blue')
    ax.fill(x_coords, y_coords, alpha=0.2, color='skyblue')
    ax.set_aspect('equal')
    plt.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig)
