import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. CORE MATH ---
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
st.set_page_config(page_title="Survey Pro", layout="wide")
st.title("📐 Geodetic Triangle Adjustment")

t1, t2, t3 = st.tabs(["Manual Input", "Batch Upload", "Triangle Sketch"])

with t1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Input Measurements")
        a_in = st.number_input("Angle A (Decimal Degrees)", value=60.0, format="%.4f")
        b_in = st.number_input("Angle B (Decimal Degrees)", value=60.0, format="%.4f")
        c_in = st.number_input("Angle C (Decimal Degrees)", value=60.0, format="%.4f")
        s_bc = st.number_input("Side BC (meters)", value=1000.0)
        r_earth = st.number_input("Earth Radius (m)", value=6371000.0)
    
    f, e, m, aa, ab, ac = calculate_adjustment(a_in, b_in, c_in, r_earth, s_bc)
    
    with col2:
        st.subheader("Results")
        st.metric("Misclosure", f"{m:.4f} sec", delta=f"{m:.2f}", delta_color="inverse")
        st.write(f"**Calculated Area:** {f:.2f} m²")
        st.info(f"**Adjusted A:** {aa:.5f}° | **B:** {ab:.5f}° | **C:** {ac:.5f}°")

with t2:
    st.subheader("CSV Batch Processing")
    up = st.file_uploader("Upload your survey_test.csv", type="csv")
    if up:
        df = pd.read_csv(up)
        # Apply the calculation to every row
        results = df.apply(lambda row: calculate_adjustment(row['A'], row['B'], row['C'], row['Radius'], row['SideBC']), axis=1)
        # Expand results into new columns
        df[['Area', 'Excess', 'Misclosure_Sec', 'Adj_A', 'Adj_B', 'Adj_C']] = pd.DataFrame(results.tolist(), index=df.index)
        st.dataframe(df)
        st.download_button("Download Adjusted Data", df.to_csv(index=False), "results.csv")

with t3:
    st.subheader("Geometric Sketch")
    # Coordinates for plotting
    # B is at (0,0), C is at (side_bc, 0)
    # A is calculated using trigonometry
    angle_b_rad = math.radians(b_in)
    angle_c_rad = math.radians(c_in)
    
    # Using Sine Rule to find side AB (c_side)
    # a/sin(A) = c/sin(C) -> c_side = (side_bc * sin(C)) / sin(A)
    angle_a_rad = math.radians(180 - (b_in + b_in)) # Approximate for sketch
    c_side = (s_bc * math.sin(angle_c_rad)) / math.sin(math.radians(a_in))
    
    ax_x = c_side * math.cos(angle_b_rad)
    ax_y = c_side * math.sin(angle_b_rad)
    
    fig, ax = plt.subplots()
    # Triangle Points: B(0,0), C(s_bc, 0), A(ax_x, ax_y)
    x_coords = [0, s_bc, ax_x, 0]
    y_coords = [0, 0, ax_y, 0]
    
    ax.plot(x_coords, y_coords, marker='o', color='blue')
    ax.fill(x_coords, y_coords, alpha=0.2, color='skyblue')
    ax.text(0, 0, '  B', verticalalignment='top')
    ax.text(s_bc, 0, '  C', verticalalignment='top')
    ax.text(ax_x, ax_y, '  A', verticalalignment='bottom')
    
    ax.set_aspect('equal')
    plt.title("Visual Representation of Triangle")
    st.pyplot(fig)
