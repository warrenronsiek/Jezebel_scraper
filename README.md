Jezebel Scraper
===============

This is code for scraping the news website jezebel.com. I hope to be using
this for future text analysis projects. Note that I will probably not be
maintaining this code for the indefinite future, and if the website structure
changes, this code will no longer work.

Some of the functions have not been fully tested and are based on my
observations of the website's general html patterns:

1. Scraping by article tag should work, but I haven't fully used this functionality yet.
2. Scraping replies to articles may be sketchy. Again, I haven't really tested this.

You may be wondering, 'Why Jezebel?' There are two answers:

1. Jezebel.com is very easy to scrape: their infrastructure has reliable patterns.
2. I hope to scrape other websites in the future. Fox news nation is in the works. This is just the first one I have written.

Some parts of this code violate coding general coding rules. I.e. there are
try/except structures that just pass on event of an error. I am aware of this,
but given the nature of webscraping, it doesn't make very much sense to have
an error log - there will be plenty of things that look like articles but
aren't, and there will be many articles that don't match the structure
required for the web scraper. Right now, I do not believe that these edge
cases will threaten future analytics.
