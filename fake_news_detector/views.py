from django.shortcuts import render
import requests
from .forms import UrlForm
from pdb import set_trace
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
import praw

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

module_dir = os.path.dirname(__file__)

token = r"AAAAAAAAAAAAAAAAAAAAAI%2F9ggEAAAAAAWd2TQzr%2Bmf%2Bny2rPl%2BjQyxgK%2FA%3DFN1l54OhSQiN9VCFVTJgqO5LLoUNssAQQd8cuyl6bDKxw0gVQg"
with open(os.path.join(module_dir, 'csv_data/gossipcop_fake.csv')) as csv_file:
        df = pd.read_csv(csv_file)
        saved_column = df.news_url
with open(os.path.join(module_dir, 'csv_data/politifact_fake.csv')) as csv_file:
    df = pd.read_csv(csv_file)
    saved_column_2 = df.news_url
result = pd.concat([saved_column, saved_column_2], ignore_index=True).tolist()
result = [sub.replace("https://", "", 1) for sub in result if isinstance(sub, str)]
result = [sub.replace("http://", "", 1) for sub in result if isinstance(sub, str)]

def index(request):
    if request.method == 'POST':
        form = UrlForm(request.POST)
        if form.is_valid():
            search = form.cleaned_data['verify_url']
            tweets, numbers = getTweets(search)
            checkCSV = searchData(search)
            checkScrape = scrapeCheck(search)
            reddit = searchReddit(search)
            return render(request, 'fake_news_detector/index.html', {'form': form, 'tweets': tweets, 'numbers': numbers, 'checkCSV': checkCSV, 'checkScrape': checkScrape, 'reddit': reddit})
    else:
        form = UrlForm()
    return render(request, 'fake_news_detector/index.html', {'form': form})

def auth():
    return token

def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

def create_url(keyword, max_results = 10):
    
    search_url = "https://api.twitter.com/2/tweets/search/recent" #endpoint you want to collect data from

    #params based on the endpoint you are using
    query_params = {'query': keyword,
                    'max_results': max_results,
                    'next_token': {}}
    return (search_url, query_params)

def connect_to_endpoint(url, headers, params, next_token = None):
    params['next_token'] = next_token   #params object received from create_url function
    response = requests.request("GET", url, headers = headers, params = params)
    print("Endpoint Response Code: " + str(response.status_code))
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def getTweets(search):
    bearer_token = auth()
    headers = create_headers(bearer_token)
    keyword = f'url:"{search}" (lang:fr OR lang:en) -is:retweet'
    keyword_fake = f'(#fake_news OR #infox OR #fakenews) url:"{search}" (lang:fr OR lang:en) -is:retweet'
    max_results = 100
    url = create_url(keyword, max_results)
    url_fake = create_url(keyword_fake, max_results)
    json_response = connect_to_endpoint(url[0], headers, url[1])
    json_response_fake = connect_to_endpoint(url_fake[0], headers, url_fake[1])
    clean_response = []
    numbers = [0, 0]
    try:
        numbers = [json_response['meta']['result_count'], json_response_fake['meta']['result_count']]
        clean_response = [id['id'] for id in json_response_fake['data']]
    except:
        pass
    return clean_response, numbers

def searchData(search):
    search = search.replace("https://", "", 1)
    search = search.replace("http://", "", 1)
    return search in result

def scrapeCheck(search):
    try:
        req = requests.get(search, headers)
        soup = BeautifulSoup(req.content, 'html.parser')
        article = soup.find("article").get_text()
        url = "https://dawg-fake-news-detector.p.rapidapi.com/predict"
        headers_api = {
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": "e6c3a67e24mshca7d29346c7da93p110b25jsn8b289d3f2b46",
            "X-RapidAPI-Host": "dawg-fake-news-detector.p.rapidapi.com"
        }
        response = requests.request("POST", url, data=article.encode('utf-8'), headers=headers_api)
        res = response.text
        if res == '{"prediction":false}\n':
            return False
        else:
            return True
    except:
        return "not found"

def searchReddit(search):
    reddit = praw.Reddit(
        client_id='8Rt--JtkMkBkPZ_1z68sPg',
        client_secret='8aSbKJy1KjdH_0WbtMF1n4ggZQkHkw', 
        user_agent='workshop'
        )
    headers = {
        'User-Agent': 'nba_comp app',
        'From': 'nickiscool88',
        'Accept': 'application/json'  
    }
    result_list = []
    search_url = 'url:' + search
    resultsUrl = reddit.subreddit('fakenews').search(search_url, limit=10)
    for post in resultsUrl:
        post2 = 'https://www.reddit.com/r/fakenews/comments/' + post.id
        result_list.append(requests.get(f"https://www.reddit.com/oembed?url={post2}", headers=headers).json()['html'])
    return result_list