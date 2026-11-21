import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.department_card import department_card
from src.database.db import (
    check_hr_exists,
    create_hr,
    hr_login,
    get_hr_departments,
    get_attendance_for_hr,
    reset_hr_password,
    delete_department
)
from src.components.dialog_create_department import create_department_dialog
from src.components.dialog_share_department import share_department_dialog
from src.components.dialog_add_photo import add_photos_dialog
from src.components.dialog_view_department_staff import view_department_staff_dialog

from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import attendance_result_dialog
import numpy as np

from datetime import datetime
import pandas as pd
from src.database.config import supabase
from src.components.dialog_voice_attendance import voice_attendance_dialog


def hr_screen():
    style_background_dashboard()
    style_base_layout()

    if "hr_data" in st.session_state or "teacher_data" in st.session_state:
        hr_dashboard()
    elif 'hr_login_type' not in st.session_state or st.session_state.hr_login_type == "login":
        hr_screen_login()
    elif st.session_state.hr_login_type == "register":
        hr_screen_register()
    elif st.session_state.hr_login_type == "forgot_password":
        hr_screen_forgot_password()


def hr_dashboard():
    hr_data = st.session_state.get('hr_data') or st.session_state.get('teacher_data')
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {hr_data['name']}""")
        st.caption("Role: **HR / Operations Manager**")
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            st.session_state.pop('teacher_data', None)
            st.session_state.pop('hr_data', None)
            st.rerun()

    st.space()

    if "current_hr_tab" not in st.session_state:
        st.session_state.current_hr_tab = 'take_attendance'
    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = "primary" if st.session_state.current_hr_tab == 'take_attendance' else "tertiary"
        if st.button('🏢 Reception Kiosk', type=type1, width='stretch', icon=':material/badge:'):
            st.session_state.current_hr_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_hr_tab == 'manage_departments' else "tertiary"
        if st.button('📁 Departments & Teams', type=type2, width='stretch', icon=':material/corporate_fare:'):
            st.session_state.current_hr_tab = 'manage_departments'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_hr_tab == 'attendance_records' else "tertiary"
        if st.button('📊 Timesheets & Records', type=type3, width='stretch', icon=':material/table_chart:'):
            st.session_state.current_hr_tab = 'attendance_records'
            st.rerun()

    st.divider()

    if st.session_state.current_hr_tab == "take_attendance":
        hr_tab_reception_kiosk()
    if st.session_state.current_hr_tab == "manage_departments":
        hr_tab_manage_departments()
    if st.session_state.current_hr_tab == "attendance_records":
        hr_tab_timesheet_records()

    footer_dashboard()


def hr_tab_reception_kiosk():
    hr_data = st.session_state.get('hr_data') or st.session_state.get('teacher_data')
    hr_id = hr_data['teacher_id']
    st.header('Office Reception Kiosk / Scan Attendance')
    st.caption("Scan office entrance or reception photos to verify employee presence")

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    departments = get_hr_departments(hr_id)

    if not departments:
        st.warning('You haven\'t created any departments yet! Please create one in "Departments & Teams" to begin.')
        return
    
    dept_options = {f"{s['name']} (Dept Code: {s['subject_code']} - {s['section']})": s['subject_id'] for s in departments}

    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')

    with col1:
        selected_dept_label = st.selectbox('Select Department / Team', options=list(dept_options.keys()))

    with col2:
        if st.button('Add Photos', type='primary', icon=':material/photo_prints:', width='stretch'):
            add_photos_dialog()

    selected_dept_id = dept_options[selected_dept_label]

    st.divider()

    if st.session_state.attendance_images:
        st.header('Entrance Camera Photos')
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, width='stretch', caption=f'Photo {idx+1}')

    has_photos = bool(st.session_state.attendance_images)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button('Clear all photos', width='stretch', type='tertiary', icon=':material/delete:', disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()

    with c2:
        if st.button('Run Face Recognition', width='stretch', type='secondary', icon=':material/analytics:', disabled=not has_photos):
            with st.spinner('Deep scanning office entrance photos...'):
                all_detected_ids = {}

                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    detected, _, _ = predict_attendance(img_np)

                    if detected:
                        for sid in detected.keys():
                            employee_id = int(sid)
                            all_detected_ids.setdefault(employee_id, []).append(f"Photo {idx+1}")

                enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', selected_dept_id).execute()
                enrolled_employees = enrolled_res.data

                if not enrolled_employees:
                    st.warning('⚠️ No employees enrolled in this department yet! Please have staff join before scanning.')
                else:
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    try:
                        existing_today_res = supabase.table('attendance_logs') \
                            .select('*') \
                            .eq('subject_id', selected_dept_id) \
                            .gte('timestamp', f"{today_str}T00:00:00") \
                            .lte('timestamp', f"{today_str}T23:59:59") \
                            .execute()
                        existing_today_map = {
                            l['student_id']: l for l in (existing_today_res.data or [])
                        }
                    except Exception:
                        existing_today_map = {}

                    results, attendance_to_log = [], []
                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                    for node in enrolled_employees:
                        employee = node['students']
                        sid = int(employee['student_id'])
                        sources = all_detected_ids.get(sid, [])
                        detected_in_photo = len(sources) > 0

                        existing_rec = existing_today_map.get(sid)
                        already_present = bool(existing_rec and existing_rec.get('is_present'))

                        if already_present:
                            ts_val = existing_rec.get('timestamp', '')
                            clock_time = ts_val.split('T')[1][:5] if 'T' in ts_val else ''
                            time_badge = f" ({clock_time})" if clock_time else ""

                            if detected_in_photo:
                                verif_source = f"Clocked in earlier + Verified in {', '.join(sources)}"
                            else:
                                verif_source = "Clocked In via Profile / Earlier Scan"
                            
                            status_text = f"✅ Already Clocked In{time_badge}"
                        elif detected_in_photo:
                            verif_source = f"Entrance Kiosk ({', '.join(sources)})"
                            status_text = "✅ Clocked In (Now)"
                            attendance_to_log.append({
                                'student_id': sid,
                                'subject_id': selected_dept_id,
                                'timestamp': current_timestamp,
                                'is_present': True
                            })
                        else:
                            verif_source = "-"
                            status_text = "❌ Not Clocked In"
                            attendance_to_log.append({
                                'student_id': sid,
                                'subject_id': selected_dept_id,
                                'timestamp': current_timestamp,
                                'is_present': False
                            })

                        results.append({
                            "Employee Name": employee['name'],
                            "Employee ID": f"EMP-{employee['student_id']:03d}",
                            "Status": status_text,
                            "Verification Source": verif_source
                        })

                    attendance_result_dialog(pd.DataFrame(results), attendance_to_log)

    with c3:
        if st.button('Use Voice Clock-In', type='primary', width='stretch', icon=':material/mic:'):
            voice_attendance_dialog(selected_dept_id)


def hr_tab_manage_departments():
    hr_data = st.session_state.get('hr_data') or st.session_state.get('teacher_data')
    hr_id = hr_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.header('Departments & Teams', width='stretch')
        st.caption("Manage company departments, shifts, and team assignments")

    with col2:
        if st.button('Create New Department', type='primary', width='stretch', icon=':material/add_circle:'):
            create_department_dialog(hr_id)

    st.divider()

    # List all Departments
    departments = get_hr_departments(hr_id)
    if departments:
        cols = st.columns(2)
        for i, sub in enumerate(departments):
            stats = [
                ("👥", "Staff", sub['total_students']),
                ("📅", "Days Logged", sub['total_classes']),
            ]

            def make_footer(current_sub):
                def footer():
                    if st.button("👥 View Department Staff & Records", key=f"view_st_{current_sub['subject_id']}", type="primary", width='stretch', icon=":material/group:"):
                        view_department_staff_dialog(current_sub['subject_id'], current_sub['name'], current_sub['subject_code'], current_sub['section'])

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button(f"Share Code", key=f"share_{current_sub['subject_id']}", icon=":material/share:", width='stretch'):
                            share_department_dialog(current_sub['name'], current_sub['subject_code'])
                    with b2:
                        if st.button(f"Delete", key=f"del_{current_sub['subject_id']}", icon=":material/delete_forever:", type="tertiary", width='stretch'):
                            del_res = delete_department(current_sub['subject_id'])
                            if del_res is not None:
                                st.toast(f"Department '{current_sub['name']}' deleted!")
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to delete department. Please try again.")
                return footer

            with cols[i % 2]:
                department_card(
                    name=sub['name'],
                    code=sub['subject_code'],
                    section=sub['section'],
                    stats=stats,
                    footer_callback=make_footer(sub)
                )
    else:
        st.info("No departments created yet. Click 'Create New Department' above to get started.")


def hr_tab_timesheet_records():
    st.header('Workforce Timesheets & Attendance Records')
    st.caption("Daily clock-in & checkout logs and attendance analytics across all departments")

    hr_data = st.session_state.get('hr_data') or st.session_state.get('teacher_data')
    hr_id = hr_data['teacher_id']
    records = get_attendance_for_hr(hr_id)

    if not records:
        st.info("No attendance records logged yet.")
        return

    # Build detailed employee records with Check-in and Checkout timestamps
    detailed_data = []
    for r in records:
        ts = r.get('timestamp')
        clock_out = r.get('clock_out')
        st_info = r.get('students') or {}
        sub_info = r.get('subjects') or {}

        # Format Check-in time
        if ts:
            try:
                date_str = datetime.fromisoformat(ts).strftime("%Y-%m-%d")
                check_in_str = datetime.fromisoformat(ts).strftime("%I:%M %p")
            except Exception:
                date_str = ts[:10]
                check_in_str = ts[11:16]
        else:
            date_str = "N/A"
            check_in_str = "-"

        # Format Checkout time
        emp_id = st_info.get('student_id', r.get('student_id'))
        session_out = st.session_state.get(f"clock_out_{emp_id}_{date_str}")
        if clock_out:
            try:
                check_out_str = datetime.fromisoformat(clock_out).strftime("%I:%M %p")
            except Exception:
                check_out_str = str(clock_out)
        elif session_out:
            check_out_str = session_out
        elif r.get('is_present'):
            check_out_str = "⏳ On Duty (Not yet checked out)"
        else:
            check_out_str = "-"

        detailed_data.append({
            "Date": date_str,
            "Employee ID": f"EMP-{emp_id:03d}" if emp_id else "-",
            "Employee Name": st_info.get('name', 'Unknown'),
            "Department": f"{sub_info.get('name', '')} ({sub_info.get('section', '')})",
            "Check-In Time": check_in_str,
            "Checkout Time": check_out_str,
            "Status": "✅ Present" if r.get('is_present') else "❌ Absent"
        })

    detail_df = pd.DataFrame(detailed_data)

    view_mode = st.radio(
        "Select Timesheet View:",
        options=["📋 Detailed Employee Logs (Check-In & Checkout)", "📊 Department Summary"],
        horizontal=True
    )

    if view_mode.startswith("📋"):
        st.subheader("Employee Check-In & Checkout Timesheet")
        # Search / filter by name
        search_kw = st.text_input("🔍 Filter by employee name or ID", placeholder="e.g. ravikant...")
        filtered_df = detail_df
        if search_kw.strip():
            kw = search_kw.strip().lower()
            filtered_df = detail_df[
                detail_df['Employee Name'].str.lower().str.contains(kw) |
                detail_df['Employee ID'].str.lower().str.contains(kw)
            ]

        st.dataframe(filtered_df, width='stretch', hide_index=True)

        csv_bytes = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Detailed Timesheet (CSV)",
            data=csv_bytes,
            file_name=f"employee_timesheet_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            icon=":material/download:"
        )

    else:
        st.subheader("Department Attendance Summary")
        summary = (
            detail_df.groupby(['Date', 'Department'])
            .agg(
                Present_Count=('Status', lambda x: (x == "✅ Present").sum()),
                Total_Count=('Status', 'count')
            ).reset_index()
        )
        summary['Presence Stats'] = (
            "✅ " + summary['Present_Count'].astype(str) + " / "
            + summary['Total_Count'].astype(str) + ' Staff Present'
        )
        display_summary = summary[['Date', 'Department', 'Presence Stats']]
        st.dataframe(display_summary, width='stretch', hide_index=True)

        csv_bytes = display_summary.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Summary (CSV)",
            data=csv_bytes,
            file_name=f"department_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            icon=":material/download:"
        )


def login_hr(username, password):
    if not username or not password:
        return False
    
    hr_user = hr_login(username.strip(), password.strip())
    if hr_user:
        st.session_state.user_role = 'hr'
        st.session_state.teacher_data = hr_user
        st.session_state.hr_data = hr_user
        st.session_state.is_logged_in = True
        return True

    return False


def hr_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('HR / Manager Login', text_alignment='center')
    st.caption("Sign in to access reception kiosk and workforce records")
    st.space()
    st.space()

    hr_username = st.text_input("Enter username", placeholder='e.g. rohit12')
    hr_pass = st.text_input("Enter password", type='password', placeholder="Enter password")

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button('Login', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            if login_hr(hr_username, hr_pass):
                st.toast("Welcome back!", icon="👋")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username and password combination.")

    with btnc2:
        if st.button('Register Instead', type="primary", icon=':material/passkey:', width='stretch'):
            st.session_state.hr_login_type = 'register'
            st.rerun()

    st.space()
    if st.button('Forgot password? Reset here', type='tertiary', icon=':material/lock_reset:', width='stretch'):
        st.session_state.hr_login_type = 'forgot_password'
        st.rerun()

    footer_dashboard()


def hr_screen_forgot_password():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Reset your password', text_alignment='center')
    st.space()
    st.space()

    reset_username = st.text_input("Enter your registered username", placeholder='e.g. rohit12')
    reset_name = st.text_input("Enter your registered full name", placeholder='e.g. rohit')
    new_pass = st.text_input("Enter new password", type='password', placeholder="Enter new password")
    confirm_pass = st.text_input("Confirm new password", type='password', placeholder="Confirm new password")

    st.divider()

    btn1, btn2 = st.columns(2)

    with btn1:
        if st.button('Update Password', type='primary', icon=':material/lock_reset:', width='stretch'):
            u = reset_username.strip() if reset_username else ""
            n = reset_name.strip() if reset_name else ""
            p1 = new_pass.strip() if new_pass else ""
            p2 = confirm_pass.strip() if confirm_pass else ""

            if not u or not n or not p1 or not p2:
                st.error("All fields are required!")
            elif p1 != p2:
                st.error("Passwords do not match!")
            elif len(p1) < 4:
                st.error("Password should be at least 4 characters long.")
            else:
                success, msg = reset_hr_password(u, n, p1)
                if success:
                    st.success("Password successfully updated! Redirecting to login...")
                    import time
                    time.sleep(2)
                    st.session_state.hr_login_type = 'login'
                    st.rerun()
                else:
                    st.error(msg)

    with btn2:
        if st.button('Back to Login', type='secondary', icon=':material/arrow_back:', width='stretch'):
            st.session_state.hr_login_type = 'login'
            st.rerun()

    footer_dashboard()


def register_hr(hr_username, hr_name, hr_pass, hr_pass_confirm):
    hr_username = hr_username.strip() if hr_username else ""
    hr_name = hr_name.strip() if hr_name else ""
    hr_pass = hr_pass.strip() if hr_pass else ""
    hr_pass_confirm = hr_pass_confirm.strip() if hr_pass_confirm else ""

    if not hr_username or not hr_name or not hr_pass:
        return False, "All Fields are required!"
    if check_hr_exists(hr_username):
        return False, "Username already taken"
    if hr_pass != hr_pass_confirm:
        return False, "Password doesn't match"
    
    try:
        res = create_hr(hr_username, hr_pass, hr_name)
        if res:
            return True, "Successfully Created! Login Now"
        return False, "Database insertion failed"
    except Exception as e:
        return False, f"Unexpected Error: {e}"


def hr_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Register HR / Manager Profile')
    st.space()
    st.space()

    hr_username = st.text_input("Enter username", placeholder='e.g. rohit12')
    hr_name = st.text_input("Enter full name", placeholder='e.g. Rohit Kumar')
    hr_pass = st.text_input("Enter password", type='password', placeholder="Enter password")
    hr_pass_confirm = st.text_input("Confirm your password", type='password', placeholder="Confirm password")

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button('Register now', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            success, message = register_hr(hr_username, hr_name, hr_pass, hr_pass_confirm)
            if success:
                st.success(message)
                import time
                time.sleep(2)
                st.session_state.hr_login_type = "login"
                st.rerun()
            else:
                st.error(message)

    with btnc2:
        if st.button('Login Instead', type="primary", icon=':material/passkey:', width='stretch'):
            st.session_state.hr_login_type = 'login'
            st.rerun()

    footer_dashboard()


# Backwards compatibility aliases
teacher_screen = hr_screen
teacher_dashboard = hr_dashboard
teacher_tab_take_attendance = hr_tab_reception_kiosk
teacher_tab_manage_subjects = hr_tab_manage_departments
teacher_tab_attendance_records = hr_tab_timesheet_records
login_teacher = login_hr
teacher_screen_login = hr_screen_login
teacher_screen_forgot_password = hr_screen_forgot_password
register_teacher = register_hr
teacher_screen_register = hr_screen_register
