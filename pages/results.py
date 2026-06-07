import streamlit as st
import pandas as pd
import json
import os

with st.spinner("Result page loading..."):
    from pipeline import ai_summary

st.title("Results")
st.write("Your analysis results will appear here.")
# check if results exist

if "results" not in st.session_state:
    st.warning("No results yet. Please go to the main page and run an analysis.")
else:
    results = st.session_state.results

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "AI Summary",
        "BLAST Results",
        "Homologs",
        "Alignment",
        "Phylogenetic Tree",
        "Identity Matrix",
        "Domain Annotation"
    ])


    with tab1:
        st.subheader("AI Summary")
        st.write(results["ai_summary"])

    with tab2:
        st.subheader("BLAST Results")
        st.dataframe(results["blast_results"])
        df = pd.DataFrame(results["blast_results"])
        st.download_button(
            "Download BLAST results",
            df.to_csv(index=False),
            "blast_results.csv"
        )


    

    with tab3:
        st.subheader("Homolog Sequences")
    
        if not results["homologs"] or not os.path.exists(results["homologs"]):
            st.warning("Homolog sequences unavailable — check logs for details.")
        else:
            with open(results["homologs"]) as f:
                st.code(f.read()[:1000])

            st.download_button(
                "Download Homologs (complete file)",
                open(results["homologs"]).read(),
                "homologs.fasta"
            )


    with tab4:
        st.subheader("Aligned Sequences")
        with open(results["alignment"]) as f:
            st.code(f.read())
        st.download_button("Download Alignment", open(results["alignment"]).read(), "aligned_sequences.fasta")

    with tab5:
        st.subheader("Phylogenetic Tree")
        with open(results["tree"]) as f:
            st.code(f.read())
        st.download_button("Download tree", open(results["tree"]).read(), "phylogenetic_tree.ph")

    with tab6:
        st.subheader("Percent Identity Matrix")
        with open(results["pim"]) as f:
            st.code(f.read())
        st.download_button("Download matrix", open(results["pim"]).read(), "percent_identity.pim")

    with tab7:
        st.subheader("Domain Annotation")
        st.json(results["domains"])
        st.download_button(
            "Download domain annotation",
            json.dumps(results["domains"], indent=2),
            "domain_annotation.json"
        )



st.divider()
st.subheader("Ask GenomEA AI")
st.caption("Ask questions about your results in the context of East African genomics")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your results..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ai_summary("", [], [], question=prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
