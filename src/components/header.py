import streamlit as st
from src.assets import get_asset_base64


def header_home():
    logo_url = get_asset_base64("logo.png")
    
    st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:25px; margin-top:20px">
            <img src='{logo_url}' style='height:95px; border-radius:18px;' />
            <h1 style='text-align:center; color:#E0E3FF; letter-spacing:1px;'>AI<br/>ATTENDANCE</h1>
            <p style='color:#E0E3FF; font-weight:600; font-size:1.1rem; margin-top:5px;'>Office Attendance & Clock-In System</p>
        </div>   
    """, unsafe_allow_html=True)


def header_dashboard():
    logo_url = get_asset_base64("logo.png")
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center; gap:12px">
            <img src='{logo_url}' style='height:75px; border-radius:14px;' />
            <div>
                <h2 style='text-align:left; color:#5865F2; margin:0;'>AI<br/>ATTENDANCE</h2>
                <span style='color:#64748b; font-size:0.85rem; font-weight:600;'>OFFICE PORTAL</span>
            </div>
        </div>   
    """, unsafe_allow_html=True)
