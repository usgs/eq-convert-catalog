#stdlib imports
import tempfile
import os.path
import sys

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
mapiodir = os.path.abspath(os.path.join(homedir,'..'))
sys.path.insert(0,mapiodir) #put this at the front of the system path, ignoring any installed mapio stuff

#third party imports
import numpy as np
from obspy.io.quakeml.core import _is_quakeml as isQuakeML

#local imports
from eqconvert.convert import create_quakeml

def check_quake(eventdict):
    f,fname = tempfile.mkstemp()
    os.close(f)
    quakeml = create_quakeml(eventdict)
    f = open(fname,'wt')
    f.write(quakeml)
    f.close()
    res = isQuakeML(fname)
    os.remove(fname)
    return res


def cmpdict(d1,d2):
    if sorted(d1.keys()) != sorted(d2.keys()):
        return (False,'Key list "%s" does not match key list "%s"' % (sorted(d1.keys()),sorted(d2.keys())))
    for key,value in d1.items():
        if isinstance(value,dict):
            isequal,msg = cmpdict(value,d2[key])
            if not isequal:
                return (False,msg)
        elif isinstance(value,(int,float)):
            try:
                np.testing.assert_almost_equal(value,d2[key])
            except:
                return (False,'Numeric value %g is not close to %g' % (value,d2[key]))
        elif isinstance(value,str):
            if not value == d2[key]:
                return (False,'String "%s" does not match "%s"' % (value,d2[key]))
    return (True,'These two dictionaries appear to be identical.')
