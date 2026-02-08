import matplotlib.pyplot as plt


def horizontalbarchart(gdp):
    
    names = [list(row.keys())[0] for row in gdp]
    values = [list(row.values())[0] for row in gdp]
    plt.figure(figsize=(10, 12))
    plt.barh(names, values, color='skyblue')
    plt.xlabel('GDP (USD)')
    plt.ylabel('Country')
    plt.title('GDP Comparison by country')

    # This puts the first item in your list at the top instead of the bottom
    plt.gca().invert_yaxis()

    plt.tight_layout()
    plt.show()

def piechart(gdp):
    # Sort the data and take only the top 10
    sorted_gdp = sorted(gdp, key=lambda x: list(x.values())[0], reverse=True)[:10]
    names = [list(row.keys())[0] for row in sorted_gdp]
    values = [list(row.values())[0] for row in sorted_gdp]
    plt.figure(figsize=(10, 7))
    plt.pie(values, labels=names, autopct='%1.1f%%', startangle=140)
    plt.title('Top 10 GDP Shares in the Region')
    #plt.axis('equal')
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
    piechart(gdp)
def visualizeDataofCountry(gdp):
   barchart(gdp)
   scatterplot(gdp)




