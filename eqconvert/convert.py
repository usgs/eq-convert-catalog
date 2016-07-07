#!/usr/bin/env python

#stdlib imports
from datetime import datetime
from xml.dom import minidom
import os.path

#third party imports
from neicio.tag import Tag

# Note to future developers:  This module makes heavy use of the Tag object, found here:
# https://github.com/usgs/neicio/blob/master/neicio/tag.py

# This object represents XML elements as having four fundamental properties:
# 1) A name, passed to the constructor as a positional argument: Tag('event') => <tag></tag>
# 2) (possibly) Attributes, passed to the constructor as a dictionary:  
#     Tag('event',attributes={'publicID':'fred','source':'us'}) => <tag publicID="fred" source="us"></tag>
# 3) (possibly) Data, passed using the data keyword.  
#    Tag('magnitude',attributes={'source':'us'},data='7.5') => <magnitude source="us">7.5</magnitude>
# 4) (possibly) child Tags, which are added after the parent tag has been created.  event_tag.addChild(mag_tag)

# Note that #3 and #4 are mutually exclusive, meaning that an XML element cannot have both data AND children.

def write_quakeml(xmlstr,eventid,outfolder,filetype=None):
    """Write a QuakeML string to a file, return name of file.

    Given the following inputs:
    eventid = 'us1234'
    outfolder = '/home/user/quakeml'
    filetype = 'ndk'
    
    the program will construct the following filename:
    /home/user/quakeml/us1234_ndk.xml

    Given the following inputs:
    eventid = 'us1234'
    outfolder = '/home/user/quakeml'
    
    the program will construct the following filename:
    /home/user/quakeml/us1234.xml
    
    
    :param xmlstr:
      QuakeML string.
    :param eventid:
      Event ID or other unique value within collection of files to be written.
    :param outfolder:
      Folder where QuakeML file should be written.
    :param filetype:
      Input file type (ndk, mloc, etc.) or some string that identifies the source of the event data.
    :returns:
      Path to output file name.
    """
    if filetype is None:
        fname = os.path.join(outfolder,'%s.xml' % (eventid))
    else:
        fname = os.path.join(outfolder,'%s_%s.xml' % (eventid,filetype))
    f = open(fname,'wt')
    f.write(xmlstr)
    f.close()
    return fname

