def sensorCheck(setting):
    sensor_info=setting["sensor_info"]
    must_list=[
        "deviceID",
        "timeResolution",
        "sensorName",
        "fieldName",
        "refRoom",
        "sensorType",
        "unit",
        "dummy",
        "measurement"]
    lost_list=[]
    for attr in must_list:
        if attr not in sensor_info:
            lost_list.append(attr)
    if lost_list!=[]:
        return lost_list
    else:
        return 0
    