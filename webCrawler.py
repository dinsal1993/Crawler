import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
import time
from collections import OrderedDict
import xlsxwriter
import math
import numpy as np

##creates 2 excel sheets for each call
#AllProducts - all the results from the query
#ValidProducts - all the results that match the query filter
def CrawlForIngredients(url, search, num, tfIdf, query):
    tp = 0
    fp = 0
    numItems = 0
    
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    URL = url
    r = requests.get(url=URL, headers=headers)
  
    soup = BeautifulSoup(r.content, 'html5lib')
    
################################################
# Get Links to all products in page 1
    links=[]  # a list to store links to items
    descriptions = []
    dictionary = {}

#load all products in page
    while True:
    #get container that has all the products in the page
        table = soup.find('section', attrs = {'class':'listingPage_RIQzl'}) 
        while table is None:
            r = requests.get(url=URL, headers=headers)
          
            soup = BeautifulSoup(r.content, 'html5lib')
            time.sleep(0.25)
            table = soup.find('section', attrs = {'class':'listingPage_RIQzl'}) 
            print("table is none. trying again.")
            
    #get links of all products
        for row in table.findAll('article', attrs = {'class':'productTile_U0clN'}):
            link = row.a['href']
            links.append(link)
        
    #check if there are more pages to the query
        progressBar = soup.find('progress', attrs = {'class': 'progressBar_anIzC'})
        
        if progressBar['max'] != progressBar['value']:
            nextPage = soup.find('a', attrs = {'data-auto-id': 'loadMoreProducts'})
            URL = nextPage['href']
            r = requests.get(url=URL, headers=headers)
            soup = BeautifulSoup(r.content, 'html5lib')    
        else:
            break
   


