# Take an input CSV and tweak which courts are assigned to which
# matches such that no one has to play on Court 1 more than once,
# if possible.
import csv


def main():
  with open('13men_14women_3courts.csv', 'r') as csvfile:
    reader = iter(csv.reader(csvfile))

    # Throw out the header row
    next(reader)

    for row in reader:
      # Actually this might be highly unlikely to yield
      # valid results. Considering adding to the original
      # optimizer instead.


if __name__ == '__main__':
  main()
