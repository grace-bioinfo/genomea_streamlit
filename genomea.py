import os
import tempfile
import hmac
from Bio import SeqIO
import streamlit as st
# Show loading state
with st.spinner("Loading GenomEA..."):
    # Heavy imports inside here
    from pipeline import run_pipeline, get_sequence, detect_sequence_type
    from dotenv import load_dotenv
    load_dotenv()


# LOGIN

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter access password", type="password")
    expected_password = os.environ.get("APP_PASSWORD")

    if not password:
        st.stop()

    if hmac.compare_digest(password, expected_password or ""):
        st.session_state.authenticated = True
        st.rerun()
        
    else:
        st.error("Incorrect password")
        st.stop()

st.success("Access granted")

# add your title
st.set_page_config(

    page_title = "GenomEA",
    layout = "wide",
    page_icon= "genomea_logo.png"
)

st.title("GenomEA")

st.markdown("### Genomic analysis for East Africa")
st.divider()
st.write("GenomEA is a bioinformatics platform built for East African researchers. Upload your protein sequence and get a complete analysis; BLAST search, sequence alignment, phylogenetic tree, domain annotation and an AI-powered summary grounded in East African genomics research. Built on local data, for local science. Starting in Kenya and scaling across the continent.")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div style="background-color:#253347; padding:20px; border-radius:5px; height:180px">
            <h3>BLAST Search</h3>
            <p>Find similar sequences across species and databases.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style="background-color:#253347; padding:20px; border-radius:5px; height:180px">
            <h3>Sequence Alignment</h3>
            <p>Align multiple sequences to identify conserved regions.</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div style="background-color:#253347; padding:20px; border-radius:5px; height:180px">
            <h3>Domain Annotation</h3>
            <p>Identify functional domains and biological significance.</p>
        </div>
    """, unsafe_allow_html=True)


st.divider()

st.header("Analyze Your Sequence")
# sequence input

input_method = st.radio("Input method", ["Paste sequence", "Upload file"])

if input_method == "Paste sequence":
    sequence = st.text_area("Paste your sequence here", height = 150)
else:
    uploaded_file = st.file_uploader("Upload file", type=["fasta", "fa", "fastq", "gb", "gbk", "gp"])

    if uploaded_file:
    # Check file size (limit to 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            st.error("File too large! Maximum file size is 5MB.")
            uploaded_file = None
        else:
            st.success("File uploaded successfully!")

# analysis type selector
analysis_type = st.selectbox(
    "Select Analysis Type",
    ["All", "BLAST Search", "Alignment", "Phylogenetic Tree", "Identity Matrix", "Domain Annotation"]
)

# submit button
if input_method == "Upload file" and uploaded_file:
    # auto detect sequence type before button is clicked
    original_ext = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=original_ext) as tmp:
        tmp.write(uploaded_file.getvalue())
        temp_path = tmp.name

    sequence, seq_id, description = get_sequence(temp_path, input_type="file")
    seq_type = detect_sequence_type(sequence)
    default_program = "blastn" if seq_type == "nucleotide" else "blastp"

    program = st.selectbox(
        "BLAST Program",
        ["blastn", "blastp", "blastx", "tblastn", "tblastx"],
        index=["blastn", "blastp", "blastx", "tblastn", "tblastx"].index(default_program)
    )

    st.info(f"Detected: {seq_type} sequence → {default_program} selected")

elif input_method == "Paste sequence" and sequence:
    seq_type = detect_sequence_type(sequence)
    default_program = "blastn" if seq_type == "nucleotide" else "blastp"

    program = st.selectbox(
        "BLAST Program",
        ["blastn", "blastp", "blastx", "tblastn", "tblastx"],
        index=["blastn", "blastp", "blastx", "tblastn", "tblastx"].index(default_program)
    )

    st.info(f"Detected: {seq_type} sequence → {default_program} selected")

if st.button("Analyze", key="analyze_btn"):
    with st.spinner("GenomEA is analysing your sequence... this may take a while"):

        if input_method == "Upload file" and uploaded_file:
            results = run_pipeline(temp_path, input_type="file", program=program)
            st.session_state.results = results
            st.success("Analysis complete! Please go to Results page.")

        elif input_method == "Paste sequence" and sequence:
            results = run_pipeline(sequence, input_type="text", program=program)
            st.session_state.results = results
            st.success("Analysis complete! Please go to Results page.")

        else:
            st.error("Please provide a sequence!")


# add divider and results header- this was a place holder and we no longer need it
# st.divider()
# st.header("Results")
# st.write("Your results will appear here after analysis.")

# add sidebar
with st.sidebar:
    st.title("GenomEA")
    st.write("Navigation")
    st.markdown("- Home")
    st.markdown("- Analysis")
    st.markdown("- About")
    st.divider()
    st.write("Decode")


    

