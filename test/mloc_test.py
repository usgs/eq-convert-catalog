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

#third party
from obspy.io.quakeml.core import _is_quakeml as isQuakeML

#local
from eqconvert.mloc import get_events
from eqconvert.convert import create_quakeml,xml_pprint
from utils import cmpdict

def test_mloc():
    filename = os.path.join('data','mloc.comcat')
    event = get_events(filename,catalog='mineral2011a')[0]
    cmpevent = {'id':'00000001',
                'catalog':'mineral2011a',
                'contributor':'us',
                'origins':[{'preferred':True,
                            'id':'minerala3.11',
                            'time':datetime(2011, 8, 23, 17, 51, 2, 520000),
                            'lat':37.9212,
                            'lon':-78.00540000000001,
                            'depth':{'value':9.6,'lower':1.7,'upper':1.7},
                            'ellipse':{'azimuth':50,'major':0.51,'minor':0.57}}],
                'magnitudes':[{'preferred':False,
                               'type':'ML',
                               'value':5.7,
                               'author':'ISC'},
                               {'preferred':False,
                                'type':'Mw',
                                'value':5.8,
                                'author':'ISC'},
                                {'preferred':True,
                                 'type':'mw',
                                 'value':5.7,
                                 'author':'se'}],
                'phases':[{'id':'20110823175112_Pg_SE.URVA.HHZ.--',
                           'name':'Pg',
                           'distance':0.51,
                           'azimuth':133,
                           'time':datetime(2011, 8, 23, 17, 51, 12, 80000),
                           'station':'SE.URVA.HHZ.--',
                           'residual':-0.1,
                           'weight':1},
                           
                          {'id':'20110823175113_Pg_US.CBN.BHZ.00',
                           'name':'Pg',
                           'distance':0.57,
                           'azimuth':60,
                           'time':datetime(2011, 8, 23, 17, 51, 13, 410000),
                           'station':'US.CBN.BHZ.00',
                           'residual':0.1,
                           'weight':1},

                          {'id':'20110823175132_Pn_LD.SDMD.HHZ.--',
                           'name':'Pn',
                           'distance':1.74,
                           'azimuth':31,
                           'time':datetime(2011, 8, 23, 17, 51, 32, 609999),
                           'station':'LD.SDMD.HHZ.--',
                           'residual':-0.4,
                           'weight':1},

                          {'id':'20110823175155_Sg_LD.SDMD.HHE.--',
                           'name':'Sg',
                           'distance':1.74,
                           'azimuth':31,
                           'time':datetime(2011, 8, 23, 17, 51, 55, 299999),
                           'station':'LD.SDMD.HHE.--',
                           'residual':-0.5,
                           'weight':1},
                           
                          {'id':'20110823175147_Pn_PE.PSUB.HHZ.--',
                           'name':'Pn',
                           'distance':2.83,
                           'azimuth':44,
                           'time':datetime(2011, 8, 23, 17, 51, 47, 240000),
                           'station':'PE.PSUB.HHZ.--',
                           'residual':-0.5,
                           'weight':1},

                          {'id':'20110823175133_Pn_IR.VWCC..',
                           'name':'Pn',
                           'distance':1.7,
                           'azimuth':247,
                           'time':datetime(2011, 8, 23, 17, 51, 33, 250000),
                           'station':'IR.VWCC..',
                           'residual':0.8,
                           'weight':0},]}
                            
                             
    res,msg = cmpdict(event,cmpevent)
    if res:
        print('Event was parsed correctly.')
    else:
        print('Event was not parsed correctly: \n"%s".' % msg)
        sys.exit(1)
    
    quakeml = create_quakeml(event)
    try:
        h,fname = tempfile.mkstemp()
        os.close(h)
        f = open(fname,'wt')
        f.write(quakeml)
        f.close()
        if isQuakeML(fname):
            print('MLOC QuakeML is valid.')
        else:
            print('MLOC QuakeML is NOT valid.')
    except:
        pass
    finally:
        os.remove(fname)

if __name__ == '__main__':
    test_mloc()
    
