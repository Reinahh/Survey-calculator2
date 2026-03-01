import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

# --- HELPER FUNCTIONS ---
def dms_to_decimal(d, m, s):
    return d + (m / 60) + (s / 3600)

def decimal_to_dms(decimal_deg):
    degrees = int(decimal_deg)
    remainder = abs(decimal_deg - degrees)
    minutes_full = remainder * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60
    return degrees, minutes, seconds

def calculate_adjustment(a_deg, b_deg, c_deg, earth_r, side_bc, wa, wb, wc):
    # Spherical Excess Calculation
    alpha = math.radians(b_deg)
    beta = math.radians(c_deg)
    f_area = 0.5 * (side_bc**2) * (math.sin(alpha) * math.sin(beta)) / math.sin(alpha + beta)
    E_rad = f_area / (earth_r**2 * math.sin(math.radians(a_deg)))
    E_sec = E_rad * 3600
    
    # Misclosure
    sum_angles = a_deg + b_deg + c_deg
    theoretical = 180 + (E_sec / 3600)
    mis_deg = sum_angles - theoretical
    
    # Weighted Adjustment
    inv_wt_sum = (1/wa) + (1/wb) + (1/wc)
    corr_deg = -mis_deg
    
    adj_a = a_deg + ((1/wa) / inv_wt_sum) * corr_deg
    adj_b = b_deg + ((1/wb) / inv_wt_sum) * corr_deg
    adj_c = c_deg + ((1/wc) / inv_wt_sum) * corr_deg
    
    return f_area, E_sec, mis_deg * 3600, adj_a, adj_b, adj_c

# --- UI CONFIG ---
st.set_page_config(page_title="Survey Adjuster Pro", layout="wide")
st.title("📐 Geodetic Triangle Adjustment Tool")

tab1, tab2, tab3 = st.tabs(["Manual Input", "Batch Upload (CSV)", "Triangle Sketch"])

# --- TAB 1: MANUAL INPUT ---
with tab1:
    col_in, col_out = st.columns([1, 2])
    with col_in:
        st.subheader("Field Measurements")
        a_d = st.number_input("Angle A (Deg)", value=60.0)
        b_d = st.number_input("Angle B (Deg)", value=60.0)
        c_d = st.number_input("Angle C (Deg)", value=60.0)
        side_c = st.number_input("Side BC (meters)", value=1000.0)
        radius = st.number_input("Earth Radius", value=6371000.0)
    
    # Perform Calc
    f, e, mis, aa, ab, ac = calculate_adjustment(a_d, b_d, c_d, radius, side_c, 1.0, 1.0, 1.0)
    
    with col_out:
        st.subheader("Adjustment Results")
        m1, m2, m3 = st.columns(3)
        m1.metric("Area (f)", f"{f:.2f} m²")
        m2.metric("Excess (E)", f"{e:.4f}\"")
        m3.metric("Misclosure", f"{mis:.3f}\"", delta=f"{mis:.3f}", delta_color="inverse")
        
        st.write("### Adjusted Angles")
        st.success(f"**A':** {decimal_to_dms(aa)[0]}° {decimal_to_dms(aa)[1]}' {decimal_to_dms(aa)[2]:.2f}\"")
        st.success(f"**B':** {decimal_to_dms(ab)[0]}° {decimal_to_dms(ab)[1]}' {decimal_to_dms(ab)[2]:.2f}\"")
        st.success(f"**C':** {decimal_to_dms(ac)[0]}° {decimal_to_dms(ac)[1]}' {decimal_to_dms(ac)[2]:.2f}\"")

# --- TAB 2: BATCH PROCESSING ---
with tab2:
    st.subheader("Upload Survey Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        # Assuming columns: A, B, C, Radius, SideBC
        results = []
        for index, row in df.iterrows():
            res = calculate_adjustment(row['A'], row['B'], row['C'], row['Radius'], row['SideBC'], 1, 1, 1)
            results.append(res)
        
        res_df = pd.DataFrame(results, columns=['Area', 'Excess', 'Misclosure', 'Adj_A', 'Adj_B', 'Adj_C'])
        st.write("Processed Results:", res_df)
        st.download_button("Download Results", res_df.to_csv().encode('utf-8'), "adjusted_survey.csv")

# --- TAB 3: SKETCH ---
with tab3:
    st.subheader("Visual Geometry Sketch")
    fig, ax = plt.subplots()
    # Simple triangle visualization
    pts = [[0,0], [side_c, 0], [side_c/2, side_c * math.sin(math.radians(60))]]
    polygon = plt.Polygon(pts, closed=True, fill=None, edgecolor='blue', linewidth=2)
    ax.add_patch(polygon)
    ax.text(pts[2][0], pts[2][1], '  A', fontsize=12)
    ax.text(pts[0][0], pts[0][1], 'B (0,0)', verticalalignment='top')
    ax.text(pts[1][0], pts[1][1], f'C ({side_c},0)', verticalalignment='top')
    ax.set_aspect('equal')
    plt.axis('off')
    st.pyplot(fig)