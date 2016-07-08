#!/usr/bin/env python

#stdlib imports
import sys
import os.path
import datetime
import optparse
import re
import math
import pickle


TIMEFMT = '%Y-%m-%d %H:%M:%S'
DYNECM_TO_NEWTONMETERS = 1/1e7

def get_events(filename,contributor=None,catalog=None):
    """Parse (possibly multi-event) NDK format file and return a list of dictionaries for each event.

    The NDK format is explained here:
    http://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/allorder.ndk_explained

    :param filename:
      Input NDK filename.
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
       - focal Dictionary of focal mechanism data, which has the following fields:
         - method 'Mwc' or 'Mww'
         - evalstatus reviewed
         - np1/np2 Dictionaries for two nodal planes containing fields:
           - strike Strike angle
           - dip Dip angle
           - rake Rake angle
        - taxis/naxis/paxis Dictionaries for principal axes, containing fields: 
          - value Length of axis
          - plunge Plunge angle of axis
          - azimuth Azimuth angle of axis
       - moment
         - method Moment method (Mwc or Mww)
         - m0 Scalar moment in Newton-meters.
         - invtype Inversion type ('zero trace','general', or 'double couple'.
         - source Dictionary of source time function information, containing fields:
           - type 'triangle' or 'box car'.
           - duration Duration time in seconds.
         - body/surface/mantle Dictionaries of information about body/surface/mantle waves used in inversion, containing fields:
           - numstations Number of body/surface/mantle stations used in inversion.
           - numchannels Number of body/surface/mantle channels used in inversion.
         - mrr/mtt/mpp/mrt/mrp/mtp Dictionaries of moment tensor component information, containing fields:
           - value Component value in newton-meters.
           - uncertainty Component uncertainty in newton-meters.
    """
    if contributor is None:
        contributor = 'us'
    if catalog is None:
        catalog = 'us'
    events = []
    fh = open(filename,'rt')
    lc = 0
    tdict = {'catalog':catalog,
             'contributor':contributor}
    for line in fh.readlines():
        if (lc+1) % 5 == 1:
            tdict = _parseLine1(line,tdict)
            lc += 1
            continue
        if (lc+1) % 5 == 2:
            tdict = _parseLine2(line,tdict)
            lc += 1
            continue
        if (lc+1) % 5 == 3:
            tdict = _parseLine3(line,tdict)
            lc += 1
            continue
        if (lc+1) % 5 == 4:
            tdict = _parseLine4(line,tdict)
            lc += 1
            continue
        if (lc+1) % 5 == 0:
            tdict = _parseLine5(line,tdict)
            del tdict['exponent']
            tdict['focal']['evalstatus'] = 'reviewed'
            events.append(tdict)
            lc += 1
            tdict = {'catalog':catalog,
                     'contributor':contributor}

    fh.close()
    return events

def _parseLine1(line,tdict):
    origins = []
    esource = line[0:4] #PDE, for example
    dstr = line[5:26]
    year = int(dstr[0:4])
    month = int(dstr[5:7])
    day = int(dstr[8:10])
    hour = int(dstr[11:13])
    minute = int(dstr[14:16])
    fseconds = float(dstr[17:])
    seconds = int(fseconds)
    if seconds > 59: #
        seconds = 59
    microseconds = int((fseconds-seconds)*1e6)
    if microseconds > 999999:
        microseconds = 999999
    etime = datetime.datetime(year,month,day,hour,minute,seconds,microseconds)
    elat = float(line[27:33])
    elon = float(line[34:41])
    edepth = float(line[42:47])*1000
    origin = {}
    origin['id'] = '%s%s' % (esource,etime.strftime('%Y%m%d%H%M%S'))
    origin['preferred'] = True
    origin['time'] = etime
    origin['lat'] = elat
    origin['lon'] = elon
    origin['depth'] = edepth
    origins.append(origin)
    tdict['origins'] = origins
    #let's not concern ourselves with triggering magnitude, since we're more interested in derived mag and
    #we may not know what they are anyway.
    return tdict

def _parseLine2(line,tdict):
    tdict['id'] = line[0:16].strip()
    body = {'numstations':int(line[19:22].strip()),
            'numchannels':int(line[22:27].strip())}
    surface = {'numstations':int(line[34:37].strip()),
               'numchannels':int(line[37:42].strip())}
    mantle = {'numstations':int(line[49:52].strip()),
              'numchannels':int(line[52:57].strip())}
            
    tdict['moment'] = {'body':body,
                       'surface':surface,
                       'mantle':mantle}

    cmt = line[62:68].strip()
    #GCMT NDK file
    m0 = re.search("CMT:\\s*0",cmt)
    m1 = re.search("CMT:\\s*1",cmt)
    m2 = re.search("CMT:\\s*2",cmt)

    #Mww NDK file
    m3 = re.search("CMT:\\s*3",cmt)
    m4 = re.search("CMT:\\s*4",cmt)
    m5 = re.search("CMT:\\s*5",cmt)

    if (m0 is not None):
        tdict['moment']['invtype'] = "general"
        tdict['moment']['method'] = 'Mwc'
        tdict['focal'] = {'method':'Mwc'}
    elif (m1 is not None):
        tdict['moment']['invtype'] = "zero trace"
        tdict['moment']['method'] = 'Mwc'
        tdict['focal'] = {'method':'Mwc'}
    elif (m2 is not None):
        tdict['moment']['invtype'] = "double couple"
        tdict['moment']['method'] = 'Mwc'
        tdict['focal'] = {'method':'Mwc'}
    if (m3 is not None):
        tdict['moment']['invtype'] = "general"
        tdict['moment']['method'] = 'Mww'
        tdict['focal'] = {'method':'Mww'}
    elif (m4 is not None):
        tdict['moment']['invtype'] = "zero trace"
        tdict['moment']['method'] = 'Mww'
        tdict['focal'] = {'method':'Mww'}
    elif (m5 is not None):
        tdict['moment']['invtype'] = "double couple"
        tdict['moment']['method'] = 'Mww'
        tdict['focal'] = {'method':'Mww'}
    

    #fill in some source time function stuff
    functype = line[69:74]
    duration = float(line[75:].strip())
    if functype == 'TRIHD':
        tdict['moment']['source'] = {'type':'triangle','duration':duration}
    else:
        tdict['source'] = {'type':'box car','duration':duration}
    return tdict

