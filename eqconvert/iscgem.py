import pandas as pd

def get_events(filename,contributor=None,catalog=None):
    if contributor is None:
        contributor = 'us'
    columns=['date','lat','lon','smajax','sminax','strike','epicenter_quality',
             'depth','depth_uncertainty','depth_quality',
             'mw','mw_unc','mw_quality','mw_source','moment','factor','moment_author',
             'mpp','mpr','mrr','mrt','mtp','mtt','eventid']
    df = pd.read_csv(filename,comment='#',names=columns,parse_dates=[0])
    events = []
    for index,row in df.iterrows():
        event = {}
        event['id'] = str(row['eventid'])
        event['catalog'] = 'iscgem'
        event['contributor'] = contributor
        event['origins'] = [{'preferred':True,
                            'id':'iscgem',
                            'evalmode':'manual',
                            'evalstatus':'reviewed',
                            'ellipse':{'major':row['smajax'],'minor':row['sminax'],'azimuth':0.0},
                            'time':row['date'].to_datetime(),
                            'lat':row['lat'],
                            'lon':row['lon'],
                            'depth':{'value':row['depth'],'uncertainty':row['depth_uncertainty']}}]
        event['magnitudes'] = [{'preferred':True,'type':'Mw','value':row['mw'],'author':row['moment_author'].strip()}]
        events.append(event.copy())
    return events
