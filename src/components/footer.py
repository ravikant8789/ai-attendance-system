import streamlit as st


def footer_home():
    st.markdown("""
        <div style="margin-top:2.5rem; display:flex; gap:8px; justify-content:center; align-items:center; text-align:center;">
            <p style="font-weight:700; color:#FFFFFF; font-size:1.1rem; margin:0; letter-spacing:0.5px;">
                Created with ❤️ by <span style="color:#FFFFFF; font-weight:900; background:rgba(255,255,255,0.2); padding:3px 12px; border-radius:12px;">Ravikant</span>
            </p>
        </div>
    """, unsafe_allow_html=True)


def footer_dashboard():
    st.markdown("""
        <div style="margin-top:2.5rem; display:flex; gap:8px; justify-content:center; align-items:center; text-align:center;">
            <p style="font-weight:700; color:#1e293b; font-size:1.1rem; margin:0; letter-spacing:0.5px;">
                Created with ❤️ by <span style="color:#5865F2; font-weight:900; background:rgba(88,101,242,0.12); padding:3px 12px; border-radius:12px;">Ravikant</span>
            </p>
        </div>
    """, unsafe_allow_html=True)
