import collections
import csv
import random

# This script assumes columns go:
# Last name, First name, _, _, M/F


def main():
  with open('roster.csv', 'r') as infile, open('namelist.txt', 'w') as outfile:
    csvreader = csv.reader(infile)
    grouped = collections.defaultdict(list)
    for row in csvreader:
      grouped[row[4]].append(f'{row[1]} {row[0]}')
    outlines = []
    for gender, names in grouped.items():
      random.shuffle(names)
      for idx, name in enumerate(names):
        outlines.append(f'{gender}{idx + 1} = {name}')
    outfile.write('\n'.join(outlines))


if __name__ == '__main__':
  main()
