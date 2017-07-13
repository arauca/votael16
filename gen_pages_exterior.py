# -*- coding: utf-8

from subprocess import call
import pandas as pd
import numpy as np
import unicodedata
import collections
import argparse
import shutil
import json
import os
import re


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_args():
    parser = argparse.ArgumentParser(
                        description="Generate pages for the elections.",
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--data', metavar="D", nargs='?',
                        default=os.path.join('data',
                                             'exterior-2017-07-12-23-00.xlsx'),
                        help='Path to the Excel data file')
    parser.add_argument('--sheet', metavar="S", nargs='?',
                        default='Sheet1',
                        help='Path to the Excel data file')
    parser.add_argument('--output', metavar="O", nargs='?',
                        default=os.path.join("output2", "pages"),
                        help='Output directory')
    parser.add_argument('--template', metavar="T", nargs='?',
                        default=os.path.join("data", "template-exterior.html"),
                        help='Template file')

    return parser.parse_args()


def remove_accents(tks):
    return [tk.encode('ascii', 'ignore').decode('ascii')
            for tk in tks]


def get_stopwords():
    f = open('data/stopwords.csv')
    stopwords = set([x.strip().lower() for x in f.readlines()])
    f.close()
    return stopwords


args = get_args()

try:
    shutil.rmtree(args.output)
except:
    pass

makedirs(args.output)
df = pd.read_excel(args.data, sheetname=args.sheet)

f = open(args.template)
template = f.read()
f.close()

print('Creating pages')
all_small = []
stopwords = get_stopwords()

index = {}
files = {}

docs = 1
title_str = '<td>{country}</td><td>{city}</td><td>{address}</td>'

for state_gk, states in df.groupby('País'):
    next_state_path = os.path.join(args.output,
                                   re.sub('[\.\s]+', '', state_gk))
    makedirs(next_state_path)

    print('  ', state_gk)

    for municipality_gk, municipalities in states.groupby('Ciudad'):
        next_path = os.path.join(next_state_path,
                                 re.sub('[\.\s]+', '',
                                        municipality_gk.replace('MP.', '')))
        makedirs(next_path)

        municipalities = municipalities.to_dict(orient='records')

        center_code = 0
        for center in municipalities:
            address = center['Dirección']
            if type(address) == float:
                address = ''

            # Create the index text
            full_str = u' '.join([center['País'], center['Ciudad'],
                                  address])

            # FIXME: Remove special characters (this could be done with
            # unicode regular expressions)
            full_str = u''.join([c for c in full_str
                                 if c not in "#(),-./0123456789;"])

            # Split in tokens
            full_str = full_str.split()

            # Include the words without accents
            full_str = [val for pair in zip(full_str,
                                            remove_accents(full_str))
                        for val in pair]

            # Remove small words and domain-specific stop-words
            full_str = [tk for tk in full_str
                        if len(tk) > 2 and tk.lower() not in stopwords]

            # TODO: Introduce errors

            # Compute weight of each word in the center
            next_tk_frequency = {}

            for tk_id, tk in enumerate(full_str):
                tk = tk.lower()
                pos_rel = len(full_str) - tk_id
                max_rel = len(full_str)
                next_tk_frequency[tk] = next_tk_frequency.get(tk, []) + \
                    [pos_rel / max_rel]
            next_tk_frequency = {tk: max(rels)
                                 for tk, rels in next_tk_frequency.items()}

            for tk, rel in next_tk_frequency.items():
                index[tk] = index.get(tk, [])
                index[tk].append({'f': docs, 'w': 1 + rel})

            # Generate the new entry
            title = title_str.format(
                     country=center['País'].title(),
                     city=center['Ciudad'].title(),
                     address=address.title())
            
            for rp in ['Mp. ', 'Mp.', 'MP.']:
                title = title.replace(rp, '')

            files[str(docs)] = \
                {
                 #'url': os.path.join(next_path,
                                     #'%d.html' % center_code),
                 'title': title}
            print(os.path.join(next_path,
                                     '%d.html' % center_code))
            docs += 1

            next_string = \
                template.format(country=center['País'].title(),
                                city=center['Ciudad'].title(),
                                address=address.title())

            f = open(os.path.join(next_path,
                                  '%d.html' % center_code), 'w')
            center_code += 1
            f.write(next_string)
            f.close()

f = open('exterior.index.js', 'w')
f.write('exterior.index = ' + json.dumps(index) + ';\n')
f.write('exterior.files= ' + json.dumps(files) + ';\n')
f.write(
"""
exterior.tokenizeString = function(string) {
        var stopWords = [%s];
        return string.split(/[\s\.,;\:\\\/\[\]\(\)\{\}]+/).map(function(val) {
            return val.toLowerCase();
        }).filter(function(val) {
            for (w in stopWords) {
                if (stopWords[w] == val) return false;
            }
            return true;
        }).map(function(word) {
            return {t: word, w: 1};
        });
};
""" % ', '.join(['"%s"' % x for x in stopwords]))
f.close()
