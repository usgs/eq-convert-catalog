#!/usr/bin/env python

#stdlib imports
import sys
import os.path
from datetime import datetime,timedelta
import re
import string
import argparse
import textwrap
import math
from collections import OrderedDict
import urllib.request as request
import json

#local imports
from .stationdb import StationTranslator

MINMAG = 4.0

URLBASE = 'http://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=[START]&endtime=[END]&latitude=[LAT]&longitude=[LON]&maxradiuskm=[RAD]'
RADIUS = 10 #km around an epicenter to search for matching earthquake
TIMEDELTA = 3 #seconds around an origin time to search for matching earthquake

SOURCE = 'rde'

TIMERROR = 5 #how many days can the phase time be from a given station epoch before we don't consider it to be part of that epoch 

TIMEFMT = '%Y-%m-%dT%H:%M:%S'
USAGE = {'+':1,'x':0,'-':0}
DEPTHTYPES = {'c':'operator assigned',
              'd':'constrained by depth phases',
              'e':'other',
              'f':'other',
              'l':'constrained by direct phases',
              'm':'from location',
              'n':'constrained by direct phases',
              'r':'from location',
              'u':'other',
              'w':'from moment tensor inversion'}

def getPrefMag(event):
    """Search ComCat for the preferred magnitude value, source, and type.

    :param event:
      Dictionary containing earthquake event information, primarily a list of origin dictionaries with lat,lon,time fields.
    :returns:
      Tuple of preferred (magnitude value,magnitude source, magnitude type).
    """
    origin = None
    for origin in event['origins']:
        if origin['preferred']:
            break
    if origin is None:
        raise Exception('No preferred origin!')
    url = URLBASE.replace('[RAD]','%i' % RADIUS)
    url = url.replace('[LAT]','%.4f' % origin['lat'])
    url = url.replace('[LON]','%.4f' % origin['lon'])
    stime = origin['time']['value'] - timedelta(seconds=TIMEDELTA)
    etime = origin['time']['value'] + timedelta(seconds=TIMEDELTA)
    url = url.replace('[START]','%s' % stime.strftime(TIMEFMT))
    url = url.replace('[END]','%s' % etime.strftime(TIMEFMT))
    try:
        fh = request.urlopen(url)
    except:
        pass
    data = fh.read().decode('utf-8')
    fh.close()
    jdict = json.loads(data)
    if not 'features' in jdict or len(jdict['features']) > 1 or len(jdict['features']) == 0:
        print('No event matching %s M%.1f' % (event['time'],event['magnitude'][0]['magnitude']))
        return (None,None,None)
    try:
        pevent = jdict['features'][0]
    except:
        pass
    etime = datetime.utcfromtimestamp(pevent['properties']['time']/1000)
    elon,elat,edep = pevent['geometry']['coordinates']
    emag = pevent['properties']['mag']
    prefmag = emag
    prefsource = pevent['properties']['sources'].split(',')[1]
    preftype = pevent['properties']['magType']
    return (prefmag,prefsource,preftype)
    
def readLayerLine(event,line):
    """Read line containing 1-D velocity layer information.

    :param event:
      Dictionary where earthquake information will be stored.
    :param line:
      Line from MLOC file ("L        0.000     5.950     3.600")
    :returns:
      Modified event dictionary with either new 'layer' list, or appended 'layer' list.
    """
    depth,vp,vs = [float(p) for p in line[1:].strip().split()]
    if 'layer' in event:
        event['layer'].append([depth,vp,vs])
    else:
        event['layer'] = [[depth,vp,vs]]
    return event

def readStationLine(event,line):
    """Read line containing station information.

    :param event:
      Dictionary where earthquake information will be stored.
    :param line:
      Line from MLOC file ("C PSUB     39.9274  -75.4514     110")
    :returns:
      Modified event dictionary with new or appended 'stations' dictionary.
    """
    parts = line[1:].strip().split()
    station = parts[0]
    lat,lon,elev = [float(p) for p in parts[1:4]]
    if 'stations' in event:
        event['stations'][station] = {'lat':lat,'lon':lon,'elev':elev}
    else:
        event['stations'] = {station:{'lat':lat,'lon':lon,'elev':elev}}

    return event
    
