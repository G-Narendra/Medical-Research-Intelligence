import os
import time
import urllib.parse
import urllib.request
import json
import xml.etree.ElementTree as ET
from typing import List, Dict
from tavily import TavilyClient


class MedicalRetriever:
    """
    Multi-source retrieval: PubMed + Tavily Web Search
    """

    def __init__(self):
        self.ncbi_api_key = os.environ.get("NCBI_API_KEY", "")
        self.tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def search_pubmed(self, query: str, max_results: int = 8) -> List[Dict]:
        """Search PubMed and return structured paper metadata."""
        try:
            # Step 1: ESearch to get PMIDs
            search_params = urllib.parse.urlencode({
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
                "api_key": self.ncbi_api_key
            })
            search_url = f"{self.base_url}esearch.fcgi?{search_params}"
            with urllib.request.urlopen(search_url) as resp:
                search_data = json.loads(resp.read().decode())

            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return []

            time.sleep(0.5)

            # Step 2: EFetch to get abstracts
            fetch_params = urllib.parse.urlencode({
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "api_key": self.ncbi_api_key
            })
            fetch_url = f"{self.base_url}efetch.fcgi?{fetch_params}"
            with urllib.request.urlopen(fetch_url) as resp:
                xml_data = resp.read().decode()

            return self._parse_pubmed_xml(xml_data)

        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def _parse_pubmed_xml(self, xml_data: str) -> List[Dict]:
        """Parse PubMed XML response into structured list."""
        papers = []
        try:
            root = ET.fromstring(xml_data)
            for article in root.findall(".//PubmedArticle"):
                title_el = article.find(".//ArticleTitle")
                abstract_el = article.find(".//AbstractText")
                pmid_el = article.find(".//PMID")
                year_el = article.find(".//PubDate/Year")
                journal_el = article.find(".//Journal/Title")

                authors = []
                for author in article.findall(".//Author")[:3]:
                    last = author.find("LastName")
                    if last is not None:
                        authors.append(last.text)

                papers.append({
                    "source": "PubMed",
                    "pmid": pmid_el.text if pmid_el is not None else "N/A",
                    "title": title_el.text if title_el is not None else "N/A",
                    "abstract": abstract_el.text if abstract_el is not None else "No abstract available",
                    "authors": authors,
                    "year": year_el.text if year_el is not None else "N/A",
                    "journal": journal_el.text if journal_el is not None else "N/A",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid_el.text}/" if pmid_el is not None else ""
                })
        except ET.ParseError as e:
            print(f"XML parse error: {e}")
        return papers

    def search_web(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search the web via Tavily for clinical trials and news."""
        try:
            results = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=["clinicaltrials.gov", "nih.gov", "who.int", "fda.gov", "nejm.org", "thelancet.com"]
            )
            web_results = []
            for r in results.get("results", []):
                web_results.append({
                    "source": "Web",
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                    "score": r.get("score", 0)
                })
            return web_results
        except Exception as e:
            print(f"Web search error: {e}")
            return []
