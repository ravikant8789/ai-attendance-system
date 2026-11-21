
import streamlit as st
from PIL import Image

from src.screens.home_screen import home_screen
from src.screens.hr_screen import hr_screen
from src.screens.employee_screen import employee_screen

from src.components.dialog_auto_join import auto_join_dialog
from src.assets import get_asset_path


def main():
    st.set_page_config(
        page_title='AI Attendance System - Office Portal',
        page_icon=get_asset_path("logo.png")
    )
    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    match st.session_state['login_type']:
        case 'hr' | 'teacher':
            hr_screen()

        case 'employee' | 'student':
            employee_screen()
        
        case None:
            home_screen()

    join_code = st.query_params.get('join-code')
    if join_code:
        if st.session_state.login_type not in ['employee', 'student']:
            st.session_state.login_type = 'employee'
            st.rerun()
        if st.session_state.get('is_logged_in') and st.session_state.get('user_role') in ['employee', 'student']:
            auto_join_dialog(join_code)


main()