def _parseLine3(line,tdict):
    origin = {}
    centroid = line[9:59]
    parts = centroid.split()

    microseconds = float(line[9:18].strip())*1e6;
    dtime = tdict['origins'][0]['time']+datetime.timedelta(microseconds=microseconds)
    dtimeerror = float(line[18:23])
    dlat = float(line[23:30])
    dlaterror = float(line[29:34])
    dlon = float(line[34:42])
    dlonerror = float(line[42:47])
    ddepth = float(line[47:53])*1000
    ddeptherror = float(line[53:58])
    origin['id'] = parts[-1]
    origin['time'] = {'value':dtime,'uncertainty':dtimeerror}
    origin['lat'] = {'value':dlat,'uncertainty':dlaterror}
    origin['lon'] = {'value':dlon,'uncertainty':dlonerror}
    origin['depth'] = {'value':ddepth,'uncertainty':ddeptherror}
    origin['preferred'] = False #centroid origin is not preferred as an origin (magnitude is)
    tdict['origins'].append(origin.copy())
    return tdict

def _parseLine4(line,tdict):
    exponent = float(line[0:2])
    tdict['exponent'] = exponent #we have to hold on to this somehow...
    moment = {}
    
    mrr = float(line[2:9])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mrrerror = float(line[9:15])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mtt = float(line[15:22])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mtterror = float(line[22:28])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mpp = float(line[28:35])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mpperror = float(line[35:41])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mrt = float(line[41:48])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mrterror = float(line[48:54])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mrp = float(line[54:61])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mrperror = float(line[61:67])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mtp = float(line[67:74])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    mtperror = float(line[74:])*math.pow(10.0,exponent)*DYNECM_TO_NEWTONMETERS
    tdict['moment']['mrr'] = {'value':mrr,'uncertainty':mrrerror}
    tdict['moment']['mtt'] = {'value':mtt,'uncertainty':mtterror}
    tdict['moment']['mpp'] = {'value':mpp,'uncertainty':mpperror}
    tdict['moment']['mrt'] = {'value':mrt,'uncertainty':mrterror}
    tdict['moment']['mrp'] = {'value':mrp,'uncertainty':mrperror}
    tdict['moment']['mtp'] = {'value':mtp,'uncertainty':mtperror}
    return tdict

def _parseLine5(line,tdict):
    taxis = {'plunge':float(line[11:14]),
             'azimuth':float(line[14:18]),
             'value':float(line[3:11])*math.pow(10.0,tdict['exponent'])*DYNECM_TO_NEWTONMETERS}
    naxis = {'plunge':float(line[26:29]),
             'azimuth':float(line[29:33]),
             'value':float(line[18:26])*math.pow(10.0,tdict['exponent'])*DYNECM_TO_NEWTONMETERS}
    paxis = {'plunge':float(line[41:44]),
             'azimuth':float(line[44:48]),
             'value':float(line[33:41])*math.pow(10.0,tdict['exponent'])*DYNECM_TO_NEWTONMETERS}

    #we defined the focal dictionary in line 2...
    tdict['focal']['taxis'] = taxis.copy()
    tdict['focal']['naxis'] = naxis.copy()
    tdict['focal']['paxis'] = paxis.copy()
    
    #the scalar moment belongs to the moment dictionary, which we've already created
    tdict['moment']['m0'] = float(line[49:56].strip())*math.pow(10.0,tdict['exponent'])*DYNECM_TO_NEWTONMETERS

    #this is the magnitude that we care about from NDK
    mag = (2.0/3.0) * (math.log10(tdict['moment']['m0']*1e7) - 16.1)
    mag = round(mag * 10.0)/10.0
    magnitude = {'preferred':True,
                 'type':tdict['focal']['method'],
                 'value':mag,
                 'author':tdict['catalog']}

    tdict['magnitudes'] = [magnitude.copy()]
    np1 = {'strike':float(line[56:60]),
           'dip':float(line[60:63]),
           'rake':float(line[63:68])}
    np2 = {'strike':float(line[68:72]),
           'dip':float(line[72:75]),
           'rake':float(line[75:])}
    tdict['focal']['np1'] = np1.copy()
    tdict['focal']['np2'] = np2.copy()
    return tdict
