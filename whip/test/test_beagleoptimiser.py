from common import *

from whip.beagleoptimiser import InvalidBeastXmlError

class Base(BaseXml):
    modulepath = 'whip.beagleoptimiser'

class TestKwargsToOptions(BeastBase):
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

class TestEstimateBeastRuntime(Base,BaseTempDir):
    functionname = 'estimate_beast_runtime'

    def test_waits_for_hours_million_line( self ):
        with patch( 'whip.beagleoptimiser.Popen',
                self.mock_beast(6.5) ) as p:
            r = self._C( self.beastfiles[0], 999, **{'-beagle_SSE':True} ) 
        assert_almost_equal( 0.65, r )

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

    @attr('current')
    def test_raises_value_error_when_no_hours_per_million_found( self ):
        sout = StringIO()
        # Write new beast xml file with small chainLength
        with open(self.beastfiles[0]) as ifh:
            with open('input.xml','w') as ofh:
                for line in ifh:
                    if 'chainLength' in line:
                        ofh.write( line.replace('100000','10000') )
                    else:
                        ofh.write( line )
        try:
            self._C( 'input.xml', stream=sout )
            ok_( False, 'Did not raise ValueError' )
        except ValueError as e:
            contents = sout.getvalue()
            ok_( 'Beast did not exit correctly' not in contents )

    @attr('current')
    def test_outputs_error_message_and_raises_error( self ):
        sout = StringIO()
        # Make a bad xml file to make beast break
        open('input.xml','w').close()
        try:
            self._C( 'input.xml', stream=sout )
        except ValueError as e:
            contents = sout.getvalue()
            ok_( 'Beast did not exit correctly' in contents )

class TestGetChainLength(BeastBase):
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

class TestGetHoursPerMillion(BeastBase):
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
        eq_( '1d 00:00:00.0', r )

    def test_converts_to_hours( self ):
        r = self._C( 1.0 )
        eq_( '01:00:00.0', r )

    def test_converts_to_minutes( self ):
        r = self._C( 1.0 / 60.0 )
        eq_( '00:01:00.0', r )

    def test_converts_to_seconds( self ):
        r = self._C( 1.0 / 3600 )
        eq_( '00:00:01.0', r )

    def test_converts_to_all( self ):
        r = self._C( 24.0 + 1.0 + (1.0 / 60.0) + (1.0 / 3600.0) )
        eq_( '1d 01:01:01.0', r )

    def test_really_small_number( self ):
        r = self._C( 0.000258 )
        eq_( '00:00:00.928800', r )

    def test_really_big_number( self ):
        r = self._C( sys.maxint )
        eq_( 'INF', r )

class BeagleOptions(Base):
    def setUp(self):
        super(BeagleOptions,self).setUp()
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
                index=2,
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
        self.resources.append(
            self._make_resource(
                index=3,
                name='Graphics card 3',
                memory=1024,
                corecount=192,
                clockspeed=1.2,
                flags={
                    'processor': 'PROCESSOR_GPU',
                    'framework': 'FRAMEWORK_CUDA'
                }
            )
        )


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

    def _test_creates_correct_cpu_resource_string( self ):
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

    def _test_creates_correct_gpu_resource_string( self ):
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

    def _expected_beagle_instances( self, baseoption, instances=multiprocessing.cpu_count() ):
        inst = []
        for i in range(2, instances+1, 2):
            inst.append( '{0} -beagle_instances {1}'.format(baseoption, i) )
        return inst

