#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 01:03:14 2018

@author: anshulsaxena
"""
#how to run the file:
#runfile('/Users/anshulsaxena/Dropbox/VOCIQ/api_calls/youtube_video_comments_from_google_api.py', args='OEydHbngSz0', wdir='/Users/anshulsaxena/Dropbox/VOCIQ/api_calls')

#https://developers.google.com/youtube/v3/docs/commentThreads/list
#but that has the client_secrets.json file problem
import sys
import pandas as pd
import time
import numpy as np

from apiclient.discovery import build
from apiclient.errors import HttpError

 # arguments to be passed to build function
DEVELOPER_KEY = "AIzaSyAsJDajMRLwrzkkRO1VAkK6BSihH3s-Qco"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
    
# creating youtube resource object for interacting with API
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=DEVELOPER_KEY)


review_list=[] #Kind of Global: This list stores the top level comments and their replies here
review_list_headers=['Video_id','Author','review','date'] #to insert this as header of review file
result_list=[]
pageToken_list=[]
youtube_video_list=[]
youtube_video_list_headers=[]
dataframe_list=[]
dataframe_dict={"0":"video_list","1":"comments"}

#for debugging purposes:
search_response_list=[]
response_list=[]
result_list_replies=[]
search_result_list=[]

#youtube_search method extracts the summary information of the videoId such as like count
def youtube_search(q,max_results=50,order="relevance", token=None, location=None, location_radius=None):
    print("in youtube_search")
   
    search_response = youtube.search().list(
            q=q,
            type="video",
            pageToken=token,
            order=order,
            part="id,snippet", #Part signifies the different kinds of data you want
            maxResults=max_results,
            location=location,
            locationRadius=location_radius).execute()
    
    search_response_list.append(search_response)
    
    channelId = []
    channelTitle = []
    categoryId = []
    viewCount = []
    likeCount = []
    dislikeCount = []
    commentCount = []
    favoriteCount = []
    category = []
    tags = []
    videos = []
    
    
    for search_result in search_response.get("items",[]):
        
        #just for debugging:
        search_result_list.append(search_result)
       
        if search_result["id"]["kind"]=="youtube#video":
            youtube_video_list_headers.append('title')
            title=search_result['snippet']['title']
            
            
            youtube_video_list_headers.append('videoId')
            videoId=search_result['id']['videoId']
           
           
            response=youtube.videos().list(
                    part='statistics,snippet',
                    id=search_result['id']['videoId']).execute()
            
            response_list.append(response)
          
            youtube_video_list_headers.append('channelId')
            channelId=response['items'][0]['snippet']['channelId']
            

            
            youtube_video_list_headers.append('channelTitle')
            channelTitle=response['items'][0]['snippet']['channelTitle']
            
            
            youtube_video_list_headers.append('categoryId')
            categoryId=response['items'][0]['snippet']['categoryId']
            
            
            youtube_video_list_headers.append('favoriteCount')
            favoriteCount=response['items'][0]['statistics']['favoriteCount']
            
            
            youtube_video_list_headers.append('viewCount')
            viewCount=response['items'][0]['statistics']['viewCount']
            
            
            youtube_video_list_headers.append('likeCount')
            likeCount=response['items'][0]['statistics']['likeCount']
           
            
            youtube_video_list_headers.append('dislikeCount')
            dislikeCount=response['items'][0]['statistics']['dislikeCount']
            
            
            
        #youtube_dict = {'tags':tags,'channelId': channelId,'channelTitle': channelTitle,'categoryId':categoryId,'title':title,'videoId':videoId,'viewCount':viewCount,'likeCount':likeCount,'dislikeCount':dislikeCount,'commentCount':commentCount,'favoriteCount':favoriteCount}
        youtube_video_list.append([title,videoId,channelId,channelTitle,categoryId,\
                                   favoriteCount,viewCount,likeCount,dislikeCount])
        df1=pd.DataFrame.from_records(youtube_video_list,\
                                      columns=youtube_video_list_headers)
        dataframe_list.append(df1)
       


# Call the API's commentThreads.list method to list the existing comment threads.
def get_comment_threads(video_id,nextPageToken=""):
    print("in get_comment_threads")
    pageToken_list.append(nextPageToken)
    results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
            ,pageToken=nextPageToken
        ).execute()
    
    result_list.append(results)
   
    for item in results["items"]:
        comment = item["snippet"]["topLevelComment"]
        author = comment["snippet"]["authorDisplayName"]
        text = comment["snippet"]["textDisplay"]
        date=comment["snippet"]["updatedAt"][:10]
        date=date[8:10]+"/"+date[5:7]+"/"+date[:4]
        review_list.append([video_id,author,text,date])
        if(int(item["snippet"]["totalReplyCount"]))>0:
            parent_id=item["id"]
            get_comment_replies(parent_id,video_id)
    
    if "nextPageToken" in results:
        print("nextPage exists")
        get_comment_threads(video_id,results["nextPageToken"]) 
        return 1           
    
    print("end of get_comment_threads")
    
    #Now we have all top level comments and their replies in review_list
    #So, let's write them to xlsx file
    df2=pd.DataFrame.from_records(review_list,\
                                      columns=review_list_headers)
    dataframe_list.append(df2)
    
    return results["items"]


# Call the API's comments.list method to list the existing comment replies.
def get_comment_replies(parent_id,video_id):
    #print("in get_comments")
    results = youtube.comments().list(
    part="snippet",
    parentId=parent_id,
    textFormat="plainText"
  ).execute()
    #result_list_replies.append(results)
    for item in results["items"]:
        author = item["snippet"]["authorDisplayName"]
        text = item["snippet"]["textDisplay"]
        date=item["snippet"]["updatedAt"][:10] #result:2018-01-12
        date=date[8:10]+"/"+date[5:7]+"/"+date[:4] #result:12-01-2018
        review_list.append([video_id,author,text,date])
    
       
def write_to_file():    
    print("in write to file")
    
    writer=pd.ExcelWriter('youtube_report.xlsx',engine='xlsxwriter')
    dataframe_list[0].to_excel(writer,sheet_name=dataframe_dict["0"],index=False)
    dataframe_list[1].to_excel(writer,sheet_name=dataframe_dict["1"],index=False)
    
    
    writer.save()
    writer.close()
    print("Succesfully written to file youtube_report.xlsx") 
   

if __name__ == "__main__":
    
    startTime=time.asctime(time.localtime(time.time()))
    print("processing Start time")
    print(startTime)
    

    try:
        video_id=sys.argv[1]
        youtube_search(video_id)
        video_comment_threads = get_comment_threads(video_id)
        write_to_file()
       
    except IndexError as ixe:
       print ("An Index error occurred: You may not have specified the video_id in the command line argument")
    except IOError as ioe:
        print ("I/O error %d occurred:\n%s" %(ioe.resp.status, ioe.content))
    except HttpError as hte:
        print ("An HTTP error %d occurred:\n%s" %(hte.resp.status, hte.content))
    else:
        endTime=time.asctime(time.localtime(time.time()))
        print("processing End time")
        print(endTime)
        
