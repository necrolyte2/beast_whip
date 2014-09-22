# coding: utf-8

from lxml import etree
import re
import argparse
import sys
from os.path import splitext, basename

# Exception for invalid Beast xml
class InvalidBeastXmlError(Exception): pass

def parse_args( args=sys.argv[1:] ):
    parser = argparse.ArgumentParser(
        description='Split a beast file into multiple xml files' \
            ' such that they can be run in parallel'
    )

    #per_split = 10
    parser.add_argument(
        '--nodes',
        '--files',
        dest='numfiles',
        type=int,
        default=2,
        help='How many resulting xml files do you want? This should probably ' \
            'match how many computers you will split the run across. Default: %(default)s'
    )

    parser.add_argument(
        dest='xmlfile',
        help='The xmlfile that should be split'
    )

    return parser.parse_args()

def get_all_idtaxa_seqtaxa( xml ):
    '''
    Get a zipped list of all <taxa><taxon>... and <alignment><taxa>...
    '''
    try:
        taxa = xml.xpath('taxa')[0]
    except IndexError as e:
        raise InvalidBeastXmlError('Missing taxa tag')
    try:
        alignment = xml.xpath('alignment')[0]
    except IndexError as e:
        raise InvalidBeastXmlError('Missing alignment tag')
    seqtaxa = alignment.findall('sequence')
    idtaxa = taxa.findall('taxon')
    if len(seqtaxa) != len(idtaxa):
        raise InvalidBeastXmlError(
            'There are not the same amount of alignment sequences as there are ' \
            ' taxa taxons'
        )
    z = zip(idtaxa,seqtaxa)
    return z

def remove_children( element ):
    '''
    Removes all children from an element
    element.clear seems to remove attributes too
    '''
    for child in element.getchildren():
        element.remove( child )

def clear_align_taxa( xml ):
    remove_children( xml.xpath('alignment')[0] )
    remove_children( xml.xpath('taxa' )[0] )

def set_filenames( xml, filename ):
    '''
    Sets the fileName options for any tags that have that attribute
    by essentially replacing whatever the value is before the extension with filename
    '''
    # Get only filename portion of filename
    filen = splitext(basename(filename))[0]

    # Should find any tag with attribute named fileName
    elements = xml.findall('.//*[@fileName]')

    if not elements:
        raise InvalidBeastXmlError(
            'Input xml does not contain any fileName attributes'
        )

    for element in elements:
        fn = splitext(basename(element.attrib['fileName']))[0]
        # Replace the filename in existing path with our filename name
        element.attrib['fileName'] = element.attrib['fileName'].replace(fn, filen)

def set_dimensions( xml, seq_per_file ):
    '''
    Sets the dimensions parameter for any tags to the number of sequences
    per file
    '''
    # Should find any parameter tag with attribute named dimension
    dimensions = xml.findall('.//parameter[@dimension]')

    # Loop through all found parameter tags with dimension in them
    for dim in dimensions:
        # Set it to 1 less than sequence number...for whatever reason
        dim.attrib['dimension'] = str(seq_per_file-1)

def evenly_split_iterable( iterable, numtimes ):
    '''
    Splits an interable into numtimes pieces that are as close as possible
    to the same size
    '''
    l = len(iterable)
    extra = l % numtimes
    splits = l / numtimes
    #print "Extra: " + str(extra)
    #print "Numtimes: " + str(numtimes)
    #print "Splits: " + str(splits)

    if extra != 0:
        splitmod = int((float(extra) / splits) + 1)
        #print "splitmod: " + str(splitmod)
        splits += splitmod

    for i,s in enumerate(range(0,l,splits)):
        start = s
        end = s+splits
        yield iterable[start:end]

def split_xml( xmlfile, numfiles ):
    '''
    Splits a given xmlfile file into numfiles number of smaller xml files

    TODO:
        Should warn the user or something if len(chunk) < 100
    '''
    xml = etree.parse(xmlfile)
    idseq = get_all_idtaxa_seqtaxa( xml )

    for i, chunk in enumerate(evenly_split_iterable(idseq, numfiles), start=1):
        remove_children( xml.xpath('alignment')[0] )
        remove_children( xml.xpath('taxa' )[0] )
        for itaxa, staxa in chunk:
            splitfile = 'split_{0}.xml'.format(i)
            xml.xpath('taxa')[0].append(itaxa)
            xml.xpath('alignment')[0].append(staxa)
            set_dimensions(xml, len(chunk))
            set_filenames(xml,splitfile)
            with open(splitfile,'w') as fh:
                xml.write(fh)
