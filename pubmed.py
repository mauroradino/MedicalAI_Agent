import requests
import xml.etree.ElementTree as ET

symptoms = "headache, fever, runny nose"

def get_medical_articles(symptoms):
    params = {
        'db': 'pubmed',
        'term': symptoms,
        'retmode': 'json',
        'retmax': 10,  
        'sort': 'relevance' 
    }
    res = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)
    data = res.json()
    article_ids=data["esearchresult"]["idlist"]

    if article_ids:
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(article_ids),
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        fetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
        fetch_response = requests.get(fetch_url, params=fetch_params)

        root = ET.fromstring(fetch_response.content)

        articles = []        

        for article in root.findall('.//PubmedArticle'):
            pmid = article.find('.//PMID').text
            title = article.find('.//ArticleTitle').text
            
            abstract_text = "No abstract available"
            abstract = article.find('.//AbstractText')
            if abstract is not None:
                abstract_text = ''.join(abstract.itertext())
            
            obj = {
                "pmid": pmid,
                "title": title,
                "abstract": abstract_text[:1000]
            }
            articles.append(obj)
    return articles
