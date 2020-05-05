import datetime
def dataPreprocesser(path:str,data:dict,static_attributes:dict):
    
    
    value,timestamp=dataClean(path,data["count"],data["timestamp"])
    
    __elarycheckResult__=elaryCheck(path,value,timestamp,static_attributes)
    
    
    return __elarycheckResult__,{"value":value,"timestamp":timestamp}

def dataClean(path:str,value:str,timestamp:str):
    #TODO:Cleanup data
    timestamp=datetime.datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%S.00Z')
    return value,timestamp

def elaryCheck(path:str,value:str,timestamp:object,static_attributes:dict):
    __LOCALDATA__=path+"/localdata.tmp"
    __COUNTER__=path+"/counter.tmp"
    __LOCALNEWEST__=path+"/localnewest.tmp"
    with open(__COUNTER__,"r") as c:
        count=int(c.read())
    __CHECKRESULT__=[]
    if count==0:
        pass
    else:
        __CHECKRESULT__=timeperoidCheck(__LOCALNEWEST__,timestamp,int(static_attributes["timeResolution"]),__CHECKRESULT__)
        __CHECKRESULT__=timeserialCheck(__LOCALNEWEST__,timestamp,__CHECKRESULT__)
    
    return __CHECKRESULT__

def timeperoidCheck(newestpath,timestamp,timeResolution,__CHECKRESULT__):
    with open(newestpath,"r") as f:
        newest=f.read()
    newest=newest.split(",")
    
    Oldtimestamp=datetime.datetime.strptime(newest[1],'%Y-%m-%d %H:%M:%S')
    timedelta=(timestamp-Oldtimestamp).total_seconds()
    if timedelta>=(timeResolution*10):
        __CHECKRESULT__.append(1)
    return __CHECKRESULT__
def timeserialCheck(newestpath,timestamp,__CHECKRESULT__):
    with open(newestpath,"r") as f:
        newest=f.read()
    newest=newest.split(",")
    
    Oldtimestamp=datetime.datetime.strptime(newest[1],'%Y-%m-%d %H:%M:%S')
    timedelta=(timestamp-Oldtimestamp).total_seconds()
    if timedelta<=0:
        __CHECKRESULT__.append(2)
    return __CHECKRESULT__