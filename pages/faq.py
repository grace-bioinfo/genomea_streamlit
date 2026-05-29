import streamlit as st

st.set_page_config(page_title="FAQ - GenomEA")

st.title("Getting started ?")
st.divider()

with st.expander("How long does analysis take?"):
    st.write("A full analysis typically takes 4-6 minutes depending on server load. BLAST also contributes to this as NCBI is a large database. Please keep the page open until complete.")

with st.expander("What sequence types does GenomEA support?"):
    st.write("GenomEA currently supports protein sequences only in FASTA or GenBank format. For nucleotide sequences, convert to protein first using a translation tool like ExPASy Translate.")

with st.expander("Are my results saved?"):
    st.write("Results are session-based only — they are not permanently stored. Please download your results before closing the page.")

with st.expander("Which file formats can I download?"):
    st.write("BLAST results → CSV | Alignment → FASTA | Phylogenetic tree → .ph | Identity matrix → .pim | Domain annotation → JSON | AI Summary → TXT")

with st.expander("What databases does GenomEA use?"):
    st.write("GenomEA uses NCBI for BLAST searches, Clustal Omega (EBI) for alignment, UniProt for domain annotation and NVIDIA Llama for AI summaries.")

with st.expander("Is GenomEA free?"):
    st.write("Yes! GenomEA is currently free for all East African researchers and students.")

with st.expander("My analysis failed. What should I do?"):
    st.write("Check that your sequence is a valid protein sequence in FASTA format. If the error persists, try again — NCBI servers occasionally time out. Contact us at gracekagendonyaga@gmail.com if the issue continues.")

with st.expander("Can I use GenomEA results in my research?"):
    st.write("Yes! Please cite the tools used: NCBI BLAST, Clustal Omega(EMBL/EBI), UniProt and GenomEA in your publications.")