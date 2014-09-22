from common import *

from whip.xmlsplitter import InvalidBeastXmlError

class Base(BaseXml):
    modulepath = 'whip.xmlsplitter'

class TestSetFilenames(Base):
    functionname = 'set_filenames'

    @raises(InvalidBeastXmlError)
    def test_xml_missing_filename_attribute( self ):
        xml = self._xml(self.xmlstr)
        self._C( xml, 'test.log' )

    def test_replaces_log_and_logtree( self ):
        self._add_filename_log_xml('beast')
        xml = self._xml(self.xmlstr)
        self._C( xml, 'split_0.xml' )
        xmlstr = etree.tostring( xml )
        print xmlstr
        ok_( 'fileName="split_0.log"' in xmlstr )
        ok_( 'fileName="split_0.trees"' in xmlstr )
        ok_( 'beast.log' not in xmlstr )
        ok_( 'beast.trees' not in xmlstr )

    def test_any_tag_with_fileName_attr( self ):
        self.xmlstr += '<mytag id="myTag" fileName="replace.me" />\n'
        xml = self._xml(self.xmlstr)
        self._C( xml, '/some/path/with.this' )
        xmlstr = etree.tostring( xml )
        print xmlstr
        ok_( 'with.me' in xmlstr )
        ok_( 'replace.me' not in xmlstr )

class TestSetDimensions(Base):
    functionname = 'set_dimensions'
    
    def test_xml_missing_dimensions( self ):
        # Nothing to check really other than no exception
        self._C( self._xml(self.xmlstr), 100 )

    def test_sets_dimensions_correctly( self ):
        xml = self._taxseqxml( 10 )
        self._C( xml, 5 )
        xmlstr = etree.tostring( xml )
        print xmlstr
        ok_( 'dimension="4"' in xmlstr )
        ok_( 'dimension="10"' not in xmlstr )
        
    def test_sets_dimensions_for_parameter_only( self ):
        self.xmlstr += '<parameter id="skyride.logPopSize" dimension="1440" value="3.9512437185814275"/>\n'
        self.xmlstr += '<groupSizes><parameter id="skyride.groupSize" dimension="1440"/></groupSizes>\n'
        xml = self._xml(self.xmlstr)
        self._C( xml, 5 )
        xmlstr = etree.tostring( xml )
        ok_( 'dimension="1440"' not in xmlstr )
        ok_( 'dimension="4"' in xmlstr )

class TestSplitXml(Base,BaseTempDir):
    functionname = 'split_xml'

    def test_splits_into_correct_amount_of_files( self ):
        self._add_filename_log_xml('beast')
        xml = self._taxseqxml( 10 )
        self._writexmlfile( xml, 'input.xml' )
        self._C( 'input.xml', 2 )
        files = os.listdir('.')
        eq_( ['input.xml','split_1.xml','split_2.xml'], sorted(files) )
    
        s1xml = etree.parse('split_1.xml')
        s2xml = etree.parse('split_1.xml')
        
        s1 = s1xml.xpath('alignment')[0].findall('sequence')
        t1 = s1xml.xpath('taxa')[0].findall('taxon')
        eq_( 5, len(s1) )
        eq_( 5, len(t1) )
        
        s2 = s1xml.xpath('alignment')[0].findall('sequence')
        t2 = s1xml.xpath('taxa')[0].findall('taxon')
        eq_( 5, len(s2) )
        eq_( 5, len(t2) )

    def test_changes_dimension_parameter( self ):
        self._add_filename_log_xml('beast')
        xml = self._taxseqxml( 10 )
        self._writexmlfile( xml, 'input.xml' )
        self._C( 'input.xml', 2 )

        for f in ('split_1.xml','split_2.xml'):
            with open(f) as fh:
                contents = fh.read()
                print contents
                ok_( 'dimension="4"' in contents )
                ok_( 'dimension="10"' not in contents )

    def test_changes_filename_attributes( self ):
        self._add_filename_log_xml('beast')
        xml = self._taxseqxml( 10 )
        self._writexmlfile( xml, 'input.xml' )
        self._C('input.xml', 2)

        for f in ('split_1.xml','split_2.xml'):
            with open(f) as fh:
                contents = fh.read()
                print contents
                fn = splitext(f)[0]
                print fn
                ok_( 'fileName="'+fn in contents )
                ok_( 'fileName="beast.' not in contents )

