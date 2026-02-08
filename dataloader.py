import csv

yearlygdp=[];
years=[];  
  
             



with open("gdp.csv", "r") as file:
    reader = csv.reader(file)
    i=0;
    rownum=-1;




    for row in reader:
        
        if i < 1:
           i+=1;
           for i in range(4,69,1):
               years.append(str(row[i]));
              
           #col 0 in the years array has the data starring from col 4 & row1 of the spreadsheet
           
           continue
        rownum=rownum+1;
        
        yearlygdp.append([])
        
        yearlygdp[rownum].append(str(row[0]))
       
        for i in range(4,70,1):
             yearlygdp[rownum].append(str(row[i]));
    
