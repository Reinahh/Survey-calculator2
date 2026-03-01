import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

# 1. Basic Functions
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
    alpha = math.radians(b_deg)
    beta = math.radians(c_deg)
    # Area calculation
    f_area = 0.5 * (side_bc**2) * (math.sin(alpha) * math.sin(beta)) / math.sin(alpha + beta)
    # Spherical Excess
    E_rad = f_area / (earth_r**2 * math.sin(math.radians(a_deg)))
    E_sec = E_rad * 3600
    # Misclosure
    sum_angles = a_deg + b_deg + c_deg
    theoretical = 180 + (E_sec / 3600)
    mis_deg = sum_angles - theoretical
    # Adjustment
    inv_wt_sum = (1/wa) + (1/wb) + (1/wc)
    corr_deg = -mis_deg
    adj_a = a_deg + ((1/wa) / inv_wt_sum) * corr_deg
    adj_b = b_deg + ((1/wb) / inv_wt_sum) * corr_deg
    adj_c = c_deg + ((1/wc) / inv_wt_sum) * corr_deg
    return f_area, E_sec, mis_deg * 3600, adj_a, adj_b, adj_c

# 2. UI Layout
st.set_page_config(page_title="Survey Pro", layout="wide")
st.title("📐 Geodetic Triangle Adjustment")

t1, t2, t3 = st.tabs(["Manual", "Batch", "Sketch"])

with t1:
    col1, col2 = st.columns(2)
    with col1:
        a_in = st.number_input("Angle A (Decimal Deg)", value=60.0)
        b_in = st.number_input("Angle B (Decimal Deg)", value=60.0)
        c_in = st.number_input("Angle C (Decimal Deg)", value=60.0)
        s_bc = st.number_input("Side BC", value=1000.0)
        r_earth = st.number_input("Radius", value=6371000.0)
    
    # Run Calc
    f, e, m, aa, ab, ac = calculate_adjustment(a_in, b_in, c_in, r_earth, s_bc, 1, 1, 1)
    
    with col2:
        st.metric("Misclosure (sec)", f"{m:.4f}")
        st.write(f"**Adj Angle A:** {aa:.4f}°")
        st.write(f"**Adj Angle B:** {ab:.4f}°")
        st.write(f"**Adj Angle C:** {ac:.4f}°")

with t2:
    st.write("Upload CSV with columns: A, B, C, Radius, SideBC")
    up = st.file_uploader("Upload File")
    if up:
        df = pd.read_csv(up)
        st.write(df.head())

with t3:
    st.write("Visual Sketch")
    fig, ax = plt.subplots()
    ax.plot([0, 1, 0.5, 0], [0, 0, 0.8, 0]) # Simple Triangle
    st.pyplot(fig)