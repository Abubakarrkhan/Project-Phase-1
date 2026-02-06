import json 
import csv 

# r mean for reading 
with open ('config.json','r') as userdata:
    userinput=json.load(userdata)
# userinput becomes a dictionary that copy the data from the config.json file
# with indentation of 'with' close the json file is closed 

def findrow(row):
    if row[0]==userinput["region"]:
        return True 
    else: 
        return False 


with open ('gdp.csv','r') as gdpData:
    regionsData=csv.reader(gdpData)
# in csv file we do not copy but iterate over the file 
# if file is closed we cannot access again so we write in 'with' indentation
    
    userRegionData=filter(findrow,regionsData) # it is 2D list but we have only one matching country we will access its data by [0][colNumber]
    stored = list(userRegionData)
#hello 
print(stored[0][1])