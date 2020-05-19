import json
import csv
import requests
import time

with open("rec-center-every-15m-large.csv", "r") as f:
    rows = csv.reader(f, delimiter=",")
    header=next(rows)
    next(rows)
    next(rows)
    count=0
    for i in rows:
        count+=1
        print(count)
        print(i)
        header = {"Content-Type": "text/plain"}
        timestamp=str(i[0]).split(" ")
        ymd=timestamp[0].split("/")
        ymd="20"+ymd[2]+"-"+ymd[0]+"-"+ymd[1]
        timestamp=ymd+"T"+timestamp[1]
        print(timestamp)
        data = "COUNT|" + str(i[1]) + "|TS|" + timestamp
        r = requests.post(
            "http://fiware-iotagent:7896/iot/d?k=UskwkHiIMN05hLHvmOdnkPR2hAmFmwTi&i=Sensor02",
            headers=header,
            data=data,
        )
        print(r.status_code)
        no=input()
