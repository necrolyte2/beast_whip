from subprocess import Popen, PIPE, CalledProcessError
import re
import tempfile
import os
import shutil
from os.path import abspath
import itertools
from datetime import datetime, timedelta
import multiprocessing
import sys
import time

# Exception for invalid Beast xml
class InvalidBeastXmlError(Exception): pass

def run_beast_options( xmlfile, stream=sys.stdout, excludelist=[] ):
    '''
    Runs beast with a combination of available -beagle_options
    Focuses only on the following options:
        -beagle_CPU
        -beagle_SSE
        -beagle_GPU

    Basically a permutation over CPU/SSE/GPU and the instances count
    -beagle_order at this point is left out due to the increase in run time that
    would occur due to the extra permutations

    Returns a list of tuples (options run, estimated hours, time to generate in seconds) sorted by estimated hours
        ascending
    '''
    with open(xmlfile) as fh:
        if 'screenLog' not in fh.read():
            raise InvalidBeastXmlError(
                '{0} does not contain a screenLog definition'.format(xmlfile)
            )
    options = get_available_beagle_options()
    runs = []
    for option in options:
        # Skip the exluded options
        skip=False
        for exclude in excludelist:
            if exclude in option:
                skip=True
                break
        if skip:
            continue
        beast_options = {}
        for o in option.split(' ', 1):
            beast_options[o] = True
        print "Running beast with {0}".format(option)
        start = time.time()
        try:
            esthours = estimate_beast_runtime(
                xmlfile, seed=999, stream=stream, **beast_options
            )
        except ValueError as e:
            # Just set estimated hours really high to indicate an error
            esthours = sys.maxint
        diff = (time.time() - start) / 3600.0
        msg = '{0} estimate: {1} (Time to generate: {2})'.format(
            option, pretty_time(esthours), pretty_time(diff))
        stream.write( msg + '\n' )
        print msg
        runs.append( (option, esthours) )
    runs.sort( key=lambda x: x[1] )
    return runs

def get_available_beagle_options( ):
    '''
    Return a list of beagle options that can be passed to beast
    Returns a list of options such as 
        ['-beagle_SSE','-beagle_CPU','-beagle_GPU','-beagle_instances']

    Will only return -beagle_SSE or -beagle_CPU with preference of -beagle_SSE
     as SSE should always be faster than CPU
    '''
    cmd = ['beast', '-beagle_info']
    p = Popen(cmd, stdout=PIPE)
    sout,serr = p.communicate()
    if 'BEAGLE resources available' in sout:
      resourcelist = sout.rstrip().partition( 'BEAGLE resources available:\n' )[2]
    else:
      resourcelist = sout.rstrip().partition( '--- BEAGLE RESOURCES ---\n' )[2]
    resourcelist = resourcelist.split('\n\n\n')
    options = []

    instances = []
    for i in range(2, multiprocessing.cpu_count()+1, 2):
        instances.append( '-beagle_instances {0}'.format(i) )

    # At some point probably should make another function for CPU resources
    # like how get_gpu_options was done
    for resource in resourcelist:
        if 'CPU' in resource and '-beagle_SSE' not in options:
            options.append( '-beagle_CPU' )
            for inst in instances:
                options.append( '-beagle_CPU ' + inst )
        if 'VECTOR_SSE' in resource:
            options.append( '-beagle_SSE' )
            for inst in instances:
                options.append( '-beagle_SSE ' + inst )
                options.remove( '-beagle_CPU ' + inst )
            options.remove( '-beagle_CPU' )

    # Put GPU before CPU since that is correct ordering
    options = get_gpu_options(resourcelist) + options

    return options

def get_gpu_options( resourcelist ):
    '''
    Get a list of GPU options from resourcelist
    '''
    options = []
    gpu_indexes = []
    for resource in resourcelist:
        if 'GPU' in resource:
            i = int(resource.split('\n')[0].split(':')[0].strip())
            gpu_indexes.append( i )
            options.append( '-beagle_GPU -beagle_order {0}'.format(i) )
    # If there is only one gpu, then there is only one option
    if len(gpu_indexes) == 1:
        return ['-beagle_GPU']
    # If there are no GPU's return null list
    if len(gpu_indexes) == 0:
        return []

    # Generate instances up to max gpu count
    for i in gpu_indexes:
        if i%2 == 0:
            options.append( '-beagle_GPU -beagle_instances {0}'.format(i) )

    return options

