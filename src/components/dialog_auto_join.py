import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
import time


@st.dialog("Quick Department Onboarding")
def auto_join_dialog(subject_code):
    student_id = st.session_state.student_data['student_id']

    res = supabase.table('subjects').select('subject_id, name, section').eq('subject_code', subject_code).execute()
    if not res.data:
        st.error('Department Code not found!')
        if st.button('Close'):
            st.query_params.clear()
            st.rerun()
        return

    if len(res.data) == 1:
        subject = res.data[0]
    else:
        st.write("Multiple shifts/teams found. Please select yours:")
        sec_options = {f"{s['name']} (Shift: {s['section']})": s for s in res.data}
        chosen = st.selectbox("Shift / Team", options=list(sec_options.keys()))
        subject = sec_options[chosen]

    check = supabase.table('subject_students').select('*').eq('subject_id', subject['subject_id']).eq('student_id', student_id).execute()
    if check.data:
        st.info(f"You are already a member of **{subject['name']} (Shift: {subject['section']})**!")
        if st.button('Got it!'):
            st.query_params.clear()
            st.rerun()
        return

    st.markdown(f"Would you like to join **{subject['name']}** (Shift: {subject['section']})?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button('No thanks'):
            st.query_params.clear()
            st.rerun()
    with col2:
        if st.button('Yes, join now!', type='primary', width='stretch'):
            enroll_student_to_subject(student_id, subject['subject_id'])
            st.success('Joined department successfully!')
            st.query_params.clear()
            time.sleep(2)
            st.rerun()
