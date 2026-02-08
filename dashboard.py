import dataloader
import dataprocessor
import visualization

config=dataloader.loadConfig('config.json')

cleaned=dataloader.clean('gdp.csv')#cleaned is list of dictionary(convert dataType of string(gdp value) to float and empty gdp value to 0.0)

regionList=dataloader.get_countries(config,cleaned)# short list the input countries

if len(regionList)==0:# mean user entered region/country not available
    raise RuntimeError("Invalid Region in input")

gdpList=dataloader.get_gdp_list(config,regionList)# get a dictionary 
result = dataprocessor.doOperation(config,gdpList)# apply operation


print("The selected records from user data is : ")
print(regionList)

if len(regionList)==1:
    print("The " ,config["operation"] ," of all years of ",config["region"], " is ", result)
    visualization.visualizeDataofCountry(gdpList)
else: 
    print("The " ,config["operation"] ," of all countries of ",config["region"], " is ", result)
    visualization.visualizeDataofRegion(gdpList)





def getDictionaryofAllRegion(row, year):
    return { row["Country Name"]: row.get(str(year), 0.0)}#str(year)convert int to str eg 2020 to "2020" so now we can access easily 



def getDictionaryofACountry(row):
    return list({ year: row.get(str(year), 0.0)} for year in range(1960, 2025))


def get_gdp_list(config, countries):# countries is list of dictionary
    if len(countries)!=1:
        target_year = config["year"]
        return list(map(lambda row: getDictionaryofAllRegion(row, target_year), countries))
    else : 
        return getDictionaryofACountry(countries[0])


