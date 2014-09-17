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
        from whip.beagleoptimiser import kwargs_to_options
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
        from whip.beagleoptimiser import estimate_beast_runtime
        return estimate_beast_runtime( *args, **kwargs )

    def test_waits_for_hours_million_line( self ):
        with patch( 'whip.beagleoptimiser.Popen',
                self.mock_beast(6.5) ) as p:
            r = self._C( self.beastfiles[0], 999, **{'-beagle_SSE':True} ) 
        assert_almost_equal( 0.65, r )

    @attr('current')
    def test_output_goes_to_specified_location( self ):
        sout = StringIO()
        r = self._C( self.beastfiles[0], 999, stream=sout, **{'-beagle_SSE':True} )
        output = sout.getvalue()
        ok_( 'beast -overwrite -seed 999 -beagle_SSE' in output )
        ok_( 'BEAST v' in output )
        ok_( 'hours/billion' in output )

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
        from whip.beagleoptimiser import get_chainlength
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
        from whip.beagleoptimiser import get_hours_per_million
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

class TestPrettyTime(object):
    def _C( self, *args, **kwargs ):
        from whip.beagleoptimiser import pretty_time
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
        r = self._C( sys.maxint )
        eq_( 'INF', r )

class BeagleOptions(object):
    def _make_resource( self, *args, **kwargs ):
        ''' Produce a -beagle_info resource string '''
        fmt = "{index} : {name}\n"
        if 'GPU' in kwargs['flags']['processor']:
            gpufmt = '    Global memory (MB): {memory}\n'
            gpufmt += '    Clock speed (Ghz): {clockspeed}\n'
            gpufmt += '    Number of cores: {corecount}\n'
            fmt += gpufmt.format(**kwargs)
        fmt += "    Flags: {flags}\n"
        fmt += "\n\n"

        return fmt.format(
            index=kwargs['index'],
            name=kwargs['name'],
            flags=self._make_flags(**kwargs['flags'])
        )

    def _make_flags( self, **flags ):
        '''
        Produce flags string
        vector_sse - If true than VECTOR_SSE will be added
        processor - PROCESSOR_CPU or PROCESSOR_GPU
        framework - FRAMEWORK_CPU or FRAMEWORK_CUDA
        '''
        if flags.get('vector_sse', False):
            flags['vector_sse'] = ' VECTOR_SSE'
        else:
            flags['vector_sse'] = ''
            
        flags_str = 'PRECISION_SINGLE PRECISION_DOUBLE COMPUTATION_SYNCH' \
            ' EIGEN_REAL EIGEN_COMPLEX SCALING_MANUAL SCALING_AUTO ' \
            'SCALING_ALWAYS SCALERS_RAW SCALERS_LOG{vector_sse} ' \
            'VECTOR_NONE THREADING_NONE {processor} {framework}'
        return flags_str.format( **flags )

    def test_creates_correct_cpu_resource_string( self ):
        r = self._make_resource(
            index=0,
            name='CPU',
            flags={
                'vector_sse': True,
                'processor': 'PROCESSOR_CPU',
                'framework': 'FRAMEWORK_CPU'
            }
        )

        cpu_resource = '''0 : CPU
    Flags: PRECISION_SINGLE PRECISION_DOUBLE COMPUTATION_SYNCH EIGEN_REAL EIGEN_COMPLEX SCALING_MANUAL SCALING_AUTO SCALING_ALWAYS SCALERS_RAW SCALERS_LOG VECTOR_SSE VECTOR_NONE THREADING_NONE PROCESSOR_CPU FRAMEWORK_CPU


'''
        eq_( cpu_resource, r )

    def test_creates_correct_gpu_resource_string( self ):
        r = self._make_resource(
            index=1,
            name='Tesla C2075',
            memory=5375,
            clockspeed=1.15,
            corecount=448,
            flags={
                'processor': 'PROCESSOR_GPU',
                'framework': 'FRAMEWORK_CUDA'
            }
        )

        gpu_resource = '''1 : Tesla C2075
    Global memory (MB): 5375
    Clock speed (Ghz): 1.15
    Number of cores: 448
    Flags: PRECISION_SINGLE PRECISION_DOUBLE COMPUTATION_SYNCH EIGEN_REAL EIGEN_COMPLEX SCALING_MANUAL SCALING_AUTO SCALING_ALWAYS SCALERS_RAW SCALERS_LOG VECTOR_NONE THREADING_NONE PROCESSOR_GPU FRAMEWORK_CUDA


'''
        eq_( gpu_resource, r )

    def _mock_beagle_info( self, resourcestring ):
        ''' Mock popen call that runs beast -beagle_info '''
        beagle_info = Mock()
        str = 'IGNORE THIS STUFF'
        str += '\n\n'
        str += 'BEAGLE resources available:\n'
        str += resourcestring
        beagle_info.communicate.return_value = (str,'')
        return Mock(return_value=beagle_info)

    def _expected_beagle_instances( self, baseoption ):
        inst = []
        for i in range(2, multiprocessing.cpu_count()+1, 2):
            inst.append( '{0} -beagle_instances {1}'.format(baseoption, i) )
        return inst

