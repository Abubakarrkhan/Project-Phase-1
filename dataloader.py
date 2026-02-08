import json 
import csv 

# r mean for reading 

def loadConfig(file='config.json'):#giving default parameter of config.json
    try:
        with open (file,'r') as userdata:
            userInput= json.load(userdata)#a dict of user input(file)
            if userInput["region"]=="":
                raise ValueError("Empty region in file")
            if userInput["year"]<0 or userInput["year"]=="":
                raise ValueError("Negative or empty year in file")
            if userInput["operation"]!='sum' and userInput["operation"]!='average':
                raise ValueError("Invalid operation")
            if userInput["output"]!='dashboard':
                raise ValueError("Invalid output window")
            return userInput
    except FileNotFoundError:
        print("File not found")
        return None  


def clean(file='gdp.csv'):  #python treat values as string when DictReader, change it to float , in case of empty value place 0.0 
    try :
        with open(file,'r') as regionsData:
            reader=csv.DictReader(regionsData)
            cleaned = map(lambda row: {
                key: (float(value) if value.strip() else 0.0) if key.isdigit() else value 
                for key, value in row.items()
            }, reader)
            return list(cleaned)
    except FileNotFoundError:
        print("File not found ")
        return None




def findrow(row,config):
    if  row["Continent"]==config["region"] or row["Country Name"]==config["region"]: 
        return True
    else: 
        return False 


def get_countries(config,cleanedData):#cleanedData is list of dictionary
        try:
            return list(filter(lambda row: findrow(row, config), cleanedData))#make list of dictionary
        except FileNotFoundError:
            print("File not found")
            return None





