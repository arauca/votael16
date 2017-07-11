import numpy as np
import pandas as pd
import argparse
import os


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_args():
    parser = argparse.ArgumentParser(
                        description="Generate pages for the elections.",
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--data', metavar="D", nargs='?',
                        default=os.path.join('data',
                                             'nacional-2017-07-10-18-00.xlsx'),
                        help='Path to the Excel data file')
    parser.add_argument('--sheet', metavar="S", nargs='?',
                        default='TablaMesasNacional',
                        help='Path to the Excel data file')
    parser.add_argument('--output', metavar="O", nargs='?',
                        default=os.path.join("output", "pages"),
                        help='Output directory')
    parser.add_argument('--template', metavar="T", nargs='?',
                        default=os.path.join("data", "template.html"),
                        help='Template file')
    return parser.parse_args()


def center_template(args):
    f = open(args.template)
    ret = f.read()
    f.close()
    return ret


args = get_args()

makedirs(args.output)
df = pd.read_excel(args.data, sheetname=args.sheet)
template = center_template(args)

for state_gk, states in df.groupby('ESTADO'):
    next_state_path = os.path.join(args.output, state_gk)
    makedirs(next_state_path)

    print(state_gk)

    for municipality_gk, municipalities in states.groupby('MUNICIPIO'):
        next_path = os.path.join(args.output, state_gk, municipality_gk)
        makedirs(next_path)

        municipalities = municipalities.to_dict(orient='records')

        for center in municipalities:
            next_string = template.format(state=center['ESTADO'],
                                          municipality=center['MUNICIPIO'],
                                          parish=center['PARROQUIA'],
                                          name=center['NOMBRE'],
                                          address=center['DIRECCION'],
                                          tables=center['MESAS'])

            f = open(os.path.join(next_path,
                                  '%d.html' % center['CODIGO_PS']), 'w')
            f.write(next_string)
            f.close()