class TestGetAvailableBeagleOptions(BeagleOptions):
    def setUp(self):
        self.resources = []
        self.resources.append(
            self._make_resource(
                index=0,
                name='CPU',
                flags={
                    'vector_sse': True,
                    'processor': 'PROCESSOR_CPU',
                    'framework': 'FRAMEWORK_CPU'
                }
            )
        )
        self.resources.append(
            self._make_resource(
                index=1,
                name='Graphics card',
                memory=1024,
                corecount=192,
                clockspeed=1.2,
                flags={
                    'processor': 'PROCESSOR_GPU',
                    'framework': 'FRAMEWORK_CUDA'
                }
            )
        )
        self.resources.append(
            self._make_resource(
                index=1,
                name='Graphics card 2',
                memory=1024,
                corecount=192,
                clockspeed=1.2,
                flags={
                    'processor': 'PROCESSOR_GPU',
                    'framework': 'FRAMEWORK_CUDA'
                }
            )
        )

    def _C( self, *args, **kwargs ):
        from whip.beagleoptimiser import get_available_beagle_options
        return get_available_beagle_options( *args, **kwargs )

    def test_gets_beaglesse_for_vector_sse( self ):
        expected_options = [
            '-beagle_SSE',
        ] + self._expected_beagle_instances('-beagle_SSE')
        resource = self._mock_beagle_info( self.resources[0] )
        with patch('whip.beagleoptimiser.Popen', resource):
            r = self._C()
            eq_( sorted(expected_options), sorted(r) )

    def test_gets_correct_gpu_options( self ):
        resource = self._make_resource(
            index=0,
            name='Graphics card',
            memory=1024,
            corecount=192,
            clockspeed=1.2,
            flags={
                'processor': 'PROCESSOR_GPU',
                'framework': 'FRAMEWORK_CUDA'
            }
        )
        expected_options = [
            '-beagle_GPU',
        ] + self._expected_beagle_instances('-beagle_GPU')
        resource = self._mock_beagle_info( self.resources[1] )
        with patch('whip.beagleoptimiser.Popen', resource):
            r = self._C()
            eq_( sorted(expected_options), sorted(r) )

    def test_gets_correct_cpu_and_gpu_options( self ):
        expected_options = [
            '-beagle_SSE',
            '-beagle_GPU',
        ] + self._expected_beagle_instances('-beagle_SSE') \
          + self._expected_beagle_instances('-beagle_GPU')
        resource = self._mock_beagle_info(
            self.resources[0] + self.resources[1] + self.resources[2]
        )
        with patch('whip.beagleoptimiser.Popen', resource):
            r = self._C()
            eq_( sorted(expected_options), sorted(r) )

class TestRunBeastOptions(BeagleOptions, BaseTempDir):
    def setUp( self ):
        super(TestRunBeastOptions,self).setUp()
        from whip.beagleoptimiser import get_available_beagle_options
        self.avail_options = [
            '-beagle_SSE',
            '-beagle_SSE -beagle_instances 2',
            '-beagle_SSE -beagle_instances 4',
            '-beagle_SSE -beagle_instances 6',
            '-beagle_GPU',
            '-beagle_GPU -beagle_instances 2',
            '-beagle_GPU -beagle_instances 4',
            '-beagle_GPU -beagle_instances 6',
        ]

    def _C( self, *args, **kwargs ):
        from whip.beagleoptimiser import run_beast_options
        return run_beast_options( *args, **kwargs )

    def test_excludelist_excludes_options( self ):
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime'),
            ) as (p1, p2):
            times = [random.random() for i in range(8)]
            p1.return_value = self.avail_options
            p2.side_effect = times
            stringstream = StringIO()

            self._C(
                self.beastfiles[0],
                stream=stringstream,
                excludelist=['-beagle_GPU','-beagle_CPU -beagle_instances']
            )

            output = stringstream.getvalue()
            ok_( '-beagle_GPU -beagle_instances 2' not in output )
            ok_( '-beagle_CPU -beagle_instances' not in output )

    def test_sends_to_correct_output_stream( self ):
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime'),
            ) as (p1, p2):
            times = [random.random() for i in range(8)]
            p1.return_value = self.avail_options
            p2.side_effect = times
            stringstream = StringIO()
            self._C( self.beastfiles[0], stream=stringstream )
            output = stringstream.getvalue()

            ok_( '-beagle_SSE estimate: ' in output )
            ok_( '-beagle_SSE -beagle_instances 2 estimate: ' in output )

    def test_picks_correctly( self ):
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime')
            ) as (p1, p2):
            times = [random.random() for i in range(8)]
            p1.return_value = self.avail_options
            p2.side_effect = times
            
            r = self._C( self.beastfiles[0] )
            expected = zip( self.avail_options, times )
            expected.sort( key=lambda x: x[1] )
            eq_( expected, r )

    def test_handles_bad_beast_run_exception( self ):
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime')
            ) as (p1, p2):
            times = [random.random() for i in range(8)]
            p1.return_value = self.avail_options
            times[4] = ValueError
            p2.side_effect = times
            
            r = self._C( self.beastfiles[0] )
            times[4] = sys.maxint
            expected = zip( self.avail_options, times )
            expected.sort( key=lambda x: x[1] )
            eq_( expected, r )
