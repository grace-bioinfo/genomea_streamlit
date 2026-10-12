import requests
import time

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

EAST_AFRICA_COUNTRIES = [
    "Kenya",
    "Uganda",
    "Tanzania",
    "Rwanda",
    "Burundi",
    "South Sudan",
    "Democratic Republic of the Congo",
    "Somalia"
]


def search_pubmed(gene_name, east_africa_only=False, max_results=10):
    if east_africa_only:
        region_filter = " OR ".join([f'{c}[AD]' for c in EAST_AFRICA_COUNTRIES])
        term = f"{gene_name} AND ({region_filter})"
    else:
        term = gene_name

    params = {
        "db": "pubmed",
        "term": term,
        "retmax": max_results,
        "retmode": "json"
    }
    response = requests.get(BASE_URL + "esearch.fcgi", params=params)
    response.raise_for_status()
    return response.json()["esearchresult"]["idlist"]




# if __name__ == "__main__":
#     results = search_pubmed("BRCA1", east_africa_only=True, max_results=5)
#     print("PubMed IDs:", results)

def fetch_summaries(pmids):
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json"
    }
    response = requests.get(BASE_URL + "esummary.fcgi", params=params)
    response.raise_for_status()
    data = response.json()["result"]

    summaries = []
    for pmid in pmids:
        if pmid in data:
            item = data[pmid]
            author_list = [a.get("name", "") for a in item.get("authors", [])]
            authors = ", ".join(author_list) if author_list else "N/A"
            summaries.append({
                "pmid": pmid,
                "title": item.get("title", ""),
                "journal": item.get("fulljournalname", ""),
                "pub_date": item.get("pubdate", ""),
                "authors": authors
            })
    
    return summaries

# if __name__ == "__main__":
#     results = search_pubmed("BRCA1", east_africa_only=True, max_results=10)
#     print("PubMed IDs:", results)

#     summaries = fetch_summaries(results)
#     print(len(summaries))
#     for s in summaries:
#         print(s["title"])
#         print(s["authors"])
#         print(s["journal"] + "-" + s["pub_date"])
#         print("----------------------------------------------------")


def fetch_abstracts(pmids):
    if not pmids:
        return {}

    abstracts = {}
    for pmid in pmids:
        params = {
            "db": "pubmed",
            "id": pmid,
            "rettype": "abstract",
            "retmode": "text"
        }
        response = requests.get(BASE_URL + "efetch.fcgi", params=params)
        response.raise_for_status()
        abstracts[pmid] = response.text
        time.sleep(0.34)

    return abstracts

# if __name__ == "__main__":
#     results = search_pubmed("BRCA1", east_africa_only=True, max_results=10)
#     print("PubMed IDs:", results)

#     summaries = fetch_summaries(results)
#     print(len(summaries))
#     for s in summaries:
#         print(s["title"])
#         print(s["authors"])
#         print(s["journal"] + "-" + s["pub_date"])
#         print("---------------------------------------------------------------------------")

#     abstracts = fetch_abstracts(results)
#     for pmid in abstracts:
#         print("PMID:", pmid)
#         print(abstracts[pmid][:300])
#         print("==========================================================================")




