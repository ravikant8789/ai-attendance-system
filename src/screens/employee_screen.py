import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import (
    get_all_employees,
    create_employee,
    get_employee_departments,
    get_employee_attendance,
    remove_employee_from_department,
    create_attendance,
    record_clock_out
)
import time
from datetime import datetime

from src.components.dialog_join_department import join_department_dialog
from src.components.department_card import department_card


def employee_dashboard():
    employee_data = st.session_state.get('employee_data') or st.session_state.get('student_data')
    employee_id = employee_data['student_id']

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {employee_data['name']}""")
        st.caption(f"Employee ID: **EMP-{employee_id:03d}**")
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            st.session_state.pop('student_data', None)
            st.session_state.pop('employee_data', None)
            st.rerun()

    st.space()

    # Load assigned departments and attendance logs
    with st.spinner('Loading workplace data...'):
        departments = get_employee_departments(employee_id)
        logs = get_employee_attendance(employee_id)

    # Work Punch Section (Clock In / Clock Out)
    with st.container(border=True):
        st.subheader("⏱️ Daily Work Punch")
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Check if already clocked in today
        today_punches = [
            l for l in logs 
            if l.get('timestamp', '').startswith(today_str) and l.get('is_present')
        ]
        has_punched_today = len(today_punches) > 0

        # Check if already clocked out today
        clock_out_time = None
        has_clocked_out_today = False
        if has_punched_today:
            for p in today_punches:
                if p.get('clock_out'):
                    clock_out_time = p['clock_out'].split("T")[1][:5] if "T" in str(p['clock_out']) else str(p['clock_out'])
                    has_clocked_out_today = True
                    break
            if not has_clocked_out_today and st.session_state.get(f"clock_out_{employee_id}_{today_str}"):
                clock_out_time = st.session_state[f"clock_out_{employee_id}_{today_str}"]
                has_clocked_out_today = True

        p1, p2, p3 = st.columns([2, 1, 1], vertical_alignment="center")
        with p1:
            st.markdown(f"**Date:** {datetime.now().strftime('%A, %d %B %Y')}")
            if has_punched_today and has_clocked_out_today:
                first_punch_time = today_punches[0]['timestamp'].split("T")[1][:5]
                st.success(f"🟢 In: **{first_punch_time}** | 🔴 Out: **{clock_out_time}**")
            elif has_punched_today:
                first_punch_time = today_punches[0]['timestamp'].split("T")[1][:5]
                st.success(f"🟢 Clocked in today at **{first_punch_time}**")
            else:
                st.info("⚪ Not yet clocked in today")

        with p2:
            if has_punched_today:
                st.button("✅ Already Clocked In", disabled=True, width="stretch", icon=":material/check_circle:")
            else:
                if st.button("🟢 Clock In", type="primary", width="stretch", icon=":material/login:"):
                    current_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    if departments:
                        punch_records = [
                            {'student_id': employee_id, 'subject_id': sub_node['subjects']['subject_id'], 'timestamp': current_ts, 'is_present': True}
                            for sub_node in departments
                        ]
                        create_attendance(punch_records)
                        st.toast("✅ Clock-In recorded successfully! Have a great work day!")
                    else:
                        st.warning("Please join at least one department first so your attendance can be logged.")
                    time.sleep(1)
                    st.rerun()

        with p3:
            if not has_punched_today:
                st.button("🔴 Clock Out", disabled=True, width="stretch", icon=":material/logout:", help="You must clock in first before clocking out.")
            elif has_clocked_out_today:
                st.button("✅ Already Clocked Out", disabled=True, width="stretch", icon=":material/check_circle:")
            else:
                if st.button("🔴 Clock Out", type="secondary", width="stretch", icon=":material/logout:"):
                    record_clock_out(employee_id)
                    current_time_str = datetime.now().strftime("%I:%M %p")
                    st.session_state[f"clock_out_{employee_id}_{today_str}"] = current_time_str
                    st.toast(f"👋 Clock-Out recorded at {current_time_str}! Have a great evening!")
                    time.sleep(1)
                    st.rerun()

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.header('Your Departments & Teams')
    with c2:
        if st.button('Join Department / Team', type='primary', width='stretch', icon=':material/group_add:'):
            join_department_dialog()

    # Calculate attendance per unique calendar date
    stats_map = {}
    for log in logs:
        sid = log.get('subject_id')
        ts = log.get('timestamp', '')
        if not ts:
            continue
        date_str = ts[:10]
        if sid not in stats_map:
            stats_map[sid] = {"total_dates": set(), "attended_dates": set()}
        stats_map[sid]["total_dates"].add(date_str)
        if log.get('is_present'):
            stats_map[sid]["attended_dates"].add(date_str)

    if departments:
        cols = st.columns(2)
        for i, sub_node in enumerate(departments):
            sub = sub_node['subjects']
            sid = sub['subject_id']
            dept_stat = stats_map.get(sid, {"total_dates": set(), "attended_dates": set()})
            total_days = len(dept_stat["total_dates"])
            attended_days = len(dept_stat["attended_dates"])

            def make_unenroll_button(current_sub):
                current_sid = current_sub['subject_id']
                def unenroll_button():
                    if st.button("Leave this Department", key=f"unenroll_{current_sid}", type='tertiary', width='stretch', icon=':material/delete_forever:'):
                        remove_employee_from_department(employee_id, current_sid)
                        st.toast(f"Left {current_sub['name']} successfully!")
                        time.sleep(1)
                        st.rerun()
                return unenroll_button

            with cols[i % 2]:
                department_card(
                    name=sub['name'],
                    code=sub['subject_code'],
                    section=sub['section'],
                    stats=[
                        ('📅', 'Work Days', total_days),
                        ('✅', 'Present', attended_days),
                    ],
                    footer_callback=make_unenroll_button(sub)
                )
    else:
        st.info("You haven't joined any departments yet. Click 'Join Department / Team' above to get started.")

    footer_dashboard()


def employee_screen():
    style_background_dashboard()
    style_base_layout()

    if "employee_data" in st.session_state or "student_data" in st.session_state:
        employee_dashboard()
        return
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Employee FaceID Clock-In / Login', text_alignment='center')
    st.caption("Look directly at the camera to verify your identity")
    st.space()
    st.space()
    
    show_registration = False
    photo_source = st.camera_input("Position your face in the frame")

    if photo_source:
        img = np.array(Image.open(photo_source))

        with st.spinner('Verifying identity...'):
            try:
                detected, all_ids, num_faces = predict_attendance(img)
            except Exception as e:
                st.warning("⚠️ Network connection blip while connecting to database. Retrying...")
                detected, all_ids, num_faces = {}, [], 0

            if num_faces == 0:
                st.warning('No face detected! Please ensure proper lighting and face the camera.')
            elif num_faces > 1:
                st.warning('Multiple faces detected! Please ensure only one employee is in the frame.')
            else:
                if detected:
                    employee_id = list(detected.keys())[0]
                    all_employees = get_all_employees()
                    employee = next((s for s in all_employees if s['student_id'] == employee_id), None)

                    if employee:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'employee'
                        st.session_state.student_data = employee
                        st.session_state.employee_data = employee
                        st.toast(f"Welcome Back, {employee['name']}!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info('Face not recognized! If you are a new employee, please register below:')
                    show_registration = True

    if show_registration:
        with st.container(border=True):
            st.header('Register New Employee Profile')
            new_name = st.text_input("Enter employee full name", placeholder='e.g. Rohit Kumar')

            st.subheader('Optional : Voice Clock-In Setup')
            st.info("Record a short voice sample to enable voice-based punch-in:")

            audio_data = None
            try:
                audio_data = st.audio_input('Say: "Hello, I am present today."')
            except Exception:
                st.error('Microphone input failed!')

            if st.button('Create Employee Profile', type='primary', width='stretch'):
                if new_name.strip():
                    with st.spinner('Creating employee profile...'):
                        img = np.array(Image.open(photo_source))
                        encodings = get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            voice_emb = None
                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_employee(new_name.strip(), face_embedding=face_emb, voice_embedding=voice_emb)

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'employee'
                                st.session_state.student_data = response_data[0]
                                st.session_state.employee_data = response_data[0]
                                st.toast(f'Employee Profile Created! Welcome {new_name}!')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error('Could not capture facial features for registration. Please try again.')
                else:
                    st.warning('Please enter your full name!')

    footer_dashboard()


# Backwards compatibility alias
student_screen = employee_screen
student_dashboard = employee_dashboard
