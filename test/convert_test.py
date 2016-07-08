#!/usr/bin/env python

#stdlib imports
import sys
import os.path
import tempfile
from datetime import datetime

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
mapiodir = os.path.abspath(os.path.join(homedir,'..'))
sys.path.insert(0,mapiodir) #put this at the front of the system path, ignoring any installed mapio stuff

#third party imports
from obspy.io.quakeml.core import _is_quakeml as isQuakeML

#local imports
from eqconvert.convert import create_quakeml

def test_simple_events():
    event1 = {'id':'1234abcd',
              'catalog':'mycatalog',
              'contributor':'us',
              'origins':[{'id':'1234abcd',
                          'preferred':True,
                          'time':datetime.utcnow(),
                          'lat':0.0,
                          'lon':0.0,
                          'depth':0.0}],
              'magnitudes':[{'preferred':True,'type':'Mw','value':9.0,'author':'us'}]}
    event2 = {'id':'1234abcd',
              'catalog':'mycatalog',
              'contributor':'us',
              'origins':[{'id':'1234abcd',
                          'preferred':True,
                          'time':datetime.utcnow(),
                          'lat':0.0,
                          'lon':0.0,
                          'depth':0.0,
                          'ellipse':{'major':10.0,'minor':8.0,'azimuth':25.4}}],
              'magnitudes':[{'type':'Mw','value':9.0,'preferred':True,'author':'us'}]}
    event3 = {'id':'1234abcd',
              'catalog':'mycatalog',
              'contributor':'us',
              'origins':[{'id':'1234abcd',
                          'preferred':True,
                          'time':{'value':datetime.utcnow(),'uncertainty':3.1},
                          'lat':{'value':0.0,'uncertainty':2.3},
                          'lon':{'value':0.0,'uncertainty':3.1},
                          'depth':{'value':0.0,'uncertainty':10.5},
                          'ellipse':{'major':10.0,'minor':8.0,'azimuth':25.4}}],
              'magnitudes':[{'type':'Mw','value':9.0,'preferred':True,'author':'us'}]}
    events = [event1,event2,event3]
    try:
        print('Testing to see if we can create valid QuakeML from increasingly complex inputs.')
        for event in events:
            f,fname = tempfile.mkstemp()
            xmlstr = create_quakeml(event)
            f = open(fname,'wt')
            f.write(xmlstr)
            f.close()
            if isQuakeML(fname):
                print('Valid simple QuakeML succesfully created.')
            else:
                print('Failed to create valid QuakeML.')
    except:
        print('Failed to create valid simple QuakeML.')
    finally:
        os.remove(fname)

    
if __name__ == '__main__':
    test_simple_events()