def create_quakeml(event):
    """Given an earthquake event dictionary, return an XML string containing QuakeML representing that earthquake information.

    :param event:
      Dictionary containing the following information:
       - id  Event ID.
       - catalog Event catalog (who created the event information). [MANDATORY]
       - contributor Event contributor (who is parsing/loading the event information into QuakeML). [MANDATORY]
       - origins Sequence of origin dictionaries, which can contain: [MANDATORY]
         - preferred Boolean indicating if this origin is to be preferred. [MANDATORY]
           Multiple origins set to preferred will raise error.
         - id  Origin id, must be unique within origins list. [MANDATORY]
         - time Either a datetime object OR dictionary of {'value':datetime,'uncertainty':seconds} [MANDATORY]
         - lat  Either float latitude of hypocenter, OR dictionary of {'value':float,'uncertainty':dd}, OR 
                 dictionary of {'value':float,'lower':float,'upper':float} [MANDATORY]
         - lat  Either float longitude of hypocenter, OR dictionary of {'value':float,'uncertainty':dd}, OR 
                 dictionary of {'value':float,'lower':float,'upper':float} [MANDATORY]
         - depth Either float depth of hypocenter, OR dictionary of {'value':float,'uncertainty':dd}, OR 
                 dictionary of {'value':float,'lower':float,'upper':float} [MANDATORY]
         - ellipse Origin uncertainty.  Dictionary containing: [OPTIONAL]
           - major Error ellipse major axis.
           - minor Error ellipse major axis.
           - azimuth Error ellipse azimuth angle.
         - quality Origin quality.  Dictionary containing: [OPTIONAL]
           - numstations Number of stations used for location.
           - numphases Number of phases used for location.
           - stderr Standard error of location.
           - azgap  Azimuthal gap.
           - mindist Minimum distance.
         - evalmode Evaluation mode ('manual','automatic') [OPTIONAL]
         - evalstatus Evaluation status ('preliminary','confirmed','reviewed','final','rejected') [OPTIONAL]
         - phases Sequence of phase dictionaries, containing: [OPTIONAL]
             - id Unique string (usually a timestamp).
             - name Phase name.
             - distance Distance of station to epicenter.
             - azimuth Angle between station and epicenter.
             - time    Arrival time at station.
             - station Station code (N.S.C.L)
             - residual Arrival residual.
             - weight   1 or 0, indicating whether the phase was used or not (inserted in Arrival.timeWeight).
       - magnitudes Sequence of magnitude dictionaries containing: [MANDATORY]
         - preferred Boolean indicating whether this magnitude is preferred. [MANDATORY]
           Multiple origins set to preferred will raise error.
         - type Magnitude type (Mw, Mb, etc.) [MANDATORY]
         - value Magnitude value (0.0-9.9) [MANDATORY]
         - author Author of magnitude. [OPTIONAL]
       - focal Dictionary of focal mechanism parameters containing: [OPTIONAL]
         - method Method by which focal mechanism is derived. [MANDATORY]
         - np1 Dictionary of first nodal plane values containing: [MANDATORY]
           - strike Strike angle of first nodal plane. [MANDATORY]
           - dip Dip angle of first nodal plane. [MANDATORY]
           - rake Rake angle of first nodal plane. [MANDATORY]
         - np2 Dictionary of second nodal plane values containing: [MANDATORY]
           - strike Strike angle of second nodal plane. [MANDATORY]
           - dip Dip angle of first second plane. [MANDATORY]
           - rake Rake angle of first second plane. [MANDATORY]
         - taxis Dictionary of T axis values containing: [MANDATORY]
           - plunge Plunge angle of T axis. [MANDATORY]
           - azimuth Azimuth angle of T axis. [MANDATORY]
           - value   Length of T axis. [MANDATORY]
         - naxis Dictionary of N axis values containing: [MANDATORY]
           - plunge Plunge angle of N axis. [MANDATORY]
           - azimuth Azimuth angle of N axis. [MANDATORY]
           - value   Length of N axis. [MANDATORY]
         - paxis Dictionary of P axis values containing: [MANDATORY]
           - plunge Plunge angle of P axis. [MANDATORY]
           - azimuth Azimuth angle of P axis. [MANDATORY]
           - value   Length of P axis. [MANDATORY]
         - evalstatus One of 'preliminary','confirmed','reviewed','final','rejected'.  Defaults to 'reviewed'. [OPTIONAL]
       - moment Dictionary of moment tensor parameters containing: [OPTIONAL]
         - method Moment method (Mww,Mwc,etc.)
         - mrr Either a float mrr component of moment tensor, or dictionary of {'value':mrr,'uncertainty':mrrerror}. [MANDATORY]
         - mtt Either a float mtt component of moment tensor, or dictionary of {'value':mtt,'uncertainty':mrrerror}. [MANDATORY]
         - mpp Either a float mpp component of moment tensor, or dictionary of {'value':mpp,'uncertainty':mrrerror}. [MANDATORY]
         - mtp Either a float mtp component of moment tensor, or dictionary of {'value':mtp,'uncertainty':mrrerror}. [MANDATORY]
         - mrp Either a float mrp component of moment tensor, or dictionary of {'value':mrp,'uncertainty':mrrerror}. [MANDATORY]
         - mrt Either a float mrt component of moment tensor, or dictionary of {'value':mrt,'uncertainty':mrrerror}. [MANDATORY]
         - m0  Scalar moment
         - source Dictionary of source time function information containing: [OPTIONAL]
           - type 'triangle','box car','trapezoid',or 'unknown'. [MANDATORY]
           - duration Source duration, seconds. [MANDATORY]
           - risetime Source rise time, seconds. [OPTIONAL]
           - decaytime Source decay time, seconds. [OPTIONAL]
         - doublecouple Moment tensor double-couple value. [OPTIONAL]
         - clvd         Moment tensor compensated linear vector dipole (clvd). [OPTIONAL]
         - invtype      Moment tensor inversion type, one of 'general','zero trace','double couple'. [OPTIONAL]
         - body Dictionary of body wave information containing: [OPTIONAL]
           - numchannels Number of body wave channels. [MANDATORY]
           - numstations Number of body wave stations. [MANDATORY]
         - surface Dictionary of surface wave information containing: [OPTIONAL]
           - numchannels Number of surface wave channels. [MANDATORY]
           - numstations Number of surface wave stations. [MANDATORY]
         - mantle Dictionary of mantle wave information containing: [OPTIONAL]
           - numchannels Number of mantle wave channels. [MANDATORY]
           - numstations Number of mantle wave stations. [MANDATORY]
    :returns:
      QuakeML string.
    """
    event_required = set(['id','catalog','contributor','origins','magnitudes'])
    origin_required = set(['time','lat','lon','depth','preferred'])
    mag_required = set(['value','type','preferred'])
    focal_required = set(['np1','np2','taxis','naxis','paxis','method'])
    moment_required = set(['m0','mrr','mpp','mtt','mrt','mtp','mrp'])
    
    event_keys = set(list(event.keys()))
    if not event_required <= event_keys:
        raise Exception('Missing required event keys: %s' %  (event_required & event_keys))

    origin_required = set(['time','lat','lon','depth','preferred'])
    
    quakeml_tag = Tag('q:quakeml',attributes={'xmlns':"http://quakeml.org/xmlns/bed/1.2",
                                               'xmlns:catalog':"http://anss.org/xmlns/catalog/0.1",
                                               'xmlns:q':"http://quakeml.org/xmlns/quakeml/1.2"})
    evpid = 'quakeml:%s.anss.org/eventParameters/%s' % (event['contributor'],event['id'])
    eventparams_tag = Tag('eventParameters',attributes={'publicID':evpid})
    event_tag = Tag('event',attributes={'catalog:eventid':event['id'],
                                        'catalog:eventsource':event['catalog'],
                                        'catalog:dataid':"%s%s" % (event['catalog'],event['id']),
                                        'catalog:datasource':event['contributor'],
                                        'publicID':"quakeml:%s.anss.org/event/%s" % (event['catalog'],event['id'])})

    #magnitude stuff
    prefmag = None
    for magnitude in event['magnitudes']:
        if prefmag is not None and magnitude['preferred']:
            raise Exception('Cannot specify multiple preferred magnitudes!')
            
        if magnitude['preferred']:
            prefmag = 'quakeml:us.anss.org/magnitude/%s/%s' % (magnitude['author'],magnitude['type'])
        #check for missing keys
        mag_keys = set(list(magnitude.keys()))
        if not mag_required <= mag_keys:
            raise Exception('Missing required magnitude keys: %s' %  (mag_required & mag_keys))
        
        magnitude_tag = _create_mag_tag(magnitude,event['id'])
        event_tag.addChild(magnitude_tag)

    #deal with origins
    preforg = None
    for origin in event['origins']:
        if preforg is not None and origin['preferred']:
            raise Exception('Cannot specify multiple preferred origins!')
            
        if origin['preferred']:
            preforg = 'quakeml:us.anss.org/origin/%s' % (origin['id'])
        #check for missing keys
        origin_keys = set(list(origin.keys()))
        if not origin_required <= origin_keys:
            raise Exception('Missing required origin keys: %s' %  (origin_required & origin_keys))
        
        event_tag = _update_event_tag(origin,event,event_tag)

    #now deal with focal mechanism and moment tensor, if present
    if 'focal' in event:
        #check for missing keys
        focal = event['focal']
        focal_keys = set(list(focal.keys()))
        if not focal_required <= focal_keys:
            raise Exception('Missing required focal mechanism keys: %s' %  (focal_required & focal_keys))
        focal_tag = _create_focal_tag(focal,event)

    if 'moment' in event:
        #check for missing keys
        moment = event['moment']
        moment_keys = set(list(moment.keys()))
        if not moment_required <= moment_keys:
            raise Exception('Missing required moment tensor keys: %s' %  (moment_required & moment_keys))
        moment_tag = _create_moment_tag(moment,event)
        focal_tag.addChild(moment_tag)

    if 'focal' in event or 'moment' in event:
        #Now that we have added every possible thing to the focal mechanism tag, add it to the event
        event_tag.addChild(focal_tag)

    #if we have preferred magnitude/origin values, insert those into the event.
    if preforg is not None:
        preforg_tag = Tag('preferredOriginID',data=preforg)
        event_tag.addChild(preforg_tag)
    if prefmag is not None:
        prefmag_tag = Tag('preferredMagnitudeID',data=prefmag)
        event_tag.addChild(prefmag_tag)
    
    #Add event tag to event parameters tag
    eventparams_tag.addChild(event_tag)
    #add event parameters tag to quakeml tag
    quakeml_tag.addChild(eventparams_tag)

    #have the quakeml tag render itself to XML
    xmlstr = quakeml_tag.renderToXML()
    
    #strip out tabs and newlines
    xmlstr = xmlstr.replace('\t','')
    xmlstr = xmlstr.replace('\n','')
    
    return xmlstr

