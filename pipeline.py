import os
import json
import time
import uuid


from Bio import Entrez, SeqIO
from Bio.Blast import NCBIWWW, NCBIXML
from openai import OpenAI
import requests
from dotenv import load_dotenv
import logging 
import streamlit as st


load_dotenv()

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

Entrez.email=os.environ.get("ENTREZ_MY_EMAIL")


# STEP 1
@st.cache_data
def get_sequence(input_data, input_type="text", file_format="fasta"):
        
        if input_type == "file":
            record = list(SeqIO.parse(input_data, file_format))
    
            if len(record) == 0:
                 raise ValueError("No sequences found in the file.")
            record = record[0]
            return str(record.seq), record.id, record.description
    
        else:
            return input_data, "unknown", "user input sequence"
    



@st.cache_data
def run_blast(sequence, program="blastp", database="nr"):
    logger.info(f"BLAST started | program: {program} | database: {database}")
    
    try:
        blast_process = NCBIWWW.qblast(
        program=program,
        database=database,
        sequence=sequence
    )
    
        with open("blast_results.xml", "w") as f:
            f.write(blast_process.read())
    
        logger.info("BLAST complete")
        return "blast_results.xml"
    except Exception as e:
        logger.error(f"BLAST failed | program: {program} | database: {database} | {e}")
        return None




@st.cache_data
def filter_results(blast_file, evalue_threshold=0.05, identity_threshold=95):
    logger.info(f"Filtering started | file: {blast_file} | evalue threshold: {evalue_threshold} | identity threshold: {identity_threshold}%")
    filtered = []
    
    try:
        with open(blast_file) as f:
            blast_records = list(NCBIXML.parse(f))
    
        for blast_record in blast_records:
            for alignment in blast_record.alignments:
                for hsp in alignment.hsps:
                    identity_percent = (hsp.identities / hsp.align_length) * 100
                    if hsp.expect < evalue_threshold and identity_percent > identity_threshold:
                        filtered.append({
                            "title": alignment.title,
                            "accession": alignment.accession,
                            "score": hsp.score,
                            "evalue": hsp.expect,
                            "identity_percent": round(identity_percent, 2),
                            "gaps": hsp.gaps
                        })
    # Save filtered results to file
        with open("filtered_summary.txt", "w") as f:
            f.write("FILTERED BLAST RESULTS SUMMARY\n")
            f.write("=" * 40 + "\n")
            f.write("Total significant hits: " + str(len(filtered)) + "\n\n")
    
            for hit in filtered:
                f.write("Title: " + hit["title"] + "\n")
                f.write("Accession: " + hit["accession"] + "\n")
                f.write("Score: " + str(hit["score"]) + "\n")
                f.write("E-value: " + str(hit["evalue"]) + "\n")
                f.write("Identity %: " + str(hit["identity_percent"]) + "\n")
                f.write("Gaps: " + str(hit["gaps"]) + "\n")
                f.write("-" * 40 + "\n")

        if len(filtered) == 0:
            logger.warning(f"Filtering complete but no hits passed thresholds | file: {blast_file}")

        else:
            logger.info(f"Filtering complete | {len(filtered)}")

        return filtered
    except FileNotFoundError as e:
        logger.error(f"BLAST file not found: {blast_file} | {e}")
        return []
    except Exception as e:
        logger.error(f"Filtering failed | file: {blast_file} | {e}")
        return []





@st.cache_data
def fetch_homologs(filtered_results):
    logger.info(f"Fetching homologs started | {len(filtered_results)}")
    
    try:
        ids = [hit["accession"] for hit in filtered_results]

        if len(ids) == 0:
            logger.warning("fetch_homologs called, no ids to fetch")
            return None
        
        handle = Entrez.efetch(
            db="protein",
            id=ids,
            rettype="fasta",
            retmode="text"
        )
    
        with open("homologs.fasta", "w") as f:
            f.write(handle.read())

        logger.info(f"Homologs fetched and saved | {len(ids)} sequences | file: homologs.fasta")
        return "homologs.fasta"
    except Exception as e:
        logger.error(f"Fetching homologs failed | {len(ids)} IDs attempted | {e}")
        return None





