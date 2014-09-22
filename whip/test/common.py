import os
import sys
from os.path import *
import tempfile
import shutil
import subprocess
import multiprocessing
import random
from StringIO import StringIO
import contextlib

from mock import Mock, patch
from nose.tools import eq_, ok_, raises, assert_almost_equal
from nose.plugins.attrib import attr

from lxml import etree

# Shortcut to directory this file is in
THIS = dirname(abspath(__file__))

class MultipleInhBase(object):
    '''
    Conused by multiple inheritance I think
    So you have to call super all the way up the chain
    So hacky hackerton here to the rescue
    Read this or something:
    http://nedbatchelder.com/blog/201210/multiple_inheritance_is_hard.html
    '''
    def setUp(self):
        sup = super(MultipleInhBase,self)
        if hasattr(sup,'setUp'):
            sup.setUp()

    def tearDown(self):
        sup = super(MultipleInhBase,self)
        if hasattr(sup,'tearDown'):
            sup.tearDown()

class BeastBase(MultipleInhBase):
    def setUp( self ):
        super(BeastBase,self).setUp()
        self.mrbayesfiles = [
            join( THIS, 'mrbayes.nex' ),
        ]

        self.beastfiles = [
            join( THIS, 'beast.xml' ),
            join( THIS, 'benchmark1.xml' ),
            join( THIS, 'benchmark2.xml' ),
        ]

    def _fake_popen( self, stdout, stderr, sleeptime ):
        def wait_stdout( self ):
            import time
            for line in stdout.splitlines():
                time.sleep(sleeptime)
                yield line

        def wait_stderr( self ):
            import time
            for line in stderr.splitlines():
                time.sleep(sleeptime)
                yield line

        m = Mock(spec=subprocess.Popen)
        sout = Mock()
        sout.read = stdout
        sout.__iter__ = wait_stdout

        serr = Mock()
        serr.read = stderr
        serr.__iter__ = wait_stderr
        
        m.return_value.stdout = sout
        m.return_value.stderr = serr
        return m

    def mock_beast( self, hpm, sleeptime=0.01 ):
        output = '''
a whole lot of stuff 
that 
should be ignored
state    Posterior       Prior           Likelihood      rootHeight      uced.mean   
0    -146157.0121    -6973.1750      -139183.8371    37.0010         1.00000         -
10000    -92741.3088     -10087.6418     -82653.6670     50.6558         13.4161         -
20000    -85760.1142     -9831.5681      -75928.5461     47.0661         12.7912         {hpm} hours/million states
30000    -80843.8855     -9745.0147      -71098.8708     45.9425         11.1163         6.45 hours/million states
'''.format(hpm=hpm)
        beast = self._fake_popen( output, '', sleeptime )
        return beast

class BaseTempDir(BeastBase):
    def setUp( self ):
        super(BaseTempDir,self).setUp()
        self.setupdir = tempfile.mkdtemp( 
            prefix='beagleoptimiizer',
            suffix='setup'
        )
        os.chdir( self.setupdir )

    def tearDown( self ):
        os.chdir( '/' )
        shutil.rmtree( self.setupdir )

class BaseTester(MultipleInhBase):
    def setUp(self):
        super(BaseTester,self).setUp()

    def _C( self, *args, **kwargs ):
        '''
        Trying this out to try and get rid of redundant code
        '''
        m = __import__( self.modulepath, fromlist=[self.functionname] )
        return getattr(m,self.functionname)( *args, **kwargs )

class BaseXml(BaseTester):
    def setUp( self ):
        super(BaseXml,self).setUp()
        self.xmlstr = '<?xml version="1.0" standalone="yes"?>\n'
        self.xmlstr += '<beast>\n'

    def _taxseqxml( self, num ):
        taxons = ['<taxon id="seq{0}"></taxon>'.format(i) for i in range(num)]
        sequences = ['<sequence><taxon idref="seq{0}"/>ATGC</sequence>'.format(i) for i in range(num)]

        self.xmlstr += '<taxa id="taxa">{0}</taxa>\n'.format(''.join(taxons))
        self.xmlstr += '<alignment id="alignment" dataType="nucleotide">{0}</alignment>\n'.format(''.join(sequences))
        self.xmlstr += '<parameter id="skyride.logPopSize" dimension="{0}" value="3.9512437185814275"/>\n'.format(num)
        self.xmlstr += '<groupSizes><parameter id="skyride.groupSize" dimension="{0}"/></groupSizes>\n'.format(num)

        return self._xml(self.xmlstr)

    def _writexmlfile( self, xml, xmlfilepath ):
        with open(xmlfilepath,'w') as fh:
            if isinstance(xml,str):
                fh.write(xml)
            else:
                fh.write( etree.tostring(xml) )

    def _add_filename_log_xml( self, filename ):
        self.xmlstr += '''
            <log id="fileLog" logEvery="1000" fileName="{0}.log" overwrite="true">
                <posterior idref="posterior"/>
                <prior idref="prior"/>
                <likelihood idref="likelihood"/>
                <parameter idref="treeModel.rootHeight"/>
                <parameter idref="constant.popSize"/>
                <parameter idref="kappa"/>
                <parameter idref="frequencies"/>
                <parameter idref="clock.rate"/>
                <treeLikelihood idref="treeLikelihood"/>
                <coalescentLikelihood idref="coalescent"/>
            </log>

            <logTree id="treeFileLog" logEvery="1000" nexusFormat="true" fileName="{0}.trees" sortTranslationTable="true">
                <treeModel idref="treeModel"/>
                <strictClockBranchRates idref="branchRates"/>
                <posterior idref="posterior"/>
            </logTree>
        '''.format(filename)

    def _xml( self, xmlstr ):
        xmlstr += '</beast>\n'
        return etree.fromstring(xmlstr)

