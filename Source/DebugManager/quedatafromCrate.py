import pprint
import requests
import datetime
header={'Content-Type': 'application/json'}
sql='{"stmt":"SELECT * FROM mtiota001.etsensor WHERE \
    time_index >= DATE_TRUNC (\'second\',\'2010-07-02T00:00:00.00Z\') AND \
    entity_id=\'urn:ngsi-ld:Temperature:02\'ORDER BY time_index"}'
r=requests.get("http://fiware-cratedb:4200/_sql",headers=header,data=sql)
info=r.json()
cols=info["cols"]
rows=info["rows"]

output=[{cols[i]:x[i] for i in range(len(cols))} for x in rows]
for idx,val in enumerate(output):
    timestampint=val["time_index"]
    t=(datetime.timedelta(seconds=timestampint/1000)+datetime.datetime(1970,1,1))
    print(idx+1,":",val["count"],val["predictionvalue"],t)