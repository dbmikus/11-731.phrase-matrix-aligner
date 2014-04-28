#!/usr/bin/python

import argparse
import sys
import codecs
from collections import namedtuple

phrase = namedtuple("phrase", "english, prob")

def setup_parser():
    parser = argparse.ArgumentParser(description='Create alignment matrix based on a phrase table.')
    parser.add_argument('-s', '--source', dest='source_filename',
        required=True,
        help='The source language version of paired f-e text.')
    parser.add_argument('-t', '--target', dest='target_filename',
        required=True,
        help='The target language version of paired f-e text.')
    parser.add_argument('-p', '--phrase-table', dest='phrase_table_filename',
        required=True,
        help='The text for the phrase table, with scoring.')
    parser.add_argument('-a', '--alignments', dest='alignment_filename',
        required=True,
        help='The text for the old alignments.')
    parser.add_argument('-l', '--max-phrase-len', dest='max_phrase_len',
        type=int, default=4,
        help='Maximum phrase length allowed')
    parser.add_argument('-n', '--num-phrases', dest='num_phrases',
        type=int, default=sys.maxint,
        help='Maximum number of phrases allowed, truncated based on phrase probability')
    parser.add_argument('-v', '--verbose', dest='verbose',
        action='store_true', default=False,
        help='Verbose mode (default=off)')

    opts = parser.parse_args()
    return opts

def main():
    opts = setup_parser()
    phrase_table = TM(opts.phrase_table_filename,
                      opts.max_phrase_len,
                      opts.num_phrases)
    max_sent_len = 25

    num_phrase_aligned = 0
    num_not_aligned = 0

    sf = codecs.open(opts.source_filename, 'r', 'utf-8')
    tf = codecs.open(opts.target_filename, 'r', 'utf-8')
    af = codecs.open(opts.alignment_filename, 'r', 'utf-8')
    sline = sf.readline()
    tline = tf.readline()
    aline = af.readline()
    while sline and tline and aline:
        swords = sline.strip().split()
        twords = tline.strip().split()
        # We convert the string for the alignment pairs into a list of tuples
        # for alignment pairs.
        align_pairs = map(lambda pair_str: tuple(map(lambda x: int(x),
                                                     pair_str.split('-'))),
                          aline.strip().split())
        # We only do the optimal phrase based aligner if the sentence is under a
        # given length, due to performance concerns.
        if len(swords) <= max_sent_len:
            alignment = phrase_alignment(swords, twords,
                                               phrase_table,
                                               opts.max_phrase_len,
                                               opts.num_phrases)
            print ''
            if (alignment):
                num_phrase_aligned += 1
            else:
                num_not_aligned += 1
        # Sentence is too long, so it will be too slow to use the standard
        # phrase-based aligner.
        else:
            alignment = align_pairs
        # Get next lines and repeat
        sline = sf.readline()
        tline = tf.readline()
        aline = af.readline()
    if (sline):
        sys.stderr.write('Error: source sentence file was longer than'
                         + ' cooresponding target sentence file')
    if (tline):
        sys.stderr.write('Error: target sentence file was longer than'
                         + ' cooresponding source sentence file')

    print("NUMBER of correctly aligned = %d", num_phrase_aligned)
    print("NUMBER unable to align = %d", num_not_aligned)


def coverage(sequence):
    # Generate a coverage for a sequence of indexes #
    # You can do things like:
    #   c1 | c2 to "add" coverages
    #   c1 & c2 will return 0 if c1 and c2 do NOT overlap
    #   c1 & c2 will be != 0 if c1 and c2 DO overlap
    return reduce(lambda x,y: x|y, map(lambda i: long(1) << i, sequence), 0)

def phrase_alignment(f, e, tm, n, k):
    f = tuple(map(lambda s: s.lower(), f))
    e = tuple(map(lambda s: s.lower(), e))

    print f
    print e

    # alignments[i] is a list of all the phrases in f that could have
    # generated phrases starting at position i in e
    alignments = [[] for _ in e]
    for fi in xrange(len(f)):
        for fj in xrange(fi+1,len(f)+1):
            if f[fi:fj] in tm:
                for phrase in tm[f[fi:fj]]:
                    ephrase = tuple(phrase.english.split())
                    for ei in xrange(len(e)+1-len(ephrase)):
                        ej = ei+len(ephrase)
                        if ephrase == e[ei:ej]:
                            alignments[ei].append((ej, phrase.prob, fi, fj))
    # Sort each possible phrase translation by descending probability.
    for i, alignment in enumerate(alignments):
        alignment.sort(key=lambda x: -x[1])
        alignments[i] = alignment[:k]


    # Compute sum of probability of all possible alignments by dynamic programming.
    # To do this, recursively compute the sum over all possible alignments for each
    # each pair of English prefix (indexed by ei) and French coverage (indexed by
    # coverage v), working upwards from the base case (ei=0, v=0) [i.e. forward chaining].
    # The final sum is the one obtained for the pair (ei=len(e), v=range(len(f))
    sum_data = namedtuple("sum_data", "prob, alignments")
    chart = [{} for _ in e] + [{}]
    chart[0][0] = sum_data(0.0, [])
    for ei, sums in enumerate(chart[:-1]):
        for v in sums:
            for ej, prob, fi, fj in alignments[ei]:
                if coverage(range(fi,fj)) & v == 0:
                    new_v = coverage(range(fi,fj)) | v
                    next_prob = sums[v].prob * prob
                    old_alignments = sums[v].alignments
                    # Append the newest phrase alignment to the list of alignments.
                    new_alignments = old_alignments + [((ei, ej), (fi, fj))]
                    if new_v in chart[ej]:
                        if chart[ej][new_v].prob < next_prob:
                            chart[ej][new_v] = sum_data(next_prob, new_alignments)
                        # chart[ej][new_v] = logadd(chart[ej][new_v], sums[v]+logprob)
                    else:
                        chart[ej][new_v] = sum_data(next_prob, new_alignments)
                        # chart[ej][new_v] = sums[v]+logprob
    goal = coverage(range(len(f)))
    if goal in chart[len(e)]:
        print ("SUCCESS: WE ALIGNED THE SENTENCE")
        return chart[len(e)][goal].alignments
    else:
        # sys.stderr.write("ERROR: COULD NOT ALIGN SENTENCE\n")
        print ("ERROR: COULD NOT ALIGN SENTENCE")
        return None



# A translation model is a dictionary where keys are tuples of French words
# and values are lists of (english, logprob) named tuples. For instance,
# the French phrase "que se est" has two translations, represented like so:
# tm[('que', 'se', 'est')] = [
#     phrase(english='what has', logprob=-0.301030009985),
#     phrase(english='what has been', logprob=-0.301030009985)]
# k is a pruning parameter: only the top k translations are kept for each f.
def TM(filename, max_len, k):
    sys.stderr.write("Reading translation model from %s...\n" % (filename,))
    tm = {}
    with codecs.open(filename, 'r', 'utf-8') as pt_text:
        for line in pt_text:
            pt_entry = line.strip().split(" ||| ")
            f = pt_entry[0].lower()
            e = pt_entry[1].lower()
            p = float(pt_entry[2].split()[0])
            # We only record phrases under a given length
            if (len(f.split()) <= max_len and len(e.split()) <= max_len):
                tm.setdefault(tuple(f.split()), []).\
                    append(phrase(e, float(p)))
    # prune all but the top k translations
    for f in tm:
        tm[f].sort(key=lambda x: -x.prob)
        del tm[f][k:]
    return tm


if (__name__ == '__main__'):
    main()