class TestGetAllIDtaxaSeqtaxa(Base):
    functionname = 'get_all_idtaxa_seqtaxa'

    @raises(InvalidBeastXmlError)
    def test_missing_taxa( self ):
        self.xmlstr += '<alignment id="alignment" dataType="nucleotide"></alignment>\n'
        self._C( self._xml(self.xmlstr) )

    @raises(InvalidBeastXmlError)
    def test_missing_alignment( self ):
        self.xmlstr += '<taxa id="taxa"></taxa>\n'
        self._C( self._xml(self.xmlstr) )

    @raises(InvalidBeastXmlError)
    def test_idtaxa_not_same_length_as_seqtaxa( self ):
        self.xmlstr += '<taxa id="taxa"><taxon id="seq1"></taxon></taxa>\n'
        self.xmlstr += '<alignment id="alignment" dataType="nucleotide"></alignment>\n'
        self._C( self._xml(self.xmlstr) )

    def test_combines_idtaxa_and_seqtaxa( self ):
        self.xmlstr += '<taxa id="taxa"><taxon id="seq1"></taxon></taxa>\n'
        self.xmlstr += '<alignment id="alignment" dataType="nucleotide"><sequence><taxon idref="seq1"/>ATGC</sequence></alignment>\n'
        r = self._C( self._xml(self.xmlstr) )
        r = r[0]
        eq_( {'id':'seq1'}, r[0].attrib )
        eq_( {'idref':'seq1'}, r[1][0].attrib )

class TestEvenlySplitIterable(object):
    def setUp(self):
        # 1-10
        self.iterable = range(1,11)

    def _C( self, *args, **kwargs ):
        from whip.xmlsplitter import evenly_split_iterable
        return evenly_split_iterable( *args, **kwargs )

    def test_gets_correct_splits_for_1( self ):
        r = self._C( self.iterable, 1 )
        # Should not change
        eq_( [self.iterable], list(r) )

    def test_gets_correct_splits_for_2( self ):
        r = self._C( self.iterable, 2 )
        e = [
                [1,2,3,4,5],
                [6,7,8,9,10],
        ]
        eq_( e, list(r) )

    def test_gets_correct_splits_for_half( self ):
        r = self._C( self.iterable, 5 )
        e = [
            [1,2],
            [3,4],
            [5,6],
            [7,8],
            [9,10],
        ]
        eq_( e, list(r) )

    def test_gets_correct_splits_for_max( self ):
        r = self._C( self.iterable, 10 )
        e = [
            [1],
            [2],
            [3],
            [4],
            [5],
            [6],
            [7],
            [8],
            [9],
            [10]
        ]
        eq_( e, list(r) )

    def test_gets_correct_splits_for_odd( self ):
        r = self._C( self.iterable, 3 )
        e = [
            [1,2,3,4],
            [5,6,7,8],
            [9,10]
        ]
        r = list(r)
        eq_( e, r )

    def test_another_test( self ):
        iter = range(1,26)
        numfiles = 3
        r = self._C( iter, numfiles )
        r = list(r)
        e = [
            range(1,10),
            range(10,19),
            range(19,26)
        ]
        eq_( e, r )

    def test_yet_another_test( self ):
        iter = range(1,1442)
        numfiles = 7
        r = self._C( iter, numfiles )
        r = list(r)
        eq_( r[0][-1], 206 )
        eq_( r[1][-1], 412 )
        eq_( r[-1][-1], 1441 )
        eq_( numfiles, len(r) )
