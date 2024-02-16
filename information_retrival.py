from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import pandas as pd
import spacy_universal_sentence_encoder

# Utility Functions to aid final pipeline

def find_similarity(text_1:str,text_2:str):
    '''
    Function to remove filler words amd calculate similarity between two textual information

    Args:
        text_1(str): First Sentence/paragraph/textual-information
        text_2(str): Second Sentence/paragraph/textual-information

    Returns:
        similarity_score(float): Percentage Similarity between text_1 and text_2
    '''
    # Complete sentence encoding
    text_1 = nlp(text_1)
    text_2 = nlp(text_2)

    # Encoding without filler and stop words like I,is,am,are,...etc..
    text_1_encoding = nlp(" ".join([str(token) for token in text_1 if not token.is_stop]))
    text_2_encoding = nlp(" ".join([str(token) for token in text_2 if not token.is_stop]))

    similarity_score = text_1_encoding.similarity(text_2_encoding)
    
    return similarity_score


def fetch_query_links(query:str):
    '''
    Fetch links of top results for the quesry from DuckDuckGo search engine

    Args:
        query(str): Query to be searched by DuckDuckGo search engine

    Returns:
        links(list[tuple[str,str]]): List of tuples containing headline/title of web page and link of that web page
    '''
    links = []
    # fetch results from DuckDuckGo search engine
    query_results = ddgs.text(region='us-en',keywords=query,max_results=10)
    # itterate over results to collect relevant information
    for result in query_results:
        title = result['title']
        link = result['href']
        links.append((title,link))

    return links


def scrap_text_from_website(link:str):
    '''
    Collect HTML response from website and scrap it to extract relevant information

    Args:
        link(str): Web address of the target website.

    Returns:
        data(str): Scrapped data in string format
    '''
    website_response = requests.get(link,headers=AGENT)     # fetch reponse from website
    website_content = website_response.content              # extract HTML content
    soup = BeautifulSoup(website_content)                   # parse HTML with BS4
    data = soup.getText()                                   # extract text information

    return data



QUERIES = [
    "Identify the industry in which Canoo operates, along with its size, growth rate, trends, and key players.",
    "Analyze Canoo's main competitors, including their market share, products or services offered, pricingstrategies, and marketing efforts.",
    "Identify key trends in the market, including changes in consumer behavior, technological advancements, and shifts in the competitive landscape."
    "Gather information on Canoo's financial performance, including its revenue, profit margins, return on investment, and expense structure."
    ]

# To bypass web-crawling restrictions
AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}

ddgs = DDGS()
nlp = spacy_universal_sentence_encoder.load_model('en_use_lg')


# Initialize Structure data dictionary to support Pandas DataFrame
structured_data = {
    'Query':[],
    'Title':[],
    'Source':[],
    'Data':[]
}

# Complete Pipeline to collect and store data
for e,query in enumerate(QUERIES):
    print(f'Executing Query : {e+1}')
    links = fetch_query_links(query=query)  # fetch first 10 webpage's links related to query
    
    for head,link in links:
        
        data = scrap_text_from_website(link) # scrap data from websites

        # Check whether similar data already exsist in database for that query
        add_in_database = True
        for checker,prev_data in enumerate(structured_data['Data']):
            if structured_data['Query'][e] == query:
                if find_similarity(prev_data,data) > 0.8:
                    add_in_database = False

        # Update Database with new information
        if add_in_database:
            stuctured_data['Query'].append(query)
            stuctured_data['Title'].append(head)
            stuctured_data['Source'].append(link)
            stuctured_data['Data'].append(data)


# converting Structured data to pandas DataFrame object which is optimized for python
dataframe = pd.DataFrame(stuctured_data)
print(dataframe.sample(frac=1))

# export structured tabular data to CSV
dataframe.to_csv('retrieved_data.csv',index=False)
