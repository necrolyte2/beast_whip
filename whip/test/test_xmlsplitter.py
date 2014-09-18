from lxml import etree

from common import *

from whip.xmlsplitter import InvalidBeastXmlError

class BaseTester(MultipleInhBase):
    def setUp(self):
        super(BaseTester,self).setUp()

    def _C( self, *args, **kwargs ):
        '''
        Trying this out to try and get rid of redundant code
        '''
        m = __import__( self.modulepath, fromlist=[self.functionname] )
        return getattr(m,self.functionname)( *args, **kwargs )

class BaseXmlSplitter(BaseTester):
    modulepath = 'whip.xmlsplitter'
    def setUp( self ):
        super(BaseXmlSplitter,self).setUp()
        self.xmlstr = '<?xml version="1.0" standalone="yes"?>\n'
        self.xmlstr += '<beast>\n'

    def _xml( self, xmlstr ):
        xmlstr += '</beast>\n'
        return etree.fromstring(xmlstr)

class TestSetDimensions(BaseXmlSplitter):
    functionname = 'set_dimensions'
    
    def test_xml_missing_dimensions( self ):
        # Nothing to check really other than no exception
        self._C( self._xml(self.xmlstr), 100 )

    def test_sets_dimensions_for_parameter_only( self ):
        self.xmlstr += '<parameter id="skyride.logPopSize" dimension="1440" value="3.9512437185814275"/>\n'
        self.xmlstr += '<groupSizes><parameter id="skyride.groupSize" dimension="1440"/></groupSizes>\n'
        xml = self._xml(self.xmlstr)
        self._C( xml, 5 )
        xmlstr = etree.tostring( xml )
        ok_( 'dimension="1440"' not in xmlstr )
        ok_( 'dimension="4"' in xmlstr )

class TestSplitXml(BaseXmlSplitter,BaseTempDir):
    functionname = 'split_xml'

    def setUp( self ):
        super(TestSplitXml,self).setUp()

    def tearDown( self ):
        super(TestSplitXml,self).tearDown()

    def _writexmlfile( self, xml, xmlfilepath ):
        with open(xmlfilepath,'w') as fh:
            fh.write( etree.tostring(xml) )

    def _taxseqxml( self, num ):
        taxons = ['<taxon id="seq{0}"></taxon>'.format(i) for i in range(num)]
        sequences = ['<sequence><taxon idref="seq{0}"/>ATGC</sequence>'.format(i) for i in range(num)]

        self.xmlstr += '<taxa id="taxa">{0}</taxa>\n'.format(''.join(taxons))
        self.xmlstr += '<alignment id="alignment" dataType="nucleotide">{0}</alignment>\n'.format(''.join(sequences))
        self.xmlstr += '<parameter id="skyride.logPopSize" dimension="{0}" value="3.9512437185814275"/>\n'.format(num)
        self.xmlstr += '<groupSizes><parameter id="skyride.groupSize" dimension="{0}"/></groupSizes>\n'.format(num)

        return self._xml(self.xmlstr)

    def test_splits_into_correct_amount_of_files( self ):
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

class TestGetAllIDtaxaSeqtaxa(BaseXmlSplitter):
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