@patch('whip.beagleoptimiser.multiprocessing')
class TestGetAvailableBeagleOptions(BeagleOptions):
    functionname = 'get_available_beagle_options'

    def test_gets_beaglesse_for_vector_sse( self, cpucount ):
        cpucount.cpu_count.return_value = 8
        expected_options = [
            '-beagle_SSE',
        ] + self._expected_beagle_instances('-beagle_SSE')
        resource = self._mock_beagle_info( self.resources[0] )
        with patch('whip.beagleoptimiser.Popen', resource):
            r = self._C()
            eq_( sorted(expected_options), r )

    def test_gets_correct_gpu_options( self, cpucount ):
        cpucount.cpu_count.return_value = 8
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
        cpus = multiprocessing.cpu_count()
        # Only 1 GPU
        expected_options = [
            '-beagle_GPU',
        ]
        resource = self._mock_beagle_info( self.resources[1] )
        with patch('whip.beagleoptimiser.Popen', resource):
            r = self._C()
            eq_( sorted(expected_options), r )

    def test_gets_correct_cpu_and_gpu_options( self, cpucount ):
        cpucount.cpu_count.return_value = 24
        expected_options = [
            '-beagle_GPU -beagle_order 1',
            '-beagle_GPU -beagle_order 2',
            '-beagle_GPU -beagle_instances 2',
            '-beagle_SSE',
        ] + self._expected_beagle_instances('-beagle_SSE', 24)

        resource = self._mock_beagle_info(
            self.resources[0] + self.resources[1] + self.resources[2]
        )

        with patch('whip.beagleoptimiser.Popen', resource):
            r = self._C()
            eq_( expected_options, r )

class TestGetGPUOptions(BeagleOptions,Base):
    functionname = 'get_gpu_options'

    def test_gets_zero_gpu( self ):
        expected = [
        ]
        r = self._C( self.resources[0:1] )
        eq_( expected, r )

    def test_gets_one_gpu( self ):
        expected = [
            '-beagle_GPU'
        ]
        r = self._C( self.resources[1:2] )
        eq_( expected, r )

    def test_gets_two_gpu( self ):
        expected = [
            '-beagle_GPU -beagle_order 2',
            '-beagle_GPU -beagle_order 3',
            '-beagle_GPU -beagle_instances 2',
        ]
        r = self._C( self.resources[2:] )
        eq_( expected, r )

    def test_gets_three_gpu( self ):
        expected = [
            '-beagle_GPU -beagle_order 1',
            '-beagle_GPU -beagle_order 2',
            '-beagle_GPU -beagle_order 3',
            '-beagle_GPU -beagle_instances 2',
        ]
        r = self._C( self.resources[1:] )
        eq_( expected, r )

    def test_gets_10_gpu( self ):
        resources = [self.resources[0]]
        for i in range(1,11):
            r = self._make_resource(
                index=i,
                name='Graphics Card {0}'.format(i),
                memory=i*1024,
                corecount=i*192,
                clockspeed=i*1.1,
                flags={
                    'processor': 'PROCESSOR_GPU',
                    'framework': 'FRAMEWORK_CUDA'
                }
            )
            resources.append( r )
        r = self._C( resources )
        expected = [
            '-beagle_GPU -beagle_order 1',
            '-beagle_GPU -beagle_order 2',
            '-beagle_GPU -beagle_order 3',
            '-beagle_GPU -beagle_order 4',
            '-beagle_GPU -beagle_order 5',
            '-beagle_GPU -beagle_order 6',
            '-beagle_GPU -beagle_order 7',
            '-beagle_GPU -beagle_order 8',
            '-beagle_GPU -beagle_order 9',
            '-beagle_GPU -beagle_order 10',
            '-beagle_GPU -beagle_instances 2',
            '-beagle_GPU -beagle_instances 4',
            '-beagle_GPU -beagle_instances 6',
            '-beagle_GPU -beagle_instances 8',
            '-beagle_GPU -beagle_instances 10',
        ]
        print r
        eq_( expected, r )

