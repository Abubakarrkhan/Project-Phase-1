import dataloader
import validcontinent
import json
from functools import reduce
askregion=None
askcountry=None
time=None
outputwindow=None
operation=None
with open("config.json", "r") as file:
    data = json.load(file)
    askregion=data["region"]
    time=str(data["year"])
    outputwindow=(data["output"])
    operation=(data["operation"])
regiondata=list(filter(lambda x: validcontinent.isvalidregion(x, askregion), dataloader.yearlygdp))
index=None
timedata=None;
timedata_=None;
sum=None;
if time in dataloader.years and regiondata:
    index=dataloader.years.index(time)+1;

    timedata_=list(map(lambda x:validcontinent.atvalidtime(x,index),regiondata))
    timedata=list(filter(lambda t:validcontinent.removenill(t),timedata_))
    if not timedata:
        timedata=[["No country data is entered","0"]]
        sum=["0"];
    else:

        sum=reduce(lambda acc,x:validcontinent.findsum(acc,x),timedata,["0"])
        if operation=="average" and len(timedata):
             sum[0]=str(float(sum[0])/len(timedata))

elif not regiondata:
    timedata=[["No region exists with this name","0"]]
    sum=["0"];
else:
    timedata=[["No time exists","0"]]
    sum=["0"];
