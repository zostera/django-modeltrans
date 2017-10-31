#!/usr/bin/env python

from __future__ import print_function

import json
import os
import sys
from collections import defaultdict

import requests

OUTPUT_FILE = 'fulltextsearch.json'
WIKIPEDIA_URL = (
    'https://{lang}.wikipedia.org/w/api.php?format=json&action=query'
    '&prop=extracts&exintro=&explaintext=&titles={titles}'
)

# seperate titles by a bar (|)
TITLE_SEP = '|'

ARTICLES = {
    'en': 'Vulture,Falcon,Frog,Toad,Duck,Dolphin'.split(','),
    'nl': 'Gieren_van_de_Oude_Wereld,Valkachtigen,Kikkers,Pad,Eenden,Dolfijnen'.split(',')
}


def get_articles(article_list, language='en'):
    url = WIKIPEDIA_URL.format(
        lang=language,
        titles=TITLE_SEP.join(article_list)
    )

    r = requests.get(url)
    if r.status_code != 200:
        print(r.text)
        raise Exception('Error from wikipedia [status: {}], url: {}'.format(r.status_code, url))

    articles = {}
    for page in r.json()['query']['pages'].values():
        articles[page['title'].replace(' ', '_')] = {
            'lang': language,
            'title': page['title'],
            'body': page['extract']
        }

    for title in article_list:
        yield articles[title]


if __name__ == '__main__':
    os.chdir(os.path.dirname(sys.argv[0]))

    fixture = defaultdict(list)
    for lang, articles in ARTICLES.items():
        for i, article in enumerate(get_articles(articles, language=lang)):
            fixture[i].append(article)

    with open(OUTPUT_FILE, 'w') as outfile:
        json.dump(fixture.values(), outfile, indent=2)

    print('Wrote {} articles to {}'.format(len(articles), OUTPUT_FILE))