class TestRunBeastOptions(BeagleOptions, BaseTempDir, Base):
    functionname = 'run_beast_options'

    def setUp( self ):
        super(TestRunBeastOptions,self).setUp()
        #from whip.beagleoptimiser import get_available_beagle_options
        self.avail_options = [
            '-beagle_GPU -beagle_order 1',
            '-beagle_GPU -beagle_order 2',
            '-beagle_GPU -beagle_instances 2',
            '-beagle_SSE',
            '-beagle_SSE -beagle_instances 2',
            '-beagle_SSE -beagle_instances 4',
            '-beagle_SSE -beagle_instances 6',
        ]

    @raises(InvalidBeastXmlError)
    def test_ensures_screenlog_in_xml( self ):
        self.xmlstr += '</beast>'
        xmlpath = 'input.xml' 
        self._writexmlfile( self.xmlstr, xmlpath )
        stringstream = StringIO()
        self._C(
            xmlpath,
            stream=stringstream,
            excludelist=[]
        )

    def test_excludelist_excludes_options( self ):
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime'),
            ) as (p1, p2):
            # Patch in our available options with random runtimes
            times = [random.random() for i in range(len(self.avail_options))]
            p1.return_value = self.avail_options
            p2.side_effect = times
            stringstream = StringIO()

            self._C(
                self.beastfiles[0],
                stream=stringstream,
                excludelist=['-beagle_GPU','-beagle_SSE -beagle_instances']
            )

            output = stringstream.getvalue()
            # Ensure that all excluded options are gone
            ok_( '-beagle_GPU -beagle_instances 2' not in output )
            ok_( '-beagle_GPU -beagle_order 1' not in output )
            ok_( '-beagle_GPU -beagle_order 2' not in output )
            ok_( '-beagle_SSE -beagle_instances' not in output )
            # Ensure only not excluded option is still there
            ok_( '-beagle_SSE' in output )

    def test_time_take_to_generate_each_test_in_output( self ):
        from whip.beagleoptimiser import pretty_time
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime'),
                patch('whip.beagleoptimiser.time'),
            ) as (p1, p2, p3):
            times = [random.random() for i in range(len(self.avail_options))]
            # Have to generate start and end
            gentimes = [i*i for i in range(len(self.avail_options)*2)]
            # Patch in avail options
            p1.return_value = self.avail_options
            # Patch in estimated times
            p2.side_effect = times
            # Patch in beast run times
            p3.time.side_effect = gentimes

            stringstream = StringIO()
            self._C( self.beastfiles[0], stream=stringstream )

            output = stringstream.getvalue()

            # We are only interested in estimate lines
            estlines = []
            for line in output.splitlines():
                if 'estimate:' in line:
                    estlines.append(line)

            # Now calculate all the time differences in gentimes
            gentimesdiff = []
            for i in range(0,len(gentimes),2):
                diff = (gentimes[i+1] - gentimes[i]) / 3600.0
                gentimesdiff.append(diff)

            # Pack up all the inputs with the actual output line
            # and then compare
            for esttime, option, gentime, outline in zip(
                    times, self.avail_options, gentimesdiff, estlines):
                expected = '{0} estimate: {1} (Time to generate: {2})'.format(
                    option, pretty_time(esttime), pretty_time(gentime)
                )
                eq_( expected, outline )

    def test_sends_to_correct_output_stream( self ):
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime'),
            ) as (p1, p2):
            times = [random.random() for i in range(len(self.avail_options))]
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
            # Assign random times between 0-1 for each available option
            times = [random.random() for i in range(len(self.avail_options))]
            p1.return_value = self.avail_options
            p2.side_effect = times
            
            # Run the test
            r = self._C( self.beastfiles[0] )
            
            # Zip up randomtime,availoption
            expected = zip( self.avail_options, times )
            # Sort the zipped list by times
            expected.sort( key=lambda x: x[1] )
            eq_( expected, r )

    def test_handles_bad_beast_run_exception( self ):
        with contextlib.nested(
                patch('whip.beagleoptimiser.get_available_beagle_options'),
                patch('whip.beagleoptimiser.estimate_beast_runtime')
            ) as (p1, p2):
            times = [random.random() for i in range(len(self.avail_options))]
            p1.return_value = self.avail_options
            times[4] = ValueError
            p2.side_effect = times
            
            r = self._C( self.beastfiles[0] )
            times[4] = sys.maxint
            expected = zip( self.avail_options, times )
            expected.sort( key=lambda x: x[1] )
            eq_( expected, r )
