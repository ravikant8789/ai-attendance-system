import streamlit as st
from src.components.header import header_home
from src.components.footer import footer_home
from src.ui.base_layout import style_base_layout, style_background_home
from src.assets import get_asset_base64


def home_screen():
    header_home()
    style_background_home()
    style_base_layout()

    col1, col2 = st.columns(2, gap="large")

    emp_img = get_asset_base64("mascot_student.png")
    hr_img = get_asset_base64("mascot_prof.png")

    with col1:
        st.header("I'm Employee")
        st.caption("Biometric Clock In / Clock Out & Timesheet")
        st.markdown(f"<div style='text-align:center; margin:10px 0;'><img src='{emp_img}' style='width:120px; object-fit:contain;' /></div>", unsafe_allow_html=True)
        if st.button('Employee Portal', type='primary', icon=':material/badge:', icon_position='right', width='stretch'):
            st.session_state['login_type'] = 'employee'
            st.rerun()

    with col2:
        st.header("I'm HR / Admin")
        st.caption("Reception Kiosk, Departments & Workforce Reports")
        st.markdown(f"<div style='text-align:center; margin:10px 0;'><img src='{hr_img}' style='width:145px; object-fit:contain;' /></div>", unsafe_allow_html=True)
        if st.button('HR & Admin Portal', type='primary', icon=':material/admin_panel_settings:', icon_position='right', width='stretch'):
            st.session_state['login_type'] = 'hr'
            st.rerun()

    footer_home()
