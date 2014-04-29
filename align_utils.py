import csv

# The alignment is pairs of (source, target) alignments.
# In the CSV file, columns are source and rows are target.
def alignment_to_csv(alignments, outfile, on='X', off='0'):
    max_col = reduce(lambda acc, x: max(acc, x[0]), alignments, -1) + 1
    max_row = reduce(lambda acc, x: max(acc, x[1]), alignments, -1) + 1
    # First order array is columns, second order arrays are rows
    # First order array is rows, second order arrays are columns
    csv_grid = [None] * max_row
    for i, row in enumerate(csv_grid):
        csv_grid[i] = [off] * max_col
    # Mark each alignment value in the grid
    for alignment in alignments:
        csv_grid[alignment[1]][alignment[0]] = on
    # Write out the CSV files
    with open(outfile, 'w+') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
        for row in csv_grid:
            csv_writer.writerow(row)


# Converts the alignment pairs to strings of the form: source - target
def alignment_to_str(alignments):
    return ' '.join(map(lambda pair: str(pair[0]) + '-' + str(pair[1]),
                        alignments))

def str_to_alignment(alignment_line):
    map(lambda pair_str: tuple(map(lambda x: int(x),
                                   pair_str.split('-'))),
        alignment_line.strip().split())
