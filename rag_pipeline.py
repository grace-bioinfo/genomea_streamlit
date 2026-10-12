import os
import pypdf
import json
import re
import requests
from openai import OpenAI
from PubMed_search import search_pubmed, fetch_summaries, fetch_abstracts

# find pdfs
zotero_path = r"C:\Users\grace\Zotero\storage" 

pdf_files = []
for root, dirs, files in os.walk(zotero_path):
    for file in files:
        if file.endswith(".pdf"):
            pdf_files.append(os.path.join(root, file))

print("Found " + str(len(pdf_files)) + " PDFs")

# After your pdf_files list is created...

if os.path.exists("knowledge_base.json"):   # chcks if knowledge base exists(makes it faster when you load fom existing)
    # faster path....load the existing chunks
    # loading code here
    with open("knowledge_base.json") as f:
        chunks = json.load(f)
    print("Loaded existing knowledge base: " + str(len(chunks)) + " chunks")
else:
    # Slow path - build from scratch
    documents = []
    for pdf_path in pdf_files:
        try:
            reader = pypdf.PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            documents.append(text)
        except:
            pass
    print("Loaded " + str(len(documents)) + " documents")

    chunks = []
    for doc in documents:
        for i in range(0, len(doc), 450):
            chunk = doc[i:i+500]
            if len(chunk) > 100:
                chunks.append(chunk)
    print("Total chunks: " + str(len(chunks)))

# save chunks to json file
    with open("knowledge_base.json", "w") as f:
        json.dump(chunks, f)
    print("Knowledge base created!!!")



# Search knowledge base


def search(query, top_k=5, min_score=2):
    results = []
    query_words = query.lower().split()
    gene_term = query_words[0]
    gene_pattern = r'\b' + re.escape(gene_term) + r'\b'

    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for word in query_words if word in chunk_lower)
        if score >= min_score and re.search(gene_pattern, chunk_lower):
            results.append((score, chunk))

    results.sort(reverse=True)
    return [chunk for score, chunk in results[:top_k]]


def get_context(query):
    local_results = search(query)

    if local_results:
        return {
            "source": "curated_papers",
            "context": local_results
        }

    gene_term = query.split()[0]
    pmids = search_pubmed(gene_term, max_results=3)
    summaries = fetch_summaries(pmids)
    abstracts = fetch_abstracts(pmids)

    labeled_context = []
    for s in summaries:
        pmid = s["pmid"]
        entry = "Title: " + s["title"] + " (PMID: " + pmid + ")\n" + abstracts.get(pmid, "")
        labeled_context.append(entry)

    return {
        "source": "pubmed_live",
        "context": labeled_context
    }

# Test it

test_results = search("XIST gene function")
print("Search results found: " + str(len(test_results)))

for i, result in enumerate(test_results):
    print(f"--- Match {i+1} ---")
    print(result[:300])
    print()

result = get_context("XIST gene function")
print("Source used:", result["source"])
print("Number of context items:", len(result["context"]))

for i, item in enumerate(result["context"]):
    print(f"--- Item {i+1} ---")
    print(item[:300])
    print()

# setup the client first
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "GKN_NVIDIA_KEY"
)
# add RAG + question

def genomea_ai(question, pipeline_results=""):
    context_result = get_context(question)
    context = "\n\n".join(context_result["context"])
    source_label = context_result["source"]

    completion = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": "You are a genomics expert specializing in East Africa. Clearly state whether your answer comes from the curated East African paper corpus or a live PubMed search."},
            {"role": "user", "content": "Context (source: " + source_label + "):\n" + context + "\n\nQuestion: " + question}
        ],
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
        stream=True
    )

    response = ""
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content

    return response






