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
                                             'nacional-2017-07-11-12-30.xlsx'),
                        help='Path to the Excel data file')
    parser.add_argument('--sheet', metavar="S", nargs='?',
                        default='TablaMesaVenezuela',
                        help='Path to the Excel data file')
    parser.add_argument('--output', metavar="O", nargs='?',
                        default=os.path.join("output", "pages"),
                        help='Output directory')
    parser.add_argument('--template', metavar="T", nargs='?',
                        default=os.path.join("data", "template.html"),
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
title_str = '<td>{state}</td><td>{municipality}</td><td>{parish}</td><td>{name}</td><td>{address}</td>'

for state_gk, states in df.groupby('ESTADO'):
    next_state_path = os.path.join(args.output,
                                   re.sub('[\.\s]+', '', state_gk))
    makedirs(next_state_path)

    print('  ', state_gk)

    for municipality_gk, municipalities in states.groupby('MUNICIPIO'):
        next_path = os.path.join(next_state_path,
                                 re.sub('[\.\s]+', '',
                                        municipality_gk.replace('MP.', '')))
        makedirs(next_path)

        municipalities = municipalities.to_dict(orient='records')

        for center in municipalities:
            address = center['DIRECCION']
            if type(address) == float:
                address = ''

            # Create the index text
            full_str = u' '.join([center['ESTADO'], center['MUNICIPIO'],
                                  center['PARROQUIA'], center['NOMBRE'],
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
                        if len(tk) > 3 and tk.lower() not in stopwords]

            # TODO: Introduce errors

            # Compute weight of each word in the center
            next_tk_frequency = {}

            for tk_id, tk in enumerate(full_str):
                tk = tk.lower()
                pos_rel = 2. ** (len(full_str) - tk_id)
                max_rel = 2. ** len(full_str)
                next_tk_frequency[tk] = next_tk_frequency.get(tk, []) + \
                    [pos_rel / max_rel]
            next_tk_frequency = {tk: max(rels)
                                 for tk, rels in next_tk_frequency.items()}

            for tk, rel in next_tk_frequency.items():
                index[tk] = index.get(tk, [])
                index[tk].append({'f': docs, 'w': 1 + rel})

            # Generate the new entry
            files[str(docs)] = \
                {'url': os.path.join(next_path,
                                     '%d.html' % center['CODIGO_PS']),
                 'title': title_str.format(
                     state=center['ESTADO'].title(),
                     municipality=center['MUNICIPIO'].title(),
                     parish=center['PARROQUIA'].title(),
                     name=center['NOMBRE'].title(),
                     address=address)}
            print(os.path.join(next_path,
                                     '%d.html' % center['CODIGO_PS']))
            docs += 1

            next_string = \
                template.format(state=center['ESTADO'].title(),
                                municipality=center['MUNICIPIO'].title(),
                                parish=center['PARROQUIA'].title(),
                                name=center['NOMBRE'],
                                address=address,
                                tables=center['MESAS'])

            f = open(os.path.join(next_path,
                                  '%d.html' % center['CODIGO_PS']), 'w')
            f.write(next_string)
            f.close()

f = open('jssearch.index.js', 'w')
f.write('jssearch.index = ' + json.dumps(index) + ';\n')
f.write('jssearch.files= ' + json.dumps(files) + ';\n')
f.write(
"""
jssearch.tokenizeString = function(string) {
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
