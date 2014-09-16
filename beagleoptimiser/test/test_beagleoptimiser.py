import os
import sys
from os.path import *
import tempfile
import shutil
import subprocess

from mock import Mock, patch
from nose.tools import eq_, ok_, raises, assert_almost_equal
from nose.plugins.attrib import attr

# Shortcut to directory this file is in
THIS = dirname(abspath(__file__))

class BeastOptimiser(object):
    def setUp( self ):
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

    def mock_beast( self, sleeptime=0.01 ):
        output = '''
a whole lot of stuff 
that 
should be ignored
state    Posterior       Prior           Likelihood      rootHeight      uced.mean   
0    -146157.0121    -6973.1750      -139183.8371    37.0010         1.00000         -
10000    -92741.3088     -10087.6418     -82653.6670     50.6558         13.4161         -
20000    -85760.1142     -9831.5681      -75928.5461     47.0661         12.7912         6.5 hours/million states
30000    -80843.8855     -9745.0147      -71098.8708     45.9425         11.1163         6.45 hours/million states
Underflow calculating likelihood. Attempting a rescaling...
40000    -78239.7523     -9741.7722      -68497.9801     46.1185         9.90248         6.61 hours/million states
50000    -76595.3961     -9725.2361      -66870.1601     46.4219         9.55640         6.67 hours/million states
60000    -74763.2233     -9685.8863      -65077.3371     46.0076         9.10706         6.43 hours/million states
70000    -73224.9638     -9663.0780      -63561.8859     46.1451         9.02328         6.09 hours/million states
80000    -71819.2802     -9557.8338      -62261.4463     45.2624         9.26833         6.34 hours/million states
'''
        beast = self._fake_popen( output, '', sleeptime )
        return beast

class BaseTempDir(BeastOptimiser):
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


class TestKwargsToOptions(BeastOptimiser):
    def _C( self, *args, **kwargs ):
        from beagleoptimiser.beagleoptimiser import kwargs_to_options
        return kwargs_to_options( *args, **kwargs )

    def test_keyword_with_string_int_float_value( self ):
        r = self._C(
            **{
                '-a': 'string',
                '-b': 1,
                '-c': 1.0,
                '-d': True,
                '-e': False,
                '--long':'works',
            }
        )
        r = sorted( r )
        e = [
            ['--long','works'],
            ['-a','string'],
            ['-b','1'],
            ['-c','1.0'],
            '-d',
        ]
        eq_( e, r )

class TestEstimateBeastRuntime(BaseTempDir):
    def _C( self, *args, **kwargs ):
        from beagleoptimiser.beagleoptimiser import estimate_beast_runtime
        return estimate_beast_runtime( *args, **kwargs )

    def test_waits_for_hours_million_line( self ):
        with patch( 'beagleoptimiser.beagleoptimiser.Popen',
                self.mock_beast() ) as p:
            r = self._C( self.beastfiles[0], 999, **{'-beagle_SSE':True} ) 
        assert_almost_equal( 0.65, r )

    def test_run_with_actual_beast( self ):
        r = self._C( self.beastfiles[0], 999, **{'-beagle_SSE':True} )
        ok_( r is not None )
        r = self._C( self.beastfiles[0], 999, **{'-beagle_CPU':True} )
        ok_( r is not None )
        r = self._C( self.beastfiles[0], 999, **{'-beagle_GPU':True} )
        ok_( r is not None )

    def test_ensure_runs_in_tempdir( self ):
        r = self._C( self.beastfiles[0] )
        eq_( [], os.listdir('.') )

    def test_relative_path_to_xml_works( self ):
        rpath = relpath( self.beastfiles[0], os.getcwd() )
        print rpath
        r = self._C( rpath )
        ok_( r is not None )

class TestGetChainLength(BeastOptimiser):
    def _C( self, *args, **kwargs ):
        from beagleoptimiser.beagleoptimiser import get_chainlength
        return get_chainlength( *args, **kwargs )

    def test_gets_correct_chainlength_as_integer( self ):
        r = self._C( self.beastfiles[0] )
        eq_( 100000, r )
        r = self._C( self.beastfiles[1] )
        eq_( 100000, r )
        r = self._C( self.beastfiles[2] )
        eq_( 1000000, r )

class TestGetHoursPerMillion(BeastOptimiser):
    def _C( self, *args, **kwargs ):
        from beagleoptimiser.beagleoptimiser import get_hours_per_million
        return get_hours_per_million( *args, **kwargs )

    def test_gets_none_for_lines_with_no_hoursmillion( self ):
        line = '0\t-146157.0121\t-6973.1750\t-139183.8371\t37.0010\t1.00000\t-'
        r = self._C( line )
        eq_( None, r )

    def test_gets_none_for_non_state_table_lines( self ):
        line = 'arr I be a pirate\twith a parrot'
        r = self._C( line )
        eq_( None, r )

    def test_gets_float_for_state_table_lines_with_hours_millions( self ):
        line = '0\t-85760.1142\t-9831.5681\t-75928.5461\t' \
            '47.0661\t12.7912\t{0} hours/million states'
        r = self._C( line.format(6.5) )
        eq_( 6.5, r )
        r = self._C( line.format(0.01) )
        eq_( 0.01, r )

    def test_gets_float_for_state_table_lines_with_hours_billions( self ):
        line = '0\t-85760.1142\t-9831.5681\t-75928.5461\t' \
            '47.0661\t12.7912\t{0} hours/billion states'
        r = self._C( line.format(1.5) )
        eq_( 1.5 / 1000, r )

@attr('current')
class TestPrettyTime(object):
    def _C( self, *args, **kwargs ):
        from beagleoptimiser.beagleoptimiser import pretty_time
        return pretty_time( *args, **kwargs )

    def test_converts_to_days( self ):
        # Should be 1 day of hours
        r = self._C( 24.0 )
        eq_( '01:00:00:00.0', r )

    def test_converts_to_hours( self ):
        r = self._C( 1.0 )
        eq_( '00:01:00:00.0', r )

    def test_converts_to_minutes( self ):
        r = self._C( 1.0 / 60.0 )
        eq_( '00:00:01:00.0', r )

    def test_converts_to_seconds( self ):
        r = self._C( 1.0 / 3600 )
        eq_( '00:00:00:01.0', r )

    def test_converts_to_all( self ):
        r = self._C( 24.0 + 1.0 + (1.0 / 60.0) + (1.0 / 3600.0) )
        eq_( '01:01:01:01.0', r )

    def test_really_small_number( self ):
        r = self._C( 0.000258 )
        eq_( '00:00:00:00.928800', r )

    def test_really_big_number( self ):
        r = self._C( 256.0 )
        eq_( '10:16:00:00.0', r )
