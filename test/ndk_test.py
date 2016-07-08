#!/usr/bin/env python

#stdlib imports
import sys
import os.path
from datetime import datetime,timedelta
import math
import tempfile

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
mapiodir = os.path.abspath(os.path.join(homedir,'..'))
sys.path.insert(0,mapiodir) #put this at the front of the system path, ignoring any installed mapio stuff

#third party
import numpy as np

#local imports
from eqconvert.ndk import get_events,DYNECM_TO_NEWTONMETERS
from eqconvert.convert import create_quakeml,xml_pprint
from utils import cmpdict,check_quake

def test_ndk():
    moment = (1.312*10**23)/1e7
    mw = (2.0/3.0) * (math.log10(moment*1e7) - 16.1)
    mw = round(mw * 10.0)/10.0
    EXP = 23
    gdict = {'id':'C200501010120A',
             'catalog':'gcmt',
             'contributor':'us',
             'origins':[{'id':'PDE20050101012005',
                         'preferred':True,
                         'time':datetime(2005,1,1,1,20,5,int(.4*1e6)),
                         'lat':13.78,
                         'lon':-88.78,
                         'depth':193.1},
                         {'id':'C200501010120A',
                          'preferred':False,
                          'time':{'value':datetime(2005,1,1,1,20,5,int(.4*1e6))+timedelta(seconds=-0.3),'uncertainty':0.9},
                          'lat':{'value':13.76,'uncertainty':0.06},
                          'lon':{'value':-89.08,'uncertainty':0.09},
                          'depth':{'value':162.8,'uncertainty':12.5}}],
             'magnitudes':[{'preferred':True,
                            'type':'Mwc',
                            'value':mw,
                            'author':'gcmt'}],
             'focal':{'method':'Mwc',
                      'evalstatus':'reviewed',
                      'np1':{'strike':9.0,
                             'dip':29.0,
                             'rake':142.0},
                      'np2':{'strike':133.0,
                             'dip':72.0,
                             'rake':66.0},
                      'taxis':{'value':1.581*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                               'plunge':56.0,
                               'azimuth':12.0},
                      'naxis':{'value':-0.537*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                               'plunge':23.0,
                               'azimuth':140.0},
                      'paxis':{'value':-1.044*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                               'plunge':24.0,
                               'azimuth':241.0}},
             'moment':{'mrr':{'value':0.838*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                              'uncertainty':0.201*(10**EXP)*DYNECM_TO_NEWTONMETERS},
                       'mtt':{'value':-0.005*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                              'uncertainty':0.231*(10**EXP)*DYNECM_TO_NEWTONMETERS},
                       'mpp':{'value':-0.833*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                              'uncertainty':0.270*(10**EXP)*DYNECM_TO_NEWTONMETERS},
                       'mrt':{'value':1.050*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                              'uncertainty':0.121*(10**EXP)*DYNECM_TO_NEWTONMETERS},
                       'mrp':{'value':-0.369*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                              'uncertainty':0.161*(10**EXP)*DYNECM_TO_NEWTONMETERS},
                       'mtp':{'value':0.044*(10**EXP)*DYNECM_TO_NEWTONMETERS,
                              'uncertainty':0.240*(10**EXP)*DYNECM_TO_NEWTONMETERS},
                       'm0':moment,
                       'method':'Mwc',
                       'source':{'type':'triangle',
                                 'duration':0.6},
                       'invtype':'zero trace',
                       'body':{'numstations':4,
                               'numchannels':4},
                       'surface':{'numstations':27,
                                  'numchannels':33},
                       'mantle':{'numstations':0,
                                  'numchannels':0}}}
    testfile = os.path.join('data','gcmt.ndk')
    tdict = get_events(testfile,catalog='gcmt')[0]
    print('Testing to see if manually created moment tensor dictionary is the same as that returned by ndk module...')
    res,msg = cmpdict(gdict,tdict)
    if res:
        print(msg)
    else:
        print('The two dictionaries are not the same - error "%s".' % msg)
    if check_quake(tdict):
        print('Test NDK dictionary created valid QuakeML.')
    else:
        print('Test NDK dictionary did not create valid QuakeML.')
        
if __name__ == '__main__':
    test_ndk()
    
