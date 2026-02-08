import dataloader
import dataprocessor
import visualization


import os

# Get the directory where the script is located
base_path = os.path.dirname(__file__)

# Join it with your filename
json_path = os.path.join(base_path, 'config.json')
csv_path = os.path.join(base_path, 'gdp.csv')


config=dataloader.loadConfig(json_path)

cleaned=dataloader.clean(csv_path)#cleaned is list of dictionary(convert dataType of string(gdp value) to float and empty gdp value to 0.0)
regionList=dataloader.get_countries(config,cleaned)# short list the input countries

if len(regionList)==0:# mean user entered region/country not available
    raise RuntimeError("Invalid Region in input")

gdpList=dataloader.get_gdp_list(config,regionList)# get a dictionary 
result = dataprocessor.doOperation(config,gdpList)# apply operation

print("=========== GDP DASHBOARD ===========")
print("The selected records from user data is : ")
print(regionList)

if len(regionList)==1:
    print("The " ,config["operation"] ,"of gdp of all years(1960-2024) of ",config["region"], " is ", result)
    visualization.visualizeDataofCountry(gdpList)
else: 
    print("The " ,config["operation"] ," of gdp of all countries of ",config["region"], " is ", result)
    visualization.visualizeDataofRegion(gdpList)
