import streamlit as st
import segno
import io


@st.dialog("Share Department Onboarding Link")
def share_department_dialog(subject_name, subject_code):
    join_url = f"/?join-code={subject_code}"

    st.markdown(f"### 🏢 {subject_name}")
    st.caption("Share this code or QR code with employees to onboard them into this department")

    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=10, border=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('**Department Join Code**')
        st.code(subject_code, language="text")
        st.info('Share this code with employees via Slack, Teams, or Email.')

    with col2:
        st.markdown('**Scan to Join**')
        st.image(out.getvalue(), caption='QR Code for Department Onboarding')
