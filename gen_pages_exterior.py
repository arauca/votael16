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
                                             'exterior-2017-07-13-23-00.xlsx'),
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


def usa_alternatives(tks, center):
    ltks = [tk.lower() for tk in tks]
    new_tks = []
    abbreviations = {'AL': 'Alabama',
                     'AZ': 'Arizona',
                     'CA': 'California',
                     'CO': 'Colorado',
                     'CT': 'Connecticut',
                     'DC': ['District', 'Columbia', 'Dist'],
                     'Dalton': 'Massachusetts',
                     'FL': 'Florida',
                     'GA': 'Georgia',
                     'HI': 'Hawaii',
                     'IL': 'Illinois',
                     'IN': 'Indiana',
                     'KS': 'Kansas',
                     'KY': 'Kentucky',
                     'LA': 'Louisiana',
                     'MA': 'Massachusetts',
                     'MD': 'Maryland',
                     'MI': 'Michigan',
                     'MN': 'Minnesota',
                     'MO': 'Missouri',
                     'MT': 'Montana',
                     'NC': ['North', 'Carolina'],
                     'NE': 'Nebraska',
                     'NJ': ['New', 'Jersey'],
                     'NM': ['New', 'Mexico'],
                     'NV': 'Nevada',
                     'NY': ['New', 'York'],
                     'OH': 'Ohio',
                     'OK': 'Oklahoma',
                     'OR': 'Oregon',
                     'PA': 'Pennsylvania',
                     'Puerto Rico': ['Puerto', 'Rico'],
                     'SC': ['South', 'Carolina'],
                     'TN': 'Tennessee',
                     'TX': 'Texas',
                     'UT': 'Utah',
                     'VA': 'Virginia',
                     'WA': 'Washington',
                     'WI': 'Wisconsin',
                     }

    if center['PAIS'] == 'ESTADOS UNIDOS':
        new_tks += ['USA', 'EEUU']
        abbr = center['CIUDAD'].split(',')[0]
        if abbr not in abbreviations:
            print('Abbreviation not found', abbr)
        elif type(abbreviations[abbr]) == str:
            new_tks.append(abbreviations[abbr])
        else:
            new_tks += abbreviations[abbr]
        return new_tks
    else:
        return tks
    return tks


def introduce_errors(tks):
    def tk_errors(tk):
        return [
                #tk.replace('s', 'z'),
                #tk.replace('z', 's'),
                #tk.replace('b', 'v'),
                #tk.replace('v', 'b'),
                #tk.replace('h', '')
                tk.replace('ñ', 'n'),
                tk.replace('á', 'a'),
                tk.replace('é', 'e'),
                tk.replace('í', 'i'),
                tk.replace('ó', 'o'),
                tk.replace('ú', 'u'),
                ]

    return [error for tk in tks for error in tk_errors(tk.lower())
            if error != tk.lower()]


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

for state_gk, states in df.groupby('PAIS'):
    next_state_path = os.path.join(args.output,
                                   re.sub('[\.\s]+', '', state_gk))
    makedirs(next_state_path)

    print('  ', state_gk)

    for municipality_gk, municipalities in states.groupby('CIUDAD'):
        next_path = os.path.join(next_state_path,
                                 re.sub('[\.\s]+', '',
                                        municipality_gk.replace('MP.', '')))
        makedirs(next_path)

        municipalities = municipalities.to_dict(orient='records')

        center_code = 0
        for center in municipalities:
            address = center['DIRECCION']
            if type(address) == float:
                address = ''

            # Create the index text
            full_str = u' '.join([center['PAIS'], center['CIUDAD'],
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

            full_str = full_str + usa_alternatives(full_str, center)

            # Remove small words and domain-specific stop-words
            full_str = [tk for tk in full_str
                        if len(tk) > 2 and tk.lower() not in stopwords]

            # Introduce errors
            full_str = full_str + introduce_errors(full_str)

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
                     country=center['PAIS'].title(),
                     city=center['CIUDAD'].title(),
                     address=address.title())
            
            for rp in ['Mp. ', 'Mp.', 'MP.']:
                title = title.replace(rp, '')

            files[str(docs)] = \
                {
                 #'url': os.path.join(next_path,
                                     #'%d.html' % center_code),
                 'title': title}
            #print(os.path.join(next_path,
                                     #'%d.html' % center_code))
            docs += 1

            next_string = \
                template.format(country=center['PAIS'].title(),
                                city=center['CIUDAD'].title(),
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
