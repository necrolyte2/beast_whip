#!/usr/bin/env python

from whip.xmlsplitter import split_xml, parse_args

def main(args):
    split_xml( args.xmlfile, args.numfiles )

if __name__ == '__main__':
    main(parse_args())
