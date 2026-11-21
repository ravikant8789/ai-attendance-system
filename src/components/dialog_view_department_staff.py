import streamlit as st
import pandas as pd
from src.database.db import get_subject_students_with_records, unenroll_student_to_subject
import time


@st.dialog("Department Staff & Attendance Records")
def view_department_staff_dialog(subject_id, subject_name, subject_code, section):
    st.markdown(f"### 🏢 {subject_name}")
    st.caption(f"Dept Code: **{subject_code}** | Shift / Team: **{section}**")

    students, total_classes = get_subject_students_with_records(subject_id)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Enrolled Staff", len(students))
    with col2:
        st.metric("Total Days Logged", total_classes)

    st.divider()

    if not students:
        st.info("ℹ️ No employees are currently enrolled in this department.")
        st.write("Share the department code with your staff to onboard them:")
        st.code(subject_code, language="text")
        return

    st.subheader("👥 Department Employee Roster")

    # Search filter
    search_query = st.text_input("🔍 Search employee by name or ID", placeholder="Type name or ID...")

    filtered_students = students
    if search_query:
        q = search_query.strip().lower()
        filtered_students = [
            s for s in students 
            if q in str(s['student_id']).lower() or q in s['name'].lower()
        ]

    # Build DataFrame for clean presentation
    table_data = []
    for s in filtered_students:
        table_data.append({
            "Employee ID": f"EMP-{s['student_id']:03d}",
            "Employee Name": s["name"],
            "Days Present": f"{s['attended']} / {total_classes}",
            "Attendance Rate": s["percentage"]
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True, width="stretch")

    # Manage enrollments (Option to remove an employee via search)
    with st.expander("⚙️ Remove Employee from Department"):
        st.write("Search for an employee by name to remove them from this department:")
        remove_search = st.text_input("Search employee to remove", placeholder="Type employee name (e.g. ravikant)...", key="remove_student_search")

        if remove_search.strip():
            query = remove_search.strip().lower()
            matched_to_remove = [
                s for s in students 
                if query in s['name'].lower() or query == str(s['student_id'])
            ]

            if not matched_to_remove:
                st.warning(f"No enrolled employee found matching '{remove_search}'.")
            else:
                for target_st in matched_to_remove:
                    r1, r2 = st.columns([3, 1], vertical_alignment="center")
                    with r1:
                        st.markdown(f"👤 **{target_st['name']}** *(EMP-{target_st['student_id']:03d})*")
                    with r2:
                        if st.button("Remove", key=f"btn_remove_{target_st['student_id']}", type="tertiary", icon=":material/delete:"):
                            unenroll_student_to_subject(target_st['student_id'], subject_id)
                            st.toast(f"Removed {target_st['name']} from {subject_name}!")
                            time.sleep(1)
                            st.rerun()
