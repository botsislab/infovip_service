import mysql.connector
from mysql.connector import errorcode
from pubmed.pubmed_utility import PubMedUtility
import ssl
import db_util
import json
import traceback
from datetime import datetime

def get_articles(query, email):

    # Get response from PubMed
    ssl._create_default_https_context = ssl._create_unverified_context
    results = PubMedUtility.search(query, email, maxRecords = 10)

    # Don't get details if there were no matches
    if len(results['IdList']) == 0:
        return []

    ids = results['IdList']
    results = PubMedUtility.fetch_details(ids, email)['PubmedArticle']

    articles = []
    params_list = []

    # Keep only the fields we care about
    for result in results:
        abstract = result['MedlineCitation']['Article']['Abstract']['AbstractText'] if 'Abstract' in result['MedlineCitation']['Article'] else []
        articles.append({
            'pmid': str(result['MedlineCitation']['PMID']),
            'title': result['MedlineCitation']['Article']['ArticleTitle'],
            'abstract': abstract,
            'full_medline': result['MedlineCitation'],
            'retrieval_time': datetime.today().isoformat().split('T')[0]
        })
        params_list.append((
            str(result['MedlineCitation']['PMID']),
            result['MedlineCitation']['Article']['ArticleTitle'],
            json.dumps(abstract),
            json.dumps(result['MedlineCitation'], sort_keys = True),
            datetime.today().isoformat().split('T')[0]
        ))
      
    # If there are no articles, return as is because there's nothing to store
    if len(articles) == 0:
        return articles

    # Store articles in the database
    columns = articles[0].keys()
    columns_string = ','.join(columns)
    placeholders = ','.join(['%s'] * len(columns))

    query = 'INSERT INTO pubmed_record_details (' + columns_string + ') VALUES (' + placeholders + ')'

    for params in params_list:
        try:
            db_util.do_update(query, params)
        except mysql.connector.Error as error:
            # Can show a minimal error message if it's just a duplicate primary key
            if error.errno == errorcode.ER_DUP_ENTRY:
                print(error)
            else:
                print(traceback.format_exc())
        except Exception:
            # Probably just duplicate key errors
            print(traceback.format_exc())

    return articles