def xml_pprint(xmlstr):
    xml = minidom.parseString(xmlstr)
    pretty_xml_as_string = xml.toprettyxml(indent="  ")
    for line in pretty_xml_as_string.split('\n'):
        if not len(line.strip()):
            continue
        print(line)

def _create_mag_tag(magnitude,eventid):
    """Internal function to create magnitude tag.
    """
    pid = 'quakeml:us.anss.org/magnitude/%s/%s' % (eventid,magnitude['type'])
    magnitude_tag = Tag('magnitude',attributes={'publicID':pid})
    mag_tag = Tag('mag')
    value_tag = Tag('value',data='%.2f' % magnitude['value'])
    type_tag = Tag('type',data=magnitude['type'])
    creation_info_tag = Tag('creationInfo')
    if 'author' in magnitude:
        author_tag = Tag('author',data=magnitude['author'])
        creation_info_tag.addChild(author_tag)
        
    mag_tag.addChild(value_tag)
    magnitude_tag.addChild(type_tag)
    if 'author' in magnitude:
        magnitude_tag.addChild(creation_info_tag)

    return magnitude_tag

def _create_focal_tag(focal,event):
    pid = 'quakeml:us.anss.org/focalmechanism/%s/%s' % (event['id'],focal['method'])
    focal_tag = Tag('focalMechanism',attributes={'publicID':pid})

    #parse the nodal plane data
    nodal_tag = Tag('nodalPlanes')
    for plane in ['np1','np2']:
        if plane == 'np1':
            plane_tag = Tag('nodalPlane1')
        else:
            plane_tag = Tag('nodalPlane2')
        for angle in ['strike','dip','rake']:
            angle_tag = Tag(angle)
            value_tag = Tag('value',data='%.0f' % focal[plane][angle])
            angle_tag.addChild(value_tag)
            plane_tag.addChild(angle_tag)
        nodal_tag.addChild(plane_tag)

    #parse the principal axes data
    axes_tag = Tag('principalAxes')
    for axis in ['tAxis','nAxis','pAxis']:
        axis_tag = Tag(axis)
        for angle in ['plunge','azimuth']:
            key = axis.lower()+'-'+angle
            angle_tag = Tag(angle)
            value_tag = Tag('value',data='%.0f' % focal[axis.lower()][angle])
            angle_tag.addChild(value_tag)
            axis_tag.addChild(angle_tag)
        axes_tag.addChild(axis_tag)

    #Put in evalmode/status fields
    mode_tag = Tag('evaluationMode',data='manual')
    status = 'reviewed'
    if 'evalstatus' in focal:
        status = focal['evalstatus']
    status_tag = Tag('evaluationStatus',data=status)
        
    focal_tag.addChild(nodal_tag)
    focal_tag.addChild(axes_tag)
    focal_tag.addChild(mode_tag)
    focal_tag.addChild(status_tag)

    return focal_tag

