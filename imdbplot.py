#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 09:38:43 2023

@author: tom

Average ratings over time for IMDB data
"""
'''
#Uses conda env in environment.yml
conda env create --name dataviz --file environment.yml

Assumes you have downloaded daily data from

https://datasets.imdbws.com/title.ratings.tsv.gz

And once from
https://datasets.imdbws.com/title.basics.tsv.gz

Documentation https://developer.imdb.com/non-commercial-datasets/

'''

SAVEENV = False #toggle, export conda environment

# -----------------------------------------------   set up environment

import socket #to get host machine identity
import os #file and folder functions
import numpy as np #number function
import pandas as pd #dataframes!
import matplotlib.pyplot as plt #plotting function
#matplotlib named colours https://matplotlib.org/stable/gallery/color/named_colors.html
import glob
import datetime

print("identifying host machine")
#test which machine we are on and set working directory
if 'tom' in socket.gethostname():
    os.chdir('/home/tom/t.stafford@sheffield.ac.uk/A_UNIVERSITY/toys/imdb')
else:
    print("Running in expected location, we are in :" + os.getcwd())
    print("Maybe the script will run anyway...")
    
#export environment in which this was last run
if SAVEENV:
    os.system('conda env export > environment.yml') 


# -----------------------------------------------   which movies to look at

# import movie budgets from thenumbers.csv

filename = 'titleinfo/thenumbers.csv'

mf = pd.read_csv(filename, sep=',')

mf.columns=['released','title','budget','domestic','international','worldwide']

mf['budget']=pd.to_numeric(mf['budget'].str.replace('$','').str.replace(',',''), errors='coerce')   
mf['worldwide']=pd.to_numeric(mf['worldwide'].str.replace('$','').str.replace(',',''), errors='coerce')   
mf['domestic']=pd.to_numeric(mf['domestic'].str.replace('$','').str.replace(',',''), errors='coerce')   
#sort by production budget descending
mf = mf.sort_values(by=['budget'], ascending=False)


# we only have daily rating data from 12 april

#convert values in the format "May 19, 2023" to datetime
mf['released'] = pd.to_datetime(mf['released'], format='%b %d, %Y')

#drop rows released before 2023-04-12
mf = mf[mf['released'] > '2023-04-12'] #len(mf) = 59

#arbitrarily look at the top 20 funded movies, released after we started collecting data
mf=mf[:20]


# -----------------------------------------------   get imdb codes


# ---- get title info
fileloc =  'titleinfo/'
filename = 'title.basics.tsv.gz'
# unzip .gz file to subdirector /unzipped/
os.system('gunzip -c ' + fileloc+filename + ' > unzipped/' + filename[:-3])
# load unzip tsv file into dataframe
tf = pd.read_csv('unzipped/' + filename[:-3], sep='\t')

#convert column startYear to numeric
tf['startYear'] = pd.to_numeric(tf['startYear'], errors='coerce')

#remove rows with no startYear
tf = tf[tf['startYear'].notna()]

#remove rows with startYear < 2023
tf = tf[tf['startYear'] > 2022]

#remove shorts
tf = tf[pd.to_numeric(tf['runtimeMinutes'], errors= 'coerce') > 90]

#remove TV series
tf = tf[tf['titleType'] == 'movie']

#now add tconst to mf by merging on mf['title#'] and tf['primaryTitle']
mf = pd.merge(mf, tf[['tconst','primaryTitle']], left_on=['title'],right_on=['primaryTitle'], how='left')

#correcting some errors
'''
MI tt9603212
GG tt6791350
TMNT tt8589698
'''
#drop row where tconst is tt27834173
mf = mf[mf['tconst'] != 'tt27834173'] #copyrcat movie, not the blockbuster

#where row title is 'Mission: Impossible Dead Reckoning Pa…' set tconst to tt9603212
mf.loc[mf['title'] == 'Mission: Impossible Dead Reckoning Pa…', 'tconst'] = 'tt9603212'
#change this row title to 'Mission: Impossible Dead Reckoning Part One'
mf.loc[mf['title'] == 'Mission: Impossible Dead Reckoning Pa…', 'title'] = 'Mission: Impossible Dead Reckoning Part One'

#where row title is 'Guardians of the Galaxy Vol 3' set tconst to tt6791350
mf.loc[mf['title'] == 'Guardians of the Galaxy Vol 3', 'tconst'] = 'tt6791350'

#where row title is 'Teenage Mutant Ninja Turtles: Mutant …' set tconst to tt8589698
mf.loc[mf['title'] == 'Teenage Mutant Ninja Turtles: Mutant …', 'tconst'] = 'tt8589698'
#change this row title to 'Teenage Mutant Ninja Turtles: Mutant Mayhem'
mf.loc[mf['title'] == 'Teenage Mutant Ninja Turtles: Mutant …', 'title'] = 'Teenage Mutant Ninja Turtles: Mutant Mayhem'

#drop column 'primaryTitle')
mf = mf.drop(columns=['primaryTitle'])


# -----------------------------------------------   get imdb ratings


#from mf get list of tconst values
ourmoviecodes = mf['tconst'].tolist()



#get list of ratings files
files = glob.glob('imdbratings*.tsv.gz')

rating_df=pd.DataFrame()


for filename in files:

    try:

        # unzip .gz file to subdirector /unzipped/
        os.system('gunzip -c ' + filename + ' > unzipped/' + filename[:-3])

        # load unzip tsv file into dataframe
        df = pd.read_csv('unzipped/' + filename[:-3], sep='\t')

        #drop all rows where tconst isn't in our list of movies
        df = df[df['tconst'].isin(ourmoviecodes)]

        #extract date from filename, counting from end not the beginning so extra B in somefiles is accounted for
        date = filename[-17:-7]

        df['date'] = date

        #append df to rating_df, dropping the index column
        rating_df = rating_df.append(df, ignore_index=True)
    except:
        print('error with file ' + filename)



# -----------------------------------------------   plot average ratings over time



#make a list of colors as long as ourmoviecodes using the rainbow colormap
colors = plt.cm.tab20(np.linspace(0,1,len(ourmoviecodes)))

#jitter on labels
upmovies =['tt1462764','tt15153532','tt15671028']
downmovies = ['tt9603212','tt11358390']


plt.clf()

for movie in ourmoviecodes:

    moviecolor = colors[ourmoviecodes.index(movie)]

    if movie in upmovies:
        offset = 0.1
    elif movie in downmovies:
        offset = -0.1
    else:
        offset = 0


    df = rating_df[rating_df['tconst'] == movie]

    #get movietitle from mf using tconst
    movietitle = mf[mf['tconst'] == movie]['title'].iloc[0]

    #sort df by date
    df = df.sort_values(by=['date'])

    #convert date to datetime
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    #find latest date in df (works because we sorted by date)
    latestdate = df['date'].iloc[-1]

    #get latest averageRating on that date
    latestrating = df['averageRating'].iloc[-1]

    #get highest rating
    maxrating = df['averageRating'].max()

    #get max numVotes
    maxvotes = df['numVotes'].max()

    #add latestrating and maxrating to the appropriate row in mf
    mf.loc[mf['tconst'] == movie, 'latestrating'] = latestrating
    mf.loc[mf['tconst'] == movie, 'maxrating'] = maxrating
    mf.loc[mf['tconst'] == movie, 'maxvotes'] = maxvotes

    
    #add column days prior to most recent
    df['days'] = (df['date'] - latestdate).dt.days

    #plt.plot(df['days'],df['averageRating'],'-',lw=3,color='white')
    plt.plot(df['days'],df['averageRating'],'-',lw=2,color=moviecolor)   

    #annotate right point with title of movie, smaller font
    plt.annotate(movietitle, (df['days'].iloc[-1]+5, df['averageRating'].iloc[-1]+offset), fontsize=7,color=moviecolor)   
    

#remove top and right border on plot
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
#label axes
today = datetime.date.today().isoformat()

plt.annotate('CC-BY Tom Stafford 2023', (0.05, 0.06), fontsize=7,color='gray',xycoords='axes fraction',ha='left',va='center')
plt.xlabel('Days prior to ' + today)
plt.ylabel('Average IMDB rating')

plt.savefig('plots/average_ratings_noocclusion.png', dpi=450,facecolor='white',bbox_inches="tight")


# -----------------------------------------------   budget bump

mf['boost']=mf['maxrating']-mf['latestrating']

omitlist=['tt9362930']#['tt9603212','tt6791350','tt8589698']

#jitter on labels
upmovies =['tt1462764','tt15671028','tt1517268','tt15789038']
downmovies = ['tt9603212','tt11358390']

scalingfactor = 5000 #larger -> smaller

plt.clf()

for index,row in mf.iterrows():


    movie = row['tconst']

    if movie in upmovies:
        offset = 0.05
    elif movie in downmovies:
        offset = -0.05
    else:
        offset = 0

    moviecolor = colors[ourmoviecodes.index(movie)]

    votesize = np.sqrt(row['maxvotes']/scalingfactor) #np.log(row['maxvotes'])/scalingfactor

    plt.plot(row['budget']/1000000,row['boost'],color=moviecolor,marker='o',ms=votesize)
    #annotate point with movie title
    if movie not in omitlist:
        plt.annotate(row['title'], (row['budget']/1000000+5, row['boost']+offset), fontsize=7,color=moviecolor)  



plt.xlabel('Production budget ($M)')
plt.ylabel('Rating boost\n(max rating - latest rating)') 
#remove top and right border on plot
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

#add note in middle right
plt.annotate('Point size proportional\nto number of votes', (0.95, 0.85), fontsize=7,color='black',xycoords='axes fraction',ha='right',va='center')
plt.annotate('CC-BY Tom Stafford 2023', (0.95, 0.75), fontsize=7,color='black',xycoords='axes fraction',ha='right',va='center')

plt.savefig('plots/boost.png', dpi=450,facecolor='white',bbox_inches="tight")

