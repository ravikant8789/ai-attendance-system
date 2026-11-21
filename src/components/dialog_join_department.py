import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
import time


@st.dialog("Join Department / Team")
def join_department_dialog():
    st.write('Enter the Department Code provided by your HR or Manager:')
    join_code = st.text_input('Department Code', placeholder='e.g. ENG, SALES, DEV-101')

    if 'enroll_section_candidates' not in st.session_state:
        st.session_state.enroll_section_candidates = None

    if st.button('Search & Join', type='primary', width='stretch'):
        code = join_code.strip().upper() if join_code else ""
        if code:
            res = supabase.table('subjects').select('subject_id, name, subject_code, section').eq('subject_code', code).execute()
            if res.data:
                student_id = st.session_state.student_data['student_id']
                if len(res.data) == 1:
                    subject = res.data[0]
                    check = supabase.table('subject_students').select('*').eq('subject_id', subject['subject_id']).eq('student_id', student_id).execute()
                    if check.data:
                        st.warning(f"You are already assigned to **{subject['name']} ({subject['section']})**.")
                    else:
                        enroll_student_to_subject(student_id, subject['subject_id'])
                        st.success(f"🎉 Successfully joined **{subject['name']}** ({subject['section']})!")
                        time.sleep(1)
                        st.session_state.enroll_section_candidates = None
                        st.rerun()
                else:
                    st.session_state.enroll_section_candidates = res.data
                    st.rerun()
            else:
                st.error(f"⚠️ Department code **'{code}'** not found. Please verify with HR.")
        else:
            st.warning('Please enter a department code.')

    if st.session_state.get('enroll_section_candidates'):
        candidates = st.session_state.enroll_section_candidates
        st.divider()
        st.write("Multiple shifts/teams found for this code. Select yours:")
        sec_map = {f"{s['name']} - {s['section']}": s for s in candidates}
        selected_label = st.selectbox("Choose Shift / Team", options=list(sec_map.keys()))

        if st.button("Confirm Joining", type="primary", width="stretch"):
            selected_sub = sec_map[selected_label]
            student_id = st.session_state.student_data['student_id']
            check = supabase.table('subject_students').select('*').eq('subject_id', selected_sub['subject_id']).eq('student_id', student_id).execute()
            if check.data:
                st.warning(f"You are already assigned to **{selected_sub['name']} ({selected_sub['section']})**.")
            else:
                enroll_student_to_subject(student_id, selected_sub['subject_id'])
                st.success(f"🎉 Joined **{selected_sub['name']}** ({selected_sub['section']})!")
                time.sleep(1)
                st.session_state.enroll_section_candidates = None
                st.rerun()
