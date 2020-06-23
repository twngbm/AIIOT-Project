import datetime

timestampint=1278034200000
timestr="2010-07-02 01:30:00"
timestamp=datetime.datetime.strptime(timestr,"%Y-%m-%d %H:%M:%S")
t=(timestamp-datetime.datetime(1970,1,1)).total_seconds()*1000
print(int(t)==timestampint)
t=(datetime.timedelta(seconds=timestampint/1000)+datetime.datetime(1970,1,1))
print(t)