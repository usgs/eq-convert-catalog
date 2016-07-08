import re
import socket
from datetime import timedelta,datetime

CWBHOST = 'cwbpub.cr.usgs.gov'
CWBPORT = 2052

TIMERROR = 5 #how many days can the phase time be from a given station epoch before we don't consider it to be part of that epoch 

class StationTranslator(object):
    def __init__(self,dictionaryfile=None):
        self.stationdict = {}
        if dictionaryfile is not None:
            f = open(dictionaryfile,'rt')
            for line in f.readlines():
                key,value = line.split('=')
                self.stationdict[key.strip()] = value.strip()
            f.close()
            

    def save(self,dictfile):
        f = open(dictfile,'wt')
        for key,value in self.stationdict.iteritems():
            f.write('%s = %s\n' % (key.strip(),value.strip()))
        f.close()

    def callCWBServer(self,req):
        req = req.encode('utf-8')
        response = ''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
            s.connect((CWBHOST,CWBPORT))
            s.send(req)
            while True:
                tresp = s.recv(10241).decode('utf-8')
                response += tresp
                if response.find('<EOR>') > -1:
                    break


            s.close()
        except Exception as msg:
            try:
                time.sleep(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
                s.connect((CWBHOST,CWBPORT))
                s.send(req)
                response = s.recv(10241)
                s.close()
            except:
                pass
        return response

    def getStationByLocation(self,station,lat,lon,radius=0.2):
        req = "-delaz %.1f:%.4f:%.4f -c r \n" % (radius,lat,lon)
        pad = chr(0) * (80 - len(req))
        req = str(req + pad)
        response = self.callCWBServer(req)
        lines = response.split('\n')
        # Station  dist(deg) azimuth
        # LDBVD       0.16   193.62
        # LDBWD       0.16   217.09
        # LDWUPA      0.12   272.46
        # PEPSUB      0.00    22.52
        # SYP60A      0.18   230.81
        # SYPSUB      0.00   155.63
        # SYWUPA      0.12   272.46
        # TAP60A      0.18   230.81
        fullstation = None
        network = None
        for line in lines[1:]:
            parts = line.split()
            if re.search(station,parts[0]) is not None:
                fullstation = parts[0]
                network = fullstation.replace(station,'')
                break
        if fullstation is None:
            return station
        req = '-c c -s %s \n' % fullstation
        pad = chr(0) * (80 - len(req))
        req = str(req + pad)
        response = self.callCWBServer(req)
        lines = response.split('\n')
        for line in lines:
            if line.find('HHZ') > -1:
                parts = line.split(':')
                net,station,location,channel = parts[0].split()
                return '%s.%s.%s.%s' % (net,station,channel,location)
        return '%s.%s..' % (network)
        
    
    def getStationEpoch(self,station,phasetime):
        req = '-c c -s ..%s -b all \n' % station
        pad = chr(0) * (80 - len(req))
        req = str(req + pad)
        response = self.callCWBServer(req)
        lines = response.split('\n')
        epochs = []
        for line in lines:
            parts = line.split()
            if len(parts) < 9:
                continue
            datestr1 = parts[10]
            timestr1 = parts[11]+':00'
            datestr2 = parts[13]
            timestr2 = parts[14]+':00'
            t1 = datetime.strptime(datestr1 + ' ' + timestr1,'%Y-%m-%d %H:%M:%S')
            t2 = datetime.strptime(datestr2 + ' ' + timestr2,'%Y-%m-%d %H:%M:%S')
            epochs.append((t1,t2))
        etime = None
        for epoch in epochs:
            t1,t2 = epoch
            if phasetime > t1 - timedelta(seconds=86400*TIMERROR) and phasetime < t2 + timedelta(seconds=86400*TIMERROR):
                dt = t2-t1
                nseconds = dt.days*86400 + dt.seconds
                etime = t1 + timedelta(seconds=nseconds/2)
                if etime > datetime.utcnow():
                    etime = phasetime
                else:
                    pass
                break
        return etime

    def getIR(self,station):
        req = '-b all -a *.*.%s -c c \n' % station
        pad = chr(0) * (80 - len(req))
        req = str(req + pad)
        response = self.callCWBServer(req)
        lines = response.split('\n')
        nscl = station
        for line in lines:
            parts = line.split(':')
            if len(parts) < 2:
                continue
            f,d,s,n = parts[0].split('.')
            if f.lower() not in ['isc','iris']:
                continue
            nscl = '%s.%s..' % (d,s)
            break
        return nscl
    
    def getFSDN(self,station):
        req = '-c c -a FDSN.IR.%s -c c \n' % station
        pad = chr(0) * (80 - len(req))
        req = str(req + pad)
        response = self.callCWBServer(req)
        lines = response.split('\n')
        fsdn = station
        for line in lines:
            parts = line.split(':')
            if len(parts) < 2:
                continue
            parts = parts[0].split('.')
            if len(parts) < 2:
                continue
            if parts[2] != station:
                continue
            fsdn = '%s.%s..' % (parts[1],parts[2])
            break
        return fsdn
    
    def getNSCL(self,station,phasetype,phasetime):
        stationkey = station+'-'+phasetype[0:1]
        if stationkey in self.stationdict:
            #sys.stderr.write('Using cached station key %s\n' % stationkey)
            return self.stationdict[stationkey]
        
        dt = timedelta(seconds=86400)
        preferred = station
        epoch = self.getStationEpoch(station,phasetime) #get a date where valid metadata is available
        if epoch is not None:
            timestr = (epoch+dt).strftime('%Y/%m/%d')
            okchannels = ['HH','BH','SH','HN']
            scode = '..%s' % (station)
            req = '-c c -s %s -b %s \n' % (scode,timestr)
            pad = chr(0) * (80 - len(req))
            req = str(req + pad)
            response = self.callCWBServer(req)
            lines = response.split('\n')
            if response.find('no channels found to match') > -1:
                preferred = station
                lines = []
        else:
            lines = []
        nscl_list = []
        for line in lines:
            parts = line.split(':')
            if len(parts) < 2:
                continue
            net,sta,loc,channel = parts[0].split()
            if sta.lower() != station.lower():
                continue
            if channel[0:2] not in okchannels:
                continue
            if phasetype.lower().startswith('p') and not channel.lower().endswith('z'):
                continue
            if phasetype.lower().startswith('s') and re.search('[1|2|E|N]$',channel) is None:
                continue
            nscl = '%s.%s.%s.%s' % (net,sta,channel,loc)
            nscl_list.append(nscl)

        for nscl in nscl_list:
            net,sta,channel,loc = nscl.split('.')
            if channel.lower().startswith('hh'):
                preferred = nscl
                break
            if channel.lower().startswith('bh'):
                preferred = nscl
                break
            if channel.lower().startswith('sh'):
                preferred = nscl
                break
            if channel.lower().startswith('hn'):
                preferred = nscl
                break
        if preferred == station:
            preferred = self.getFSDN(station)
        if preferred == station:
            preferred = self.getIR(station)
        self.stationdict[stationkey] = preferred
        return preferred
