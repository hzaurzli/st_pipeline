#! /usr/bin/env python
#@Author Jose Fernandez
""" 
Script that parses the tab delimited file
generated from countClusters.py with clusters
and barcodes to a data frame format like this :

    cluster1.....clusterN
BC1 
BC2
...
BCN

It needs the original BED file with ST data to extract the reads count 
"""

import argparse
import sys
from collections import defaultdict
from stpipeline.common.utils import fileOk

def main(input_files, use_density, outfile=None, new_paraclu=False):
    
    if len(input_files) != 2:
        sys.stderr.write("Error, input file not present or invalid format\n")
        sys.exit(-1)

    bed_file = input_files[0]
    original_file = input_files[1]
    
    if not fileOk(bed_file) or not fileOk(original_file):
        sys.stderr.write("Error, input file not present or invalid format\n")
        sys.exit(-1)
     
    if outfile is None:
        outfile = "output_table_" + bed_file
           
    # load all the original barcode - gene - count
    map_original_clusters = defaultdict(list)
    with open(original_file, "r") as filehandler:
        for line in filehandler.readlines():
            if line.find("Chromosome") == -1:
                tokens = line.split()
                chromosome = str(tokens[0])
                start_site = str(tokens[1])
                end_site = str(tokens[2])
                strand = str(tokens[5])
                #gene = tokens[6]
                barcode = str(tokens[7])
                map_original_clusters[(barcode,chromosome,strand)].append((int(start_site),int(end_site)))
            
    # loads all the clusters
    map_clusters = defaultdict(int)
    clusters = set()
    barcodes = set()
    value_index = 5
    if use_density:
        value_index = 6
    with open(bed_file, "r") as filehandler:
        for line in filehandler.readlines():
            if line.find("#") == -1:
                tokens = line.split()
                barcode = str(tokens[8])
                chromosome = str(tokens[0])
                strand = str(tokens[1])
                start = int(tokens[2])
                end = int(tokens[3])
                if new_paraclu:
                    map_clusters[(barcode,chromosome,strand,start,end)] = int(tokens[value_index])
                else:
                    # doing a full search of intersections over all barcodes
                    # If we could rely on that no barcodes were missing doing the clustering we could
                    # a faster approach not needing to iterate all the barcodes but only one   
                    # this intersection method is prob overcounting
                    for key,value in map_original_clusters.iteritems():
                        barcode_original_file = key[0]
                        chr_original_file = key[1]
                        strand_original_file = key[2]
                        if chromosome == chr_original_file and strand == strand_original_file:
                            for start_original_file,end_original_file in value:
                                if (start_original_file >= start and start_original_file <= end) \
                                or (end_original_file <= end and end_original_file >= start):
                                    map_clusters[(barcode_original_file,chromosome,strand,start,end)] += 1
                barcodes.add(barcode)
                clusters.add((chromosome,strand,start,end))    
    
    # write cluster count for each barcode 
    with open(outfile, "w") as filehandler:
        filehandler.write("Cluster")
        for chr,strand,star,end in clusters:
            filehandler.write("\t" + chr + ":" + str(star) + "-" + str(end) + "," + str(strand))
        filehandler.write("\n")
        for bc in barcodes:
            filehandler.write(bc)
            for chr,strand,star,end in clusters:
                count = map_clusters[(bc,chr,strand,star,end)]
                filehandler.write("\t" + str(count))
            filehandler.write("\n")            
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_files', nargs=2, 
                        help="The tab delimited file containing the clusters and the ST original BED file")
    parser.add_argument("--outfile", help="Name of the output file")
    parser.add_argument("--use-density", 
                        action="store_true", 
                        default=False, help="Output the cluster width instead of the cluster count")
    parser.add_argument("--new-paraclu", action="store_true", 
                        default=False, help="Use new paraclu that outputs barcodes")
    args = parser.parse_args()
    main(args.input_files, args.use_density, args.outfile, args.new_paraclu)