import datetime

timestampint=1280435400000
timestr="2010-07-29 20:30:00"
timestamp=datetime.datetime.strptime(timestr,"%Y-%m-%d %H:%M:%S")
t=(timestamp-datetime.datetime(1970,1,1)).total_seconds()*1000
print(int(t)==timestampint)