##########################################
# For each product, if valid - add to array of final products
#valid = has 100% cotton
    products = []
    i = 1
    for link in links:
    #for every product, seperate description words, check if valid
    #if valid add to list

        headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
        URL = link
        r = requests.get(url=URL, headers=headers)
        soup = BeautifulSoup(r.content, 'html5lib')
    
        aboutMeDiv = soup.find('div', attrs= {'id':'productDescriptionAboutMe'})
        if aboutMeDiv is None:
            if numItems < 10:
                fp = fp + 1
            print("product out of stock. num: " + str(i))
            descriptions.append("product out of stock")
        else:
            aboutMe = aboutMeDiv.find('div', attrs= {'class':'F_yfF'}).text
            print("product " + str(i))
            #some text refinement for building inverted index automatically
            aboutMe = aboutMe.replace(":", "")
            aboutMe = aboutMe.replace(".", "")
            aboutMe = aboutMe.replace(",", "")
        
            place = 0
            for x in aboutMe:
                if x == x.upper() and place > 0 and ord(x) >= 65 and ord(x) <= 90 and aboutMe[place] != " ":
                    aboutMe = aboutMe[:place] + " " + aboutMe[place:]
                place = place + 1
                
            if aboutMe.__contains__(search):
                products.append(link)
                if numItems < 10:
                    tp = tp + 1
            else:
                if numItems < 10:
                    fp = fp + 1
        
            descriptions.append(aboutMe)
            
        numItems = numItems + 1
        i = i + 1
        if i == 51:
            break
    

    #make dictionary that contain every word with 
    #how many times every word occoured
    for item in descriptions:
        temp = item.split()
        for word in temp:
            if word in dictionary:
                dictionary[word] = dictionary[word] + 1
            else:
                dictionary[word] = 1


    d_descending = OrderedDict(sorted(dictionary.items(), 
                                  key=lambda kv: kv[1], reverse=True))
    print("occurences of each word:\n")
    tempList = d_descending.items()
    for x in tempList:
        print (str(x) + "\n")
    #print(d_descending)
    print("\n")
    
    #inverted index
    
    j = 0 # product number
    k = 0 # number of words to check
    z = 0 # give location of only first 20 pages
    invertedIndex = []

    for word in d_descending:
        z = 0
        tempList = []
        tempList.append(word)
        j = 0
        for prod in descriptions:
            if z == 20:
                break
            if prod.__contains__(word):
                tempList.append(j)
                z = z + 1
            j = j + 1
        invertedIndex.append(tempList)
        k = k + 1
        if k == 15:
            break
    
    print("\nInverted Index:\n")
    for x in invertedIndex:
        print(x)
    #print(invertedIndex)
    print("\n")
           
    
    
        
    
    #Calculate tfIdf
    if tfIdf == 1:
        
        terms = query.split(" ")
        
        ###### tf
        tf = []
        for term in terms: # calculate tf for each term לכל דף יש אחד משלו
            temp = [term]
            
            for doc in descriptions: 
                frequency = 0
                
                if doc.__contains__(term): # contains term, calculate tf
                    words = doc.split(" ")
                    for word in words:
                        if word == term:
                            frequency = frequency + 1
                    temp.append(frequency)
                    
                else: # dont containt term, tf  = 0
                    temp.append(0)
                    
            tf.append(temp)
            
            print("tf: \n")
            for x in tf:
                print(str(x) + "\n")

        
        ######## df
        dfi = []    #document frequency for each term בכמה דפים מופיע מילה לכל מילה ערך אחד
        for term in terms:
            frequency = 0
            for doc in descriptions:
                if doc.__contains__(term):
                    frequency = frequency + 1
            if frequency == 0:
                frequency = 0.001
            dfi.append([term,frequency])
            
        print("df: \n")
        for x in dfi:
            print(str(x) + "\n")

            
        ######## idf
        idf = []
        D = len(descriptions)
        i = 0
        for term in terms:
            calc = math.log(D / dfi[i][1], 10)
            idf.append([term,calc])
            i = i + 1
            
        print("idf: \n")
        for x in idf:
            print(str(x) + "\n")

        
        ############ tf-idf matrix
        tf_idf = []
        termNum = 0
        j = 0 # the index of idf
        for term in terms:
            temp = [term]
            k = 0
            for i in tf[termNum]:
                if k != 0:
                    calc = i * idf[j][1]
                    temp.append(calc)
                else:
                    k = k + 1
                
            j = j + 1
            termNum = termNum + 1
            tf_idf.append(temp)
        
        print("tf-idf: \n")
        print("prints the term. then each element in the list is the tf-idf of" + 
              " corresponding number. so arr[1] is tf_idf of document 1\n")
        for x in tf_idf:
            print(str(x) + "\n")

                
        
        
    else:
        if num == 1:
            workbook = xlsxwriter.Workbook('AllProductsShirt.xlsx')
        else:
            workbook = xlsxwriter.Workbook('AllProductsShoes.xlsx')
        
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0

    #make excel file
        for item in links:
            worksheet.write(row, col, item)
            col = 1
            worksheet.write(row, col, descriptions[row])
            col = 0
            row = row + 1
            #if row == 50:
            #    break
        

        workbook.close()


        productsData = pd.DataFrame(products)

        if num == 1:
            productsData.to_excel('ValidproductsShirt.xlsx')
        else:
            productsData.to_excel('Validproductsshoes.xlsx')
        return tp, fp, links.__len__()

#tp1, fp1, length = CrawlForIngredients("https://www.asos.com/search/?q=men+shirt+100%25+cotton","100% Cotton",1, 0, "")

#assume 25% not retrived 
#fn = math.floor(length * 0.25)
#precision = tp1 / tp1 + fp1
#recall = tp1 / tp1 + fn

#print("First Query:\nPrecision: " + str(precision) + ", recall: " + str(recall))

#print("\n")

#inverted index is written inside the function
#tp1, fp1, length = CrawlForIngredients("https://www.asos.com/search/?q=shoe%20lining%3A%20100%25%20polyurethane","100% Polyurethane",2, 0, "")

#assume 25% not retrived 
#fn = math.floor(length * 0.25)
#precision = tp1  / tp1 + fp1
#recall = tp1 / tp1 + fn

#print("Second Query:\nPrecision: " + str(precision) + ", recall: " + str(recall))

#print tf-idf
CrawlForIngredients("https://www.asos.com/search/?q=men+shirt+100%25+cotton","100% Cotton",1, 1, "men shirt 100% Cotton")