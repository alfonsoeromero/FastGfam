#!/usr/bin/env python
"""Command line script that finds all the regions of a given set
of sequences that are not assigned to any InterPro domain in a
given InterPro domain assignment file
"""

import bisect
import optparse
import sys

from Bio import SeqIO
from gfam.interpro import AssignmentReader
from gfam.scripts import CommandLineApp
from gfam.utils import Sequence, open_anything

__author__  = "Tamas Nepusz"
__email__   = "tamas@cs.rhul.ac.uk"
__copyright__ = "Copyright (c) 2010, Tamas Nepusz"
__license__ = "GPL"

class FindUnassignedApp(CommandLineApp):
    """\
    Usage: %prog [options]

    Given the InterPro assignments for a genome, finds all the regions
    that were not assigned to any InterPro domain and outputs these
    regions in the following format:

      seqID1 start1 end1
      seqID2 start2 end2
      ...

    A sequence ID may appear many times in the first column when multiple
    unassigned regions are present. Starting and ending coordinates are
    both inclusive and start from 1.
    """

    short_name = "find_unassigned"

    def __init__(self):
        super(FindUnassignedApp, self).__init__()
        self.seqcat = {}

    def create_parser(self):
        """Creates the command line parser used by this script"""
        parser = super(FindUnassignedApp, self).create_parser()
        parser.add_option("-l", "--min-length", dest="min_length",
                metavar="LENGTH",
                help="minimum sequence LENGTH needed for a sequence in order to include its fragments in the output",
                default=0, type=int)
        parser.add_option("-f", "--min-fragment-length", dest="min_fragment_length",
                metavar="LENGTH",
                help="minimum fragment LENGTH needed in the output",
                default=0, type=int)
        parser.add_option("-S", "--sequences",
                dest="sequences_file", metavar="FILE",
                help="FASTA file containing all the sequences of the representative gene model",
                default=None)
        return parser

    def run_real(self):
        self.process_sequences_file(self.options.sequences_file)

        for infile in (self.args or ["-"]):
            self.process_infile(infile)

        self.print_unassigned()

    def process_sequences_file(self, fname):
        self.seq_ids_to_length = {}
        for seq in SeqIO.parse(open_anything(fname), "fasta"):
            self.seq_ids_to_length[seq.id] = len(seq.seq)

    def process_infile(self, fname):
        for assignment in AssignmentReader(fname):
            try:
                seq = self.seqcat[assignment.id]
            except KeyError:
                seq = Sequence(assignment.id, assignment.length)
                self.seqcat[assignment.id] = seq
            if seq.length != assignment.length:
                raise ValueError, "different lengths encountered for %s: %d and %d" % (seq.name, seq.length, assignment.length)
            seq.assign(assignment)

    def print_unassigned(self):
        for seqID, seq in self.seqcat.iteritems():
            if seq.length < self.options.min_length:
                continue
            for start, end in seq.unassigned_regions():
                if end-start+1 < self.options.min_fragment_length:
                    continue
                print "%s\t%d\t%d" % (seqID, start, end)
        for seqID in set(self.seq_ids_to_length.keys()) - set(self.seqcat.keys()):
            print "%s\t1\t%d" % (seqID, self.seq_ids_to_length[seqID])


if __name__ == "__main__":
    sys.exit(FindUnassignedApp().run())