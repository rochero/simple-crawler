import requests
from requests_html import HTMLSession
import json
import time
import re
from utils.save import append_data_xlsx

def launchbox():
    f = open('./data/launchbox/Metadata.xml', 'r+', encoding='utf-8',errors='ignore')
    s = f.read()
    f.close()
    l = re.findall('<Game>(.+?)</Game>', s, re.S)
    tags = []
    for i in l:
        Overview=re.search('<Overview>(.*?)</Overview>', i, re.S).group(1) if re.search('<Overview>(.*?)</Overview>', i, re.S) else ''
        CommunityRatingCount=re.search('<CommunityRatingCount>(.*?)</CommunityRatingCount>', i, re.S).group(1) if re.search('<CommunityRatingCount>(.*?)</CommunityRatingCount>', i, re.S) else ''
        Publisher=re.search('<Publisher>(.*?)</Publisher>', i, re.S).group(1) if re.search('<Publisher>(.*?)</Publisher>', i, re.S) else ''
        Genres=re.search('<Genres>(.*?)</Genres>', i, re.S).group(1) if re.search('<Genres>(.*?)</Genres>', i, re.S) else ''
        ReleaseDate=re.search('<ReleaseDate>(.*?)</ReleaseDate>', i, re.S).group(1) if re.search('<ReleaseDate>(.*?)</ReleaseDate>', i, re.S) else ''
        DatabaseID=re.search('<DatabaseID>(.*?)</DatabaseID>', i, re.S).group(1) if re.search('<DatabaseID>(.*?)</DatabaseID>', i, re.S) else ''
        ESRB=re.search('<ESRB>(.*?)</ESRB>', i, re.S).group(1) if re.search('<ESRB>(.*?)</ESRB>', i, re.S) else ''
        ReleaseYear=re.search('<ReleaseYear>(.*?)</ReleaseYear>', i, re.S).group(1) if re.search('<ReleaseYear>(.*?)</ReleaseYear>', i, re.S) else ''
        VideoURL=re.search('<VideoURL>(.*?)</VideoURL>', i, re.S).group(1) if re.search('<VideoURL>(.*?)</VideoURL>', i, re.S) else ''
        Cooperative=re.search('<Cooperative>(.*?)</Cooperative>', i, re.S).group(1) if re.search('<Cooperative>(.*?)</Cooperative>', i, re.S) else ''
        DOS=re.search('<DOS>(.*?)</DOS>', i, re.S).group(1) if re.search('<DOS>(.*?)</DOS>', i, re.S) else ''
        StartupFile=re.search('<StartupFile>(.*?)</StartupFile>', i, re.S).group(1) if re.search('<StartupFile>(.*?)</StartupFile>', i, re.S) else ''
        StartupParameters=re.search('<StartupParameters>(.*?)</StartupParameters>', i, re.S).group(1) if re.search('<StartupParameters>(.*?)</StartupParameters>', i, re.S) else ''
        StartupMD5=re.search('<StartupMD5>(.*?)</StartupMD5>', i, re.S).group(1) if re.search('<StartupMD5>(.*?)</StartupMD5>', i, re.S) else ''
        MaxPlayers=re.search('<MaxPlayers>(.*?)</MaxPlayers>', i, re.S).group(1) if re.search('<MaxPlayers>(.*?)</MaxPlayers>', i, re.S) else ''
        WikipediaURL=re.search('<WikipediaURL>(.*?)</WikipediaURL>', i, re.S).group(1) if re.search('<WikipediaURL>(.*?)</WikipediaURL>', i, re.S) else ''
        SetupFile=re.search('<SetupFile>(.*?)</SetupFile>', i, re.S).group(1) if re.search('<SetupFile>(.*?)</SetupFile>', i, re.S) else ''
        ReleaseType=re.search('<ReleaseType>(.*?)</ReleaseType>', i, re.S).group(1) if re.search('<ReleaseType>(.*?)</ReleaseType>', i, re.S) else ''
        Platform=re.search('<Platform>(.*?)</Platform>', i, re.S).group(1) if re.search('<Platform>(.*?)</Platform>', i, re.S) else ''
        Name=re.search('<Name>(.*?)</Name>', i, re.S).group(1) if re.search('<Name>(.*?)</Name>', i, re.S) else ''
        CommunityRating=re.search('<CommunityRating>(.*?)</CommunityRating>', i, re.S).group(1) if re.search('<CommunityRating>(.*?)</CommunityRating>', i, re.S) else ''
        Developer=re.search('<Developer>(.*?)</Developer>', i, re.S).group(1) if re.search('<Developer>(.*?)</Developer>', i, re.S) else ''
        SetupMD5=re.search('<SetupMD5>(.*?)</SetupMD5>', i, re.S).group(1) if re.search('<SetupMD5>(.*?)</SetupMD5>', i, re.S) else ''
        tags.append([
            Overview,
            CommunityRatingCount,
            Publisher,
            Genres,
            ReleaseDate,
            DatabaseID,
            ESRB,
            ReleaseYear,
            VideoURL,
            Cooperative,
            DOS,
            StartupFile,
            StartupParameters,
            StartupMD5,
            MaxPlayers,
            WikipediaURL,
            SetupFile,
            ReleaseType,
            Platform,
            Name,
            CommunityRating,
            Developer,
            SetupMD5,
        ])

    # f = open('a.txt','w+', encoding='utf-8', errors='ignore')
    # for j in tags:
    #     f.write('\t'.join("\""+x.strip().replace("\u2022","").replace('\t','').replace('\n','')+"\"" for x in j)+'\n')
    # f.close()
    append_data_xlsx(tags)