@st.cache_data
def run_alignment(homologs_file):
    logger.info(f"Alignment started | file: {homologs_file}")  # moment 1

    try:
        with open(homologs_file) as f:
            fasta_data = f.read()

        response = requests.post(
            "https://www.ebi.ac.uk/Tools/services/rest/clustalo/run",
            data={
                "email": os.environ.get("ENTREZ_MY_EMAIL"),
                "sequence": fasta_data,
                "format": "fasta"
            },
            verify=False
        )

        job_id = response.text
        logger.info(f"Alignment job submitted | job_id: {job_id}")

        # Wait for job to finish
        while True:
            status = requests.get(
                "https://www.ebi.ac.uk/Tools/services/rest/clustalo/status/" + job_id,
                verify=False
            )
            logger.info(f"Alignment status | job_id: {job_id} | status: {status.text}")

            if status.text == "FINISHED":
                break
            elif status.text == "FAILED":
                logger.error(f"Alignment job failed on EBI side | job_id: {job_id}")
                return None, None, None

            time.sleep(10)

        # Fetch results
        alignment = requests.get(
            "https://www.ebi.ac.uk/Tools/services/rest/clustalo/result/" + job_id + "/fa",
            verify=False
        )
        tree = requests.get(
            "https://www.ebi.ac.uk/Tools/services/rest/clustalo/result/" + job_id + "/phylotree",
            verify=False
        )
        pim = requests.get(
            "https://www.ebi.ac.uk/Tools/services/rest/clustalo/result/" + job_id + "/pim",
            verify=False
        )

        with open("aligned_sequences.fasta", "w") as f:
            f.write(alignment.text)
        with open("phylogenetic_tree.ph", "w") as f:
            f.write(tree.text)
        with open("percent_identity.pim", "w") as f:
            f.write(pim.text)

        logger.info(f"Alignment complete | job_id: {job_id} | files saved: aligned_sequences.fasta, phylogenetic_tree.ph, percent_identity.pim")  # moment 2
        return "aligned_sequences.fasta", "phylogenetic_tree.ph", "percent_identity.pim"

    except FileNotFoundError as e:
        logger.error(f"Homologs file not found: {homologs_file} | {e}")  # moment 3
        return None, None, None

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not reach EBI ClustalOmega | {e}")
        return None, None, None

    except Exception as e:
        logger.error(f"Alignment failed | file: {homologs_file} | {e}")
        return None, None, None





@st.cache_data
def annotate_domains(uniprot_id):
    logger.info(f"Domain annotation started | uniprot_id: {uniprot_id}")  # moment 1

    try:
        url = "https://rest.uniprot.org/uniprotkb/" + uniprot_id + ".json"
        response = requests.get(url, verify=False)

        if response.status_code != 200:
            logger.error(f"UniProt request failed | uniprot_id: {uniprot_id} | status code: {response.status_code}")
            return []

        data = response.json()

        with open("domain_annotation.json", "w") as f:
            json.dump(data, f)

        # Extract key info
        domains = []
        if "features" in data:
            for feature in data["features"]:
                if feature["type"] in ["Domain", "Region", "Binding site", "Active site"]:
                    domains.append({
                        "type": feature["type"],
                        "description": feature.get("description", ""),
                        "start": feature["location"]["start"]["value"],
                        "end": feature["location"]["end"]["value"]
                    })

        if len(domains) == 0:
            logger.warning(f"No domains found | uniprot_id: {uniprot_id}")
        else:
            logger.info(f"Domain annotation complete | uniprot_id: {uniprot_id} | domains found: {len(domains)}")  # moment 2

        return domains

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not reach UniProt | uniprot_id: {uniprot_id} | {e}")  # moment 3
        return []

    except KeyError as e:
        logger.error(f"Unexpected UniProt response structure | uniprot_id: {uniprot_id} | missing key: {e}")
        return []

    except Exception as e:
        logger.error(f"Domain annotation failed | uniprot_id: {uniprot_id} | {e}")
        return []



#  AI summary
@st.cache_data
def ai_summary(sequence, blast_results, domains, question="Summarize these genomic analysis results in the context of East African research."):
    NVIDIA_KEY=os.environ.get("GKN_NVIDIA_KEY")
    # Format results for AI

    nvidia_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_KEY
    )

    blast_summary = json.dumps(blast_results[:5], indent=2)
    domain_summary = json.dumps(domains, indent=2)
    
    prompt = f"""
    Sequence Analysis Results:
    
    Top BLAST hits:
    {blast_summary}
    
    Protein domains:
    {domain_summary}
    
    Question: {question}
    """
    
    completion = nvidia_client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": "You are GenomEA, an AI assistant specializing in East African genomics research."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
        stream=False
    )
    
    return completion.choices[0].message.content

def run_pipeline(input_data, input_type="text", file_format="fasta", uniprot_id="P51587"):
    print("Starting GenomEA pipeline...")
    
    # Generate unique ID for this session
    session_id = str(uuid.uuid4())[:8]
    
    # All files get unique names
    blast_file = "blast_" + session_id + ".xml"
    filter_path = "filtered_" + session_id + ".txt"
    homologs_file = "homologs_" + session_id + ".fasta"
    alignment_file = "aligned_" + session_id + ".fasta"
    tree_file = "tree_" + session_id + ".ph"
    pim_file = "pim_" + session_id + ".pim"
    
    # Step 1
    
    sequence, seq_id, description = get_sequence(input_data, input_type, file_format)
    time.sleep(1)
    
    # Step 2
    blast_file = run_blast(sequence)
    time.sleep(2)
    
    # Step 3
    filtered = filter_results(blast_file)
    time.sleep(1)
    
    # Step 4
    homologs_file = fetch_homologs(filtered)
    time.sleep(2)
    
    # Step 5
    alignment_file, tree_file, pim_file = run_alignment(homologs_file)
    time.sleep(1)
    
    # Step 6
    domains = annotate_domains(uniprot_id)
    time.sleep(1)
    
    # Step 7
    summary = ai_summary(sequence, filtered, domains)
    
    print("Pipeline complete!")
    return {
        "sequence_id": seq_id,
        "blast_results": filtered,
        "homologs": homologs_file,
        "alignment": alignment_file,
        "tree": tree_file,
        "pim": pim_file,
        "domains": domains,
        "ai_summary": summary
    }


    if __name__ == "__main__":
        results = run_pipeline("seq1.fasta", input_type="file")
        print(results)


