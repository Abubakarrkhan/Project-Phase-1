import matplotlib.pyplot as plt

def visualizeDataofRegion(gdp):
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

def visualizeDataofCountry(gdp):
    names = [list(row.keys())[0] for row in gdp]
    values = [list(row.values())[0] for row in gdp]

    plt.figure(figsize=(10, 12))
    plt.bar(names, values, color='skyblue')

    plt.ylabel('GDP (USD)')
    plt.xlabel('Year')
    plt.title('GDP Comparison by year')

    plt.tight_layout()
    plt.show()




