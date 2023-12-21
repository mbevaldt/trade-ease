import os

def countlines(start, lines=0, header=True, begin_start=None):
    if header:
        print('{:>10} |{:>10} | {:<20}'.format('ADDED', 'TOTAL', 'FILE'))
        print('{:->11}|{:->11}|{:->20}'.format('', '', ''))

    for thing in os.listdir(start):
        thing = os.path.join(start, thing)
        if os.path.isfile(thing):
            if thing.endswith('.py'):
                with open(thing, 'r') as f:
                    newlines = f.readlines()
                    newlines = len(newlines)
                    lines += newlines

                    if begin_start is not None:
                        reldir_of_thing = '.' + thing.replace(begin_start, '')
                    else:
                        reldir_of_thing = '.' + thing.replace(start, '')

                    print('{:>10} |{:>10} | {:<20}'.format(
                            newlines, lines, reldir_of_thing))


    for thing in os.listdir(start):
        thing = os.path.join(start, thing)
        if os.path.isdir(thing):
            lines = countlines(thing, lines, header=False, begin_start=start)

    return lines


#countlines('C:/Users/mbeva/OneDrive/Documentos/python/trade-ease')

import pandas as pd

labels = ["label1", "label2", "label3"]
types = ["type1", "type2", "type3", "type4", "type5", "type6"]
counts = [[3, 5, 2, 1, 7, 10], [2, 2, 4, 1, 7, 2], [1, 6, 8, 11, 2, 3]]

df = pd.DataFrame(counts, columns=types, index=labels).reset_index().melt(id_vars="index")

print(df)