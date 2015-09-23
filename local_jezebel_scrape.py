import requests
import re
from bs4 import BeautifulSoup
from lxml import html
import requests
import datetime as dt
import numpy as np
import string
import pickle
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import enchant
from collections import Counter
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


class Jezebel(object):
    def __init__(self):
        self.dates = None
        self.bigurl = None
        self.j_strings = None

    def set_dates(self, begin=dt.date(2007,5,21), end=dt.datetime.now()):
        begin = int(begin.strftime("%s")) * 1000
        end = int(end.strftime("%s")) * 1000
        increment = 500000000
        self.dates = np.arange(begin,end,increment)

    def get_urls(self, tag=None):
        responses = []
        soups = []
        js = requests.Session()
        if tag:
            for date in self.dates:
                j_string = 'http://jezebel.com/tag/' + tag + '?startTime=' + str(date)
                soups.append(BeautifulSoup(js.get(j_string, stream=False).content))
        else:
            for date in self.dates:
                j_string = 'http://jezebel.com/?startTime=' + str(date)
                soups.append(BeautifulSoup(js.get(j_string, stream=False).content))

        bigurl = set()
        for soup in soups:
            urls = [x['href'] for x in soup.find_all('a', href=True)]
            urls = [re.search('jezebel',x) for x in urls]
            urls = [x for x in urls if x is not None]
            urls = [x.string for x in urls]
            urls = [x for x in urls if len(x)>50]
            urls = set(urls)
            bigurl = bigurl.union(urls)

        amazons = set(filter((lambda x: re.search(r'amazon', x)),bigurl))
        self.bigurl = bigurl - amazons

    def get_articles(self):
        wordsoups = []
        js = requests.Session()
        for url in self.bigurl:
            wordsoups.append(BeautifulSoup(js.get(url, stream=False).content))

        j_strings = []
        dates = []
        titles = []
        authors = []
        for soup in wordsoups:
            j_string = str()
            for p in soup.find_all('p'):
                temp = p.text
                temp = temp.encode('ascii','ignore')
                j_string += " " + temp
            j_strings.append(j_string)
            dt = soup.find(class=" published updated")
            dates.append(dt.text)
            title = soup.find('title')
            titles.append(title.text)
        with open('jezebel_jstring_list.pkl','wb') as f:
            pickle.dump(j_strings,f)
        self.j_strings = j_strings

    def clean_articles(self):
        j_strings = self.j_strings
        for x in j_strings:
            x = x.replace("\'","").replace("\n"," ").lower()
            x = x.translate(None, string.punctuation)
            x = x.translate(None, digits)
            x = nltk.word_tokenize(x)
        lemmatizer = WordNetLemmatizer()
        for i,j_string in enumerate(j_strings):
            j_string = [x for x in j_string if x not in stopwords.words('english')]
            j_string = [x for x in j_string if len(x)>2]
            j_string = [lemmatizer.lemmatize(x, 'v') for x in j_string]
            j_string = [lemmatizer.lemmatize(x) for x in j_string]
            j_string = [str(x) for x in j_string]
            j_strings[i] = j_string
        self.j_strings = j_strings

    def word_df(self):
        wordset = set()
        for j_string in j_strings:
            wordset = wordset.union(set(j_string))
        wordlist = list(wordset)

        worddf = pd.DataFrame(index=range(len(j_strings)), columns=wordlist)
        worddf = worddf.fillna(0)
        for i,j_string in enumerate(j_strings):
            c = Counter(j_string)
            for key in c:
                worddf[key].ix[i] += c[key]

        index = worddf.apply(sum,0) > 3
        worddf = worddf.ix[:,index]
        worddf = worddf.ix[:,index]
        for word in wordlist:
            if sum(worddf[word]) < 3:
                worddf.drop(word,1)
        with open('jezebel_worddf.pkl','wb') as f:
            pickle.dump(worddf,f)

if __name__ == "__main__":
    j = Jezebel()
    j.set_dates()
    j.get_urls()
    j.get_articles()
