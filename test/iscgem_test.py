#!/usr/bin/env python

#stdlib imports
import sys
import os.path
from datetime import datetime
import tempfile

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
mapiodir = os.path.abspath(os.path.join(homedir,'..'))
sys.path.insert(0,mapiodir) #put this at the front of the system path, ignoring any installed mapio stuff

#third party imports
from obspy.io.quakeml.core import _is_quakeml as isQuakeML

#local imports
from eqconvert.iscgem import get_events
from eqconvert.convert import create_quakeml,xml_pprint
from utils import cmpdict,check_quake

def test_read():
    #this is a two-earthquake (loma prieta, northridge) sample from the full ISC-GEM catalog file.
    datafile = os.path.join('data','isc-gem-cat.csv')
    eventlist = get_events(datafile)
    lomaprieta = eventlist[0]
    northridge = eventlist[1]
    test_loma = {'id':'389808',
                 'catalog':'iscgem',
                 'contributor':'us',
                 'origins':[{'id':'iscgem',
                             'preferred':True,
                             'evalmode':'manual',
                             'evalstatus':'reviewed',
                             'ellipse':{'major':4.4,'minor':3.3,'azimuth':52.0},
                             'time':datetime(1989,10,18,0,4,17,int(.44*1e6)),
                             'lat':37.074,
                             'lon':-121.806,
                             'depth':{'value':12.0,'uncertainty':3.3}}],
                 'magnitudes':[{'preferred':True,'type':'Mw','value':6.89,'author':'gcmt'}]}
    test_northridge = {'id':'189275',
                       'catalog':'iscgem',
                       'contributor':'us',
                       'origins':[{'id':'iscgem',
                                   'preferred':True,
                                   'evalmode':'manual',
                                   'evalstatus':'reviewed',
                                   'ellipse':{'major':4.0,'minor':3.4,'azimuth':49.8},
                                   'time':datetime(1994,1,17,12,30,56,int(.24*1e6)),
                                   'lat':34.164,
                                   'lon':-118.550,
                                   'depth':{'value':15.0,'uncertainty':3.4}}],
                       'magnitudes':[{'preferred':True,'type':'Mw','value':6.65,'author':'gcmt'}]}
    print('Comparing Loma Prieta to known example...')
    res,msg = cmpdict(test_loma,lomaprieta)
    if res:
        print('Loma Prieta was parsed correctly.')
    else:
        print('Loma Prieta was not parsed correctly: \n"%s".' % msg)
        sys.exit(1)

    #now make sure these create valid quakeml
    if check_quake(lomaprieta):
        print('Loma Prieta dictionary created valid QuakeML.')
    else:
        print('Loma Prieta dictionary did NOT create valid QuakeML.')
        
    print('Comparing Loma Prieta to known example...')
    res,msg = cmpdict(test_northridge,northridge)
    if res:
        print('Northridge was parsed correctly.')
    else:
        print('Northridge was not parsed correctly.')
        sys.exit(1)

    if check_quake(northridge):
        print('Northridge dictionary created valid QuakeML.')
    else:
        print('Northridge dictionary did NOT create valid QuakeML.')

if __name__ == '__main__':
    test_read()
    