def _create_moment_tag(moment,event):
    pid = 'quakeml:us.anss.org/momenttensor/%s/%s' % (event['id'],moment['method'])
    moment_tag = Tag('momentTensor',attributes={'publicID':pid})
    scalar_tag = Tag('scalarMoment')
    value_tag = Tag('value',data='%i' % moment['m0'])
    scalar_tag.addChild(value_tag)
    tensor_tag = Tag('tensor')
    for comp in ['Mrr','Mtt','Mpp','Mrt','Mrp','Mtp']:
        comp_tag = Tag(comp)
        if isinstance(moment[comp.lower()],float):
            value_tag = Tag('value',data='%s' % moment[comp.lower()])
        else:
            value_tag = Tag('value',data='%s' % moment[comp.lower()]['value'])
            unc_tag = Tag('uncertainty',data='%s' % moment[comp.lower()]['uncertainty'])
            comp_tag.addChild(unc_tag)
        comp_tag.addChild(value_tag)
        tensor_tag.addChild(comp_tag)

    #fill in source time function, if present
    if 'source' in moment:
        source_tag = Tag('sourceTimeFunction')
        type_tag = Tag('type',data=moment['source']['type'])
        duration_tag = Tag('duration',data='%.1f' % (moment['source']['duration']))
        if 'risetime' in moment['source']:
            rise_tag = Tag('riseTime',data='%.1f' % (moment['source']['risetime']))
            source_tag.addChild(rise_tag)
        if 'decaytime' in moment['source']:
            decay_tag = Tag('decayTime',data='%.1f' % (moment['source']['decaytime']))
            source_tag.addChild(decay_tag)
        source_tag.addChild(type_tag)
        source_tag.addChild(duration_tag)
        tensor_tag.addChild(source_tag)

    #percent double couple value
    if 'doublecouple' in moment:
        double_tag = Tag('doubleCouple',data='%.3f' % moment['doublecouple'])
        moment_tag.addChild(double_tag)

    #compensated linear vector dipole (clvd).
    if 'clvd' in moment:
        clvd_tag = Tag('clvd',data='%.3f' % moment['clvd'])
        moment_tag.addChild(clvd_tag)

    return moment_tag
                    

