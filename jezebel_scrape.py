import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import numpy as np
import json
import boto3
from boto3.s3.transfer import S3Transfer
import string
import time

class Jezebel(object):
    '''
    This object scrapes the Jezebel website for news articles and stores
    each article as a seperate json file on AWS S3. The object will wait a
    specified amount of time before re-running.

    INPUTS: config file with AWS keys.
    OUTPUTS: json files in the format:
        {'author': author, 'date': date, 'text': text, 'title': title}

    Each file is named a concatenated title as a name. If the scraper does not
    find a title, the file will be called a auto-incrementing number. The json
    files will have the value of 'NULL' if the scraper does not return a value.
    '''
    def __init__(self):
        '''
        Set the date to begin scraping.
        '''
        self.begin = dt.date(2007, 5, 21)

    def open_connection(self, config):
        '''
        Read in a config file with AWS auth keys. Format:
        {'key': key, 'secrete': secrete-key}
        '''
        keys = eval(open(config).read())
        self.client = boto3.client('s3', 'us-east-1',
                                   aws_access_key_id=keys['key'],
                                   aws_secret_access_key=keys['secrete'])
        self.transfer = S3Transfer(self.client)

    def set_dates(self, end=dt.datetime.now()):
        '''
        Create an array of dates in unixtime. These are used in looping
        through the website's main articles index.
        '''
        begin = int(self.begin.strftime("%s")) * 1000
        end = int(end.strftime("%s")) * 1000
        increment = 300000000
        self.dates = np.arange(begin, end, increment)
        self.end = end
        self.begin = end

    def get_urls(self, replies=False, tag=None):
        '''
        This function loops through the main article index and pulls the
        urls for each article.
        OPTIONS:
            replies: If True, it will collect the comments on each article.
            tag: tag can be set to a string that relates to any tags that
                 jezebel uses.
        '''
        js = requests.Session()
        bigurl = set()
        if tag:
            for date in self.dates:
                try:
                    j_string = 'http://jezebel.com/tag/' + tag + \
                               '?startTime=' + str(date)
                    soup = \
                        BeautifulSoup(js.get(j_string, stream=False).content)
                    urls = [x['href'] for x in soup.find_all('a', href=True)]
                    urls = [re.search('http:.*jezebel', x) for x in urls]
                    urls = [x for x in urls if x is not None]
                    urls = [x.string for x in urls]
                    urls = [x for x in urls if len(x) > 50]
                    urls = set(urls)
                    bigurl = bigurl.union(urls)
                except requests.exceptions.RequestException:
                    pass
        else:
            for date in self.dates:
                try:
                    j_string = 'http://jezebel.com/?startTime=' + str(date)
                    soup = \
                        BeautifulSoup(js.get(j_string, stream=False).content)
                    urls = [x['href'] for x in soup.find_all('a', href=True)]
                    urls = [re.search('http:.*jezebel',x) for x in urls]
                    urls = [x for x in urls if x is not None]
                    urls = [x.string for x in urls]
                    urls = [x for x in urls if len(x) > 50]
                    urls = set(urls)
                    bigurl = bigurl.union(urls)
                except requests.exceptions.RequestException:
                    pass

        amazons = set(filter((lambda x: re.search(r'amazon', x)), bigurl))
        if replies:
            self.bigurl = bigurl - amazons
        else:
            rep = set(filter((lambda x: re.search(r'replies', x)), bigurl))
            self.bigurl = bigurl - amazons - rep

    def get_articles(self, path):
        '''
        This loops through the urls collected by the get_urls function and
        scrapes the website at the end of the url. It then populates a
        dictionary with the results, dumps it as a json, and uploads the
        json to S3. 
        '''
        self.open_connection(path)
        js = requests.Session()
        n = 1
        for url in self.bigurl:
            article = {}
            try:
                soup = BeautifulSoup(js.get(url, stream=False).content)
                j_string = str()
                if soup:
                    for p in soup.find_all('p'):
                        if p:
                            temp = p.text
                            temp = temp.encode('ascii', 'ignore')
                            j_string += " " + temp
                    if j_string == str():
                        j_string = 'NULL'
                    article['text'] = j_string
                    dt = soup.find("span", {"class": " published updated"})
                    if dt:
                        dt = dt.text
                        article['date'] = dt
                    else:
                        dt = 'NULL'
                        article['date'] = 'NULL'
                    title = soup.find('title')
                    if title:
                        title = title.text.encode('ascii', 'ignore')
                        article['title'] = title
                    else:
                        title = 'NULL'
                        article['title'] = 'NULL'
                    author = soup.find("meta", {"name": "author"})
                    if author:
                        author = author['content'].encode('ascii', 'ignore')
                        article['author'] = author
                    else:
                        author = 'NULL'
                        article['author'] = 'NULL'
                    with open('dump', 'w') as temp:
                        json.dump(article, temp)
                    rems = string.punctuation + string.whitespace
                    if article['title'] != 'NULL':
                        name = \
                            article['title'].translate(None, string.punctuation)
                        name = name.translate(None, string.whitespace)
                        name = name.lower()
                    else:
                        name = str(n)
                        n += 1
                    self.transfer.upload_file('dump', 'jezebel.scrape',
                                              key=name)
            except requests.exceptions.RequestException:
                print 'Warning: failed parsing url: ' + str(url)

if __name__ == "__main__":
    path = '/home/ec2-user/aws.config.txt'
    j = Jezebel()
    while True:
        j.set_dates(end=pd.datetime.now())
        j.get_urls()
        j.get_articles(path=path)
        time.sleep(299999)
