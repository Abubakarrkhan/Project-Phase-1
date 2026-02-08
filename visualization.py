import matplotlib.pyplot as plt


def horizontalbarchart(gdp):
    
    names = [list(row.keys())[0] for row in gdp]
    values = [list(row.values())[0] for row in gdp]

    plt.barh(names, values, color='skyblue')
    plt.xlabel('GDP (USD)')
    plt.ylabel('Country')
    plt.title('GDP Comparison by country')

    # This puts the first item in your list at the top instead of the bottom
    plt.gca().invert_yaxis() 
    plt.show()

def barchart(gdp):
    names = [list(row.keys())[0] for row in gdp]
    values = [list(row.values())[0] for row in gdp]
    plt.bar(names, values, color='skyblue')
    plt.ylabel('GDP (USD)')
    plt.xlabel('Year')
    plt.title('GDP Comparison by year')
    plt.show()

def scatterplot(gdp):
   names=[list(row.keys())[0] for row in gdp]
   values=[list(row.values())[0] for row in gdp]
   plt.title('GDP Comparison by year')
   plt.xlabel("Years")
   plt.ylabel("gdp")
   plt.scatter(names,values)
   plt.show()



def visualizeDataofRegion(gdp):
    horizontalbarchart(gdp)

def visualizeDataofCountry(gdp):
   barchart(gdp)
   scatterplot(gdp)




