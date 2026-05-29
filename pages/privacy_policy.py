import streamlit as st

st.set_page_config(page_title="Privacy Policy - GenomEA", page_icon="🔒")

st.title("Privacy Policy 🔒")
st.write("Last updated: May 2026")
st.divider()

st.write("""
GenomEA collects only the minimum information necessary to provide its services. 
By using GenomEA, you agree to the terms outlined in this policy.
""")

st.header("1. Information We Collect")
st.write("GenomEA collects only sequence data submitted for analysis, uploaded files and anonymous usage data. We do not collect personal identifiers.")

st.header("2. How We Use Your Information")
st.write("Information is used exclusively for running analysis, generating AI summaries and improving the platform. We do not sell or share your data.")

st.header("3. Research Disclaimer")
st.error("Results from GenomEA are for research purposes only and should not be used for clinical diagnosis or medical decision-making.")

st.header("4. Contact")
st.write("For questions contact: gracekagendonyaga@gmail.com")
st.write("GitHub: github.com/grace-bioinfo")