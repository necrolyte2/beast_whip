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
        getattr(super(BeastBase),'setUp',None)
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