def _create_generic_origin_tag(origin,tagtype='lat'):
    """Internal function to create time, lat,lon, or depth tags inside origin.
    """
    if tagtype == 'lat':
        longname = 'latitude'
        shortname = 'lat'
        fmt = '%.4f'
    elif tagtype == 'lon':
        longname = 'longitude'
        shortname = 'lon'
        fmt = '%.4f'
    elif tagtype == 'depth':
        longname = 'depth'
        shortname = 'depth'
        fmt = '%.1f'
    else:
        longname = 'time'
        shortname = 'time'
        fmt = '%s'
        
    generic_tag = Tag(longname)
    error = None
    lower = None
    upper = None
    if isinstance(origin[shortname],dict):
        value = origin[shortname]['value']
        if 'lower' in origin[shortname]:
            lower = origin[shortname]['lower']
            upper = origin[shortname]['upper']
        else:
            error = origin[shortname]['uncertainty']
    else:
        value = origin[shortname]
    if isinstance(value,datetime):
        value = value.strftime('%Y-%m-%dT%H:%M:%SZ')
    value_tag = Tag('value',data=fmt % value)
    generic_tag.addChild(value_tag)
    if error is not None:
        error_tag = Tag('uncertainty',data='%.2f' % error)
        generic_tag.addChild(error_tag)
    elif lower is not None:
        lower_tag = Tag('lowerUncertainty',data='%.2f' % lower)
        upper_tag = Tag('upperUncertainty',data='%.2f' % upper)
        generic_tag.addChild(lower_tag)
        generic_tag.addChild(upper_tag)

    return generic_tag

def _create_uncertainty_tag(origin):
    """Internal function to create origin uncertainty tag.
    """
    unc_tag = Tag('OriginUncertainty')
    ellipse_tag = Tag('confidenceEllipsoid')
    major_tag = Tag('semiMajorAxisLength',data='%.2f' % (origin['ellipse']['major']))
    minor_tag = Tag('semiMinorAxisLength',data='%.2f' % (origin['ellipse']['minor']))
    az_tag = Tag('majorAxisAzimuth',data='%.2f' % (origin['ellipse']['azimuth']))
    ellipse_tag.addChild(major_tag)
    ellipse_tag.addChild(minor_tag)
    ellipse_tag.addChild(az_tag)
    unc_tag.addChild(ellipse_tag)
    return unc_tag

def _create_quality_tag(origin):
    """Internal function to create origin quality tag.
    """
    quality_tag = Tag('quality')
    used_phasecount_tag = Tag('usedPhaseCount',data=origin['quality']['numphases'])
    used_stationcount_tag = Tag('usedStationCount',data=origin['quality']['numstations'])
    stderr_tag = Tag('standardError',data=origin['quality']['stderr'])
    gap_tag = Tag('azimuthalGap',data=origin['quality']['azgap'])
    mindist_tag = Tag('minimumDistance',data=origin['quality']['mindist'])
    quality_tag.addChild(used_phasecount_tag)
    quality_tag.addChild(used_stationcount_tag)
    quality_tag.addChild(stderr_tag)
    quality_tag.addChild(gap_tag)
    quality_tag.addChild(mindist_tag)
    return quality_tag

