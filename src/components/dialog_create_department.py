import streamlit as st
from src.database.db import create_subject
from src.database.config import supabase
import time


@st.dialog("Create New Department / Team")
def create_department_dialog(teacher_id):
    st.write("Enter details for the new department or team:")
    sub_id = st.text_input("Department Code", placeholder="e.g. ENG, SALES, DEV-101")
    sub_name = st.text_input("Department Name", placeholder="e.g. Software Engineering")
    sub_section = st.text_input("Shift / Team", placeholder="e.g. General Shift, Team Alpha")

    if st.button("Create Department Now", type='primary', width='stretch'):
        clean_code = sub_id.strip().upper() if sub_id else ""
        clean_name = sub_name.strip() if sub_name else ""
        clean_section = sub_section.strip() if sub_section else ""

        if clean_code and clean_name and clean_section:
            try:
                check = supabase.table("subjects").select("subject_code, section").eq("subject_code", clean_code).eq("section", clean_section).execute()
                if check.data:
                    st.error(f"⚠️ Department **'{clean_code}' ({clean_section})** already exists! Please choose a different code or shift.")
                    return
            except Exception:
                pass

            try:
                res = create_subject(clean_code, clean_name, clean_section, teacher_id)
                if res:
                    st.toast("🎉 Department created successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to create department. Please try again.")
            except Exception as e:
                err_str = str(e)
                if "subjects_subject_code_key" in err_str:
                    st.error(f"⚠️ Department code **'{clean_code}'** is already taken. Please use a distinct code (e.g. **'{clean_code}-{clean_section}'**).")
                elif "subjects_code_section_unique" in err_str or "already exists" in err_str:
                    st.error(f"⚠️ Department **'{clean_code}' ({clean_section})** already exists!")
                else:
                    st.error("Unable to create department. Please try again.")
        else:
            st.warning("Please fill in all the fields.")
