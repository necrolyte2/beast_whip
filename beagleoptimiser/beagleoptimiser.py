from subprocess import Popen, PIPE, CalledProcessError
import re
import tempfile
import os
import shutil
from os.path import abspath

from datetime import datetime, timedelta

def estimate_beast_runtime( xmlfile, seed=999, **beast_options ):
    '''
    Run beast and wait for the first line that has the hours/million line
    Then terminate beast and calculate how long it would take to run based 
    on the iterations in the xml file

    Requires that there is a screenLog entry in the xml although it is not
    checked for :(
    TODO:
        Check for screenLog entry in xmlfile

    xmlfile - Input xml file to run beast on
    seed - Seed to set so all runs are the same
    beast_options is a kwargs set that you can specify any beast options
    '''
    # Convert to absolute path since we are moving to a temp directory later
    xmlfile = abspath( xmlfile )
    cmd = ['beast', '-overwrite', '-seed {0}'.format(seed)]
    cmd += kwargs_to_options( **beast_options )
    cmd += [xmlfile]
    # Create a temporary directory to work in
    tdir = tempfile.mkdtemp(prefix='beastoptimiser',suffix='run')
    p = Popen( cmd, stdout=PIPE, stderr=PIPE, cwd=tdir )
    # Loop through beast output
    for line in p.stdout:
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
        # Ensure beast is dead
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
    td = timedelta( hours=hours_float )
    # From the beginning of Unix time add our time delta
    dt = datetime(1,1,1) + td
    # Time format we like
    fmt = '{0:02d}:{1:02d}:{2:02d}:{3:02d}.{4}'
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