def _create_arrival_tag(origin,event):
    """Internal function to create arrival tag.
    """
    picktime = phase['id'].strftime('%s')+'.'+phase['id'].strftime('%f')
    arrid = 'quakeml:us.anss.org/arrival/%s/us_%s' % (event['id'],picktime)
    arrival_tag = Tag('arrival',attributes={'publicID':arrid})
    pickid = 'quakeml:us.anss.org/pick/%s/us_%s' % (event['id'],picktime)
    pickid_tag = Tag('pickID',data=pickid)
    phase_tag = Tag('phase',data=phase['name'])
    azimuth_tag = Tag('azimuth',data='%.2f' % (phase['azimuth']))
    distance_tag = Tag('distance',data='%.2f' % (phase['distance']))
    residual_tag = Tag('timeResidual',data='%.2f' % (phase['residual']))
    weight_tag = Tag('timeWeight',data='%.2f' % (phase['weight']))
    arrival_tag.addChild(pickid_tag)
    arrival_tag.addChild(phase_tag)
    arrival_tag.addChild(azimuth_tag)
    arrival_tag.addChild(distance_tag)
    arrival_tag.addChild(residual_tag)
    arrival_tag.addChild(weight_tag)
    return arrival_tag

def _create_pick_tag(origin,event):
    """Internal function to create pick tag.
    """
    picktime = phase['id'].strftime('%s')+'.'+phase['id'].strftime('%f')
    pickid = 'quakeml:us.anss.org/pick/%s/us_%s' % (event['id'],picktime)
    pick_tag = Tag('pick',attributes={'publicID':pickid})
    time_tag = Tag('time')
    timevalue_tag = Tag('value',data=phase['time'].strftime(TIMEFMT+'Z'))
    time_tag.addChild(timevalue_tag)
    network,station,channel,location = phase['sta'].split('.')
    attributes = {}
    if network.replace('-','').strip() != '':
        attributes['networkCode'] = network
    if station.replace('-','').strip() != '':
        attributes['stationCode'] = station
    if channel.replace('-','').strip() != '':
        attributes['channelCode'] = channel
    if location.replace('-','').strip() != '':
        attributes['locationCode'] = location
    wave_tag = Tag('waveformID',attributes=attributes)
    hint_tag = Tag('phaseHint',data=phase['name']) #duplicate of arrival->phase (??)
    eval_tag = Tag('evaluationMode',data='manual')

    pick_tag.addChild(time_tag)
    pick_tag.addChild(wave_tag)
    pick_tag.addChild(hint_tag)
    pick_tag.addChild(eval_tag)
    return pick_tag

def _update_event_tag(origin,event,event_tag):
    """Internal function to update an already existing event tag with origins and magnitudes.
    """
    origin_tag = Tag('origin',attributes={'publicID':"quakeml:us.anss.org/origin/%s" % origin['id']})

    #time tag
    time_tag = _create_generic_origin_tag(origin,'time')
    origin_tag.addChild(time_tag)

    #latitude tag
    lat_tag = _create_generic_origin_tag(origin,'lat')
    origin_tag.addChild(lat_tag)

    #longitude tag
    lon_tag = _create_generic_origin_tag(origin,'lon')
    origin_tag.addChild(lon_tag)

    #depth tag
    depth_tag = _create_generic_origin_tag(origin,'depth')
    origin_tag.addChild(depth_tag)

    #error ellipse stuff
    if 'ellipse' in origin:
        unc_tag = _create_uncertainty_tag(origin)
        origin_tag.addChild(unc_tag)

    #origin quality information
    if 'quality' in origin:
        quality_tag = _create_quality_tag(origin)
        origin_tag.addChild(quality_tag)

    #phases, picks, arrivals, etc.
    if 'phases' in origin:
        for phase in origin['phases']:
            #arrivals first
            arrival_tag = _create_arrival_tag(origin,event)

            #picks
            pick_tag = _create_pick_tag(origin,event)

            #arrivals belong to origins
            origin_tag.addChild(arrival_tag)
            #but picks belong to the event
            event_tag.addChild(pick_tag)

    #Add origin tag to event before returning event
    event_tag.addChild(origin_tag)

    return event_tag


