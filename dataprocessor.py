from functools import  reduce

def doSum(x, row):
    gdp_value = list(row.values())[0]
    return x + gdp_value

def doOperation(config,data):   
    sum= reduce(doSum,data,0.0) #function , iteratable,initalizer 
    if(config["operation"]=='sum'):
        return sum 
    elif config["operation"]=='average':
        return sum/len(data)
    else :
        return None


