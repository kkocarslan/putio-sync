import re
import urllib2
import json

tmdbApiKey = "4caf966c414d017dd8ec7fbaf338dd72"

def parseFileName(filename):
  data = {}
  try:
    filename_c = re.sub("[^\w\n]+|_+", " ", filename, flags=re.UNICODE)
    data["moviename"] = re.sub("(.*)\s*((?:19|20)[0-9]{2})\s+.*", "\\1", filename_c)
    data["movieyear"] = re.sub(".*\s*((?:19|20)[0-9]{2})\s+.*", "\\1", filename_c)
    if data["movieyear"] == filename_c: return False
    return data
  except Exception, e:
    print Exception, e
    return False

def queryMovie(moviename, movieyear):
  try:
    tmdbUrl = "https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s&year=%s" % (tmdbApiKey, urllib2.quote(moviename), movieyear)
    request = urllib2.Request(tmdbUrl, headers={"Accept" : "application/json"})
    response = urllib2.urlopen(request)
    jsonRes = json.load(response)
    if jsonRes["total_results"] > 0: return jsonRes
    else: return False
  except Exception, e:
    print Exception, e
    return False


def getMovieInfo(movieid):
  return False

def isAMovie(filename):
  try:
    parsedFileName = parseFileName(filename)
    queryRes = queryMovie(parsedFileName["moviename"], parsedFileName["movieyear"])
    if queryRes != False: return queryRes[0]
    else: return False
  except Exception, e:
    print Exception, e
    return False
    