def readCommentLine(event,line):
    """Read line containing comment information.

    :param event:
      Dictionary where earthquake information will be stored.
    :param line:
      Line from MLOC file ("# Focal depths for all events were estimated during early runs with free")
    :returns:
      Modified event dictionary with new or appended 'comment' string.
    """
    com = line[1:].strip()
    if 'comment' in event:
        event['comment'] += ' '+com
    else:
        event['comment'] = ' '+com
    return event

def readHypoLine(event,line):
    """Read line containing hypocenter information.

    :param event:
      Dictionary where earthquake information will be stored.
    :param line:
      Line from MLOC file ("H   2011 08 23 17 51  3.52  0.04   37.9212  281.9946  50  0.51  0.57   9.6 m   1.7   1.7 CH01 EBergman minerala3.11")
    :returns:
      Modified event dictionary with new or appended 'origins' list of dictionaries.
    """
    parts = line[1:].strip().split()
    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])
    hour = int(parts[3])
    minute = int(parts[4])
    second = float(parts[5])
    microsecond = int((second - int(second))*1e6)

    #it seems like seconds are from 1-60 (sometimes), so we're subtracting one.
    second = int(second) - 1
    #sometimes this doesn't work.  This is not my fault.
    if second == -1:
        second = 0
        
    origin = {}
    origin['time'] = {'value':datetime(year,month,day,hour,minute,second,microsecond),
                      'uncertainty':float(parts[6])}
    origin['lat'] = float(parts[7])
    lon = float(parts[8])
    if lon > 180:
        lon -= 360
    origin['lon'] = lon

    ellipse = {}
    ellipse['azimuth'] = int(parts[9])
    ellipse['minor'] = float(parts[10])
    ellipse['major'] = float(parts[11])
    
    depthvalue = float(parts[12])
    depthcode = parts[13]
    depthlower = float(parts[14])
    depthupper = float(parts[15])

    origin['depth'] = {'value':depthvalue,'lower':depthlower,'upper':depthupper}
    origin['ellipse'] = ellipse

    clusterid = parts[18]
    origin['id'] = clusterid
    #add this origin to a list of origins.  The first origin should be the only preferred one.
    if 'origins' in event:
        origin['preferred'] = False
        event['origins'] = [origin]
    else:
        origin['preferred'] = True
        event['origins'] = [origin]
    return event

def readMagnitudeLine(event,line):
    """Read line containing magnitude information.

    :param event:
      Dictionary where earthquake information will be stored.
    :param line:
      Line from MLOC file ("M   5.7  UNK   ISC")
    :returns:
      Modified event dictionary with new or appended 'magnitudes' list of dictionaries.
    """
    parts = line[1:].split()
    mag = {}
    mag['preferred'] = True
    mag['value'] = float(parts[0])
    magtype = parts[1]
    if magtype == 'UNK':
        magtype = 'ML'
    mag['type'] = magtype
    mag['author'] = ' '.join(parts[2:])
    if 'magnitudes' in event:
        mag['preferred'] = False #only first magnitude is preferred
        event['magnitudes'].append(mag)
    else:
        event['magnitudes'] = [mag]
    return event

def readPhaseLine(event,line,st):
    """Read line containing phase information.

    :param event:
      Dictionary where earthquake information will be stored.
    :param line:
      Line from MLOC file ("P + URVA     0.51 133 Pg       2011  8 23 17 51 13.08  -2  -0.1  0.10")
    :returns:
      Modified event dictionary with new or appended 'phases' list of dictionaries.
    """
    parts = line[1:].split()
    phase = {}
    #some phases are recorded but not used
    #following Hydra precedent here and using arrival->timeWeight=0 to mark those unused phases
    phase['weight'] = USAGE[parts[0]] 
    station = parts[1]
    phase['name'] = parts[4]
    phase['distance'] = float(parts[2])
    phase['azimuth'] = int(parts[3])
    year = int(parts[5])
    month = int(parts[6])
    day = int(parts[7])
    hour = int(parts[8])
    minute = int(parts[9])
    second = float(parts[10])
    microsecond = int((second - int(second))*1e6)
    second = int(second) - 1 #assumption here is that input seconds are 1 to 60
    if second == -1: #sometimes seconds are 0 to 59, sometimes 1 to 60.  Not my problem.
        second = 0
    phase['time'] = datetime(year,month,day,hour,minute,second,microsecond)
    nscl_station = station
    if 'stations' in event and station in event['stations']:
        nscl_station = st.getStationByLocation(station,
                                               lat=event['stations'][station]['lat'],
                                               lon=event['stations'][station]['lon'])
        if nscl_station == station:
            nscl_station = st.getNSCL(station,phase['name'],phase['time'])
    else:
        nscl_station = st.getNSCL(station,phase['name'],phase['time'])
    phase['id'] = phase['time'].strftime('%Y%m%d%H%M%S')+'_%s_%s' % (phase['name'],nscl_station)
    phase['station'] = nscl_station
    phase['precision'] = int(parts[11])
    phase['residual'] = float(parts[12])
    #phase['error'] = float(parts[13])
    phasekey = phase['station']+'_'+phase['name']
    #if this phase matches one previously found, we'll replace that in the list.
    if 'phases' not in event:
        event['phases'] = [phase.copy()]
    else:
        haskey = False
        for i in range(0,len(event['phases'])):
            tphase = event['phases'][i]
            if tphase['station']+'_'+tphase['name'] == phasekey:
                event['phases'][i] = phase.copy()
                haskey = True
                break
        if not haskey:
            event['phases'].append(phase.copy())

    return event