def estimate_beast_runtime( xmlfile, seed=999, stream=sys.stdout, **beast_options ):
    '''
    Run beast and wait for the first line that has the hours/million line
    Then terminate beast and calculate how long it would take to run based 
    on the iterations in the xml file

    xmlfile - Input xml file to run beast on
    seed - Seed to set so all runs are the same
    beast_options is a kwargs set that you can specify any beast options
    '''
    # Need the absolute path to the xml file since we enter a temp
    #  directory and reference the file from there
    xmlfile = abspath( xmlfile )
    # Build Beast options to run
    cmd = ['beast', '-overwrite', '-seed {0}'.format(seed)]
    cmd += kwargs_to_options( **beast_options )
    cmd += [xmlfile]
    # Create a temporary directory to work in
    tdir = tempfile.mkdtemp(prefix='beastoptimiser',suffix='run')
    # Send the command ran to stream
    stream.write( ' '.join(cmd) + '\n' )
    p = Popen( cmd, stdout=PIPE, stderr=PIPE, cwd=tdir )
    # Loop through beast output
    for line in p.stdout:
        # Send all output to output stream
        stream.write( line )
        # Parse each output line
        hours_per_million = get_hours_per_million( line )
        # First line that returns an actual result for hours/million states
        if hours_per_million is not None:
            # No longer need to run beast
            p.kill()
            # Exit looping over output
            break
    # Make sure we actually got what we were looking for
    if hours_per_million is None:
        p.wait()
        if p.returncode != 0:
            stream.write( '!!!!!!!!!!!! Beast did not exit correctly !!!!!!!!!!!!!!!!!!\n' )
            stream.write( 'Here is the remaining output:\n' )
            stream.write( p.stderr.read() )
            stream.write( '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' )
        # Ensure beast is dead
        if p.poll() is None:
            p.kill()
        raise ValueError( "Initial hours/million state was not found in output" )
    # Compute some numbers
    total_chains = get_chainlength( xmlfile )
    hours = hours_per_million * (total_chains / 1000000.0)
    # Clean up our temp directory if retcode was 0
    shutil.rmtree( tdir )
    # Return the goodness
    return hours

def pretty_time( hours_float ):
    '''
    Convert floating point number that represents hours into
    Days:Hours:Min:Sec
    Taken from:
    http://stackoverflow.com/questions/4048651/python-function-to-convert-seconds-into-minutes-hours-and-days
    '''
    # Get a time delta
    try:
        td = timedelta( hours=hours_float )
    except OverflowError as e:
        return 'INF'

    # From the beginning of Unix time add our time delta
    dt = datetime(1,1,1) + td
    # Time format we like
    fmt = '{1:02d}:{2:02d}:{3:02d}.{4}'
    # Add days if needed
    if dt.day-1 > 0:
        fmt = '{0}d ' + fmt    
    return fmt.format(dt.day-1, dt.hour, dt.minute, dt.second, dt.microsecond)

def kwargs_to_options( **kwargs ):
    '''
    Convert kwargs type input(essentially dictionary) into 
    -key value pairs or just -key if the value is a boolean(True)
    
    Returned value should be a correct options list to be used with Popen
    '''
    options = []
    for k,v in kwargs.iteritems():
        if isinstance(v,bool):
            if v:
                options.append( k )
        else:
            options.append( [k,'{0}'.format(v)] )
    return options

def get_hours_per_million( stateline ):
    '''
    Parse a state Posterior Prior Likelihood rootHeight uced.mean line
    Return None or float that represents the hours/million states
        If output is in hours/billion than convert to hours/million
    '''
    p = '(\d+\.\d+) hours/[mb]illion states'
    m = re.search( p, stateline )
    if m:
        # Convert hours/[mb]illion states to float
        hours_pm = float(m.group(1))
        # If output was per billion than convert to million
        if 'billion' in stateline:
            return hours_pm / 1000
        # Return hours per million
        return hours_pm
    # Return None to indicate this line did not have a valid hours/[mb]illion line
    return None

def get_chainlength( xmlfile ):
    '''
    Pull the chainLength out of the xml as an integer
    '''
    states = 0
    with open(xmlfile) as fh:
        for line in fh:
            if 'chainLength' in line:
                m = re.search( 'chainLength="(\d+)"', line )
                states = m.group(1)
                break
    return int(states)