def get_events(qomfile,contributor='us',catalog='us'):
    """Parse MLOC format file, return list of event dictionaries, including origin, magnitude, and phase information.

    :param qomfile:
      File in MLOC format.
    :param contributor:
      Source network of whoever is parsing this file.
    :param catalog:
      Source network of whoever created the MLOC data.
    :returns:
      List of event dictionaries, which have the following fields:
       - id Event ID.
       - catalog (see above).
       - contributor (see above).
       - origins List of dictionaries, containing fields:
         - preferred Boolean valued indicating if this origin is preferred.
         - id  Origin ID.
         - time Datetime indicating origin time of rupture.
         - lat  Float latitude of origin.
         - lon  Float longitude of origin.
         - depth  Dictionary of depth information, containing fields:
           - value Depth value in km.
           - lower Depth lower uncertainty.
           - upper Depth upper uncertainty.
       - magnitudes List of dictionaries, which have the following fields:
         - preferred Boolean valued indicating if this magnitude is preferred.
         - type Magnitude type (ML,Mw,Mb, etc.)
         - value Magnitude value (0.0-9.9)
         - author Source of magnitude value.
       - phases List of dictionaries, which have the following fields:
         - id Phase ID
         - name Phase type (Pg, Pn, Sg, etc.)
         - distance Distance from origin to station (dec degrees).
         - azimuth Angle between origin and station.
         - time Datetime of pick arrival time.
         - station NSCL of station where phase was determined.
         - residual Float travel time residual (seconds).
         - weight  1 or 0 indicating whether this phase was used in the relocation.
    """
    st = StationTranslator(dictionaryfile=None)
    f = open(qomfile,'rt')
    events = []
    event = {'catalog':catalog,
             'contributor':contributor}
    i = 1
    nphases = 0
    phaselist = []
    comment = ''    
    for line in f.readlines():
        if line.startswith('L'):
            event = readLayerLine(event,line)
        if line.startswith('C'):
            event = readStationLine(event,line)
        if line.startswith('#'):
            comment += line.strip('#')
        if line.startswith('E'):
            event['id'] = '%08i' % i #ignore Eric's event ID fields
        if line.startswith('H'):
            event = readHypoLine(event,line)
        if line.startswith('M'):
            event = readMagnitudeLine(event,line)
        if line.startswith('P'):
            #sys.stderr.write('reading phase line %i ("%s")\n' % (nphases+1,line))
            nphases += 1
            event = readPhaseLine(event,line,st)
        if line.startswith('STOP'):
            if 'stations' in event:
                del event['stations']
            events.append(event.copy())
            sys.stderr.write('Parsed event %i\n' % i)
            i += 1
            sys.stderr.flush()
            event = {'catalog':catalog,
                     'contributor':contributor}
    f.close()
    print('Read %i events' % len(events))

    #try to find the best magnitude from comcat for the larger events
    for event in events:
        if event['magnitudes'][0]['value'] > MINMAG:
            prefmag,prefsource,preftype = getPrefMag(event)
            if prefmag is not None:
                for i in range(0,len(event['magnitudes'])):
                    if event['magnitudes'][i]['preferred']:
                        event['magnitudes'][i]['preferred'] = False
                        
                event['magnitudes'].append({'preferred':True,
                                            'type':preftype,
                                            'value':prefmag,
                                            'author':prefsource})

    return events


    
