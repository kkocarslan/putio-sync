import putio2
import os
import urllib2
from datetime import timedelta
import datetime
import signal
import sys
import fcntl
import downloadfile
from pprint import pprint
import argparse
import ConfigParser
import dbconn
import mailsender
from name_parser.parser import NameParser, InvalidNameException
import string
import fnmatch
import tvdb_api
import tmdb

#
# shares fix
#
os.setgid(1000)

#
# parse arguments
#
parser = argparse.ArgumentParser(description='Sync your put.io')
parser.add_argument('--bw-limit', '-l', help='bandwith limit. ie: 800k', default='800k')
args = parser.parse_args()
BW_LIMIT = args.bw_limit

#
# read ini file
#
try:
  config = ConfigParser.ConfigParser()
  config.read(os.path.dirname(os.path.realpath(__file__)) + "/config.ini")
  OAUTH_KEY = config.get('putiosync', 'OAUTH_KEY')
  PUTIO_SOURCEDIR = config.get('putiosync', 'PUTIO_SOURCEDIR')
  LOCAL_TARGETDIR = config.get('putiosync', 'LOCAL_TARGETDIR')
  TVSHOWS_BASEDIR = config.get('putiosync', 'TVSHOWS_BASEDIR')
  MOVIES_BASEDIR = config.get('putiosync', 'MOVIES_BASEDIR')
  REPORT_FROM = config.get('putiosync', 'REPORT_FROM')
  REPORT_TO   = config.get('putiosync', 'REPORT_TO')
  SMTP_HOST   = config.get('putiosync', 'SMTP_HOST')
  SMTP_USER   = config.get('putiosync', 'SMTP_USER')
  SMTP_PASS   = config.get('putiosync', 'SMTP_PASS')
except Exception, e:
  print "Error reading config.ini"
  print e
  sys.exit(1)

#
# prevent multiple sessions
#
lockfile = "/tmp/putiosynclockfile"
fp = open(lockfile, 'w')
try:
  fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
  print "Already running"
  sys.exit(1)

#
# initiate NameParser
#
np = NameParser(True)
tvdb = tvdb_api.Tvdb()


#
# catch ctrl+c properly
#
def signal_handler(signal, frame):
  print "\n\n\n\nYou pressed Ctrl+C!"
  sys.exit(0)

#
# get id for the sourcedir
#
def getSourceDirId():
  try:
    dirs = client.request("/files/search/\"" + PUTIO_SOURCEDIR + "\" from:me type:directory/page/-1")["files"]
    dirs = filter(lambda x: x["name"] == PUTIO_SOURCEDIR, dirs)
    dirs = filter(lambda x: x["parent_id"] == 0, dirs)
    sourceid = dirs[0]['id']
    if not sourceid > 0:
      print "Unable to get source dir id"
      sys.exit(1)
    else:
      return sourceid
  except Exception, e:
    print "Unable to get source dir id:", e
    sys.exit(1)

def checkIfDownloaded(fileId):
  return dbconn.checkFileId(fileId)

def markAsDownloaded(fileId):
  return dbconn.insertFileId(fileId)

#
# parse tv show name
#
def parseTvShowName(filename):
  res = {}
  try:
    parsed = np.parse(filename)
    series_name = string.capwords(parsed.series_name.lower())
    show = tvdb[series_name]
    res["series_name"] = show.data["seriesname"]
    res["season_number"] = "%02d" % (parsed.season_number,)
    return res 
  except:
    return False

def isThereUnfinishedDownloads(cdir):
  try:
    matches = []
    for root, dirnames, filenames in os.walk(cdir):
      for filename in fnmatch.filter(filenames, '*.part'):
        return True
    return False
  except:
    return True


def syncFiles(parent_id, target_base_folder):
  rfiles = client.request("/files/list?parent_id=" + str(parent_id))["files"]
  for rfile in rfiles:
    rfile["name"] = rfile["name"].replace(":", " ")
    if rfile["content_type"] == "application/x-directory":
      syncFiles(rfile["id"], target_base_folder + "/" + rfile["name"])
    else:
      infoLine = ("\n"
                 "\nTarget.......: " + target_base_folder + "/" + rfile["name"] + ""
                 "\nFilesize.....: " + str(rfile["size"]) + ""
                 "\nCRC32........: " + rfile["crc32"] + ""
                 "\nContent-Type.: " + rfile["content_type"] + "")
      print infoLine
      if checkIfDownloaded(str(rfile["id"])):
        print "Status.......: Already downloaded" 
      else:
        print "Status.......: Starting/continuing to download" 
        if not os.path.isdir(target_base_folder):
          os.mkdir(target_base_folder)
        downloadUrl = client.request("/files/" + str(rfile["id"]) + "/download", return_url=True)
        print downloadUrl
        if downloadfile.downloadfile(downloadUrl, rfile["name"], target_base_folder, rfile["size"], BW_LIMIT):
          if os.path.getsize(target_base_folder + "/" + rfile["name"]) >= rfile["size"]:
            markAsDownloaded(str(rfile["id"]) + "\n")
            subj = "[PutioSync] Download complete: " + rfile["name"]
            mailsender.sendMail(REPORT_FROM, REPORT_TO, SMTP_HOST, SMTP_USER, SMTP_PASS, subj, infoLine)

    # !!!!!!!
    # before doing actual work
    # make sure file is downloaded, and directory is created
    #
    #print "======> " + str(parent_id) + ":" + str(sourceDirId)
    if str(parent_id) == str(sourceDirId):
      #
      # continue if path is moved before or not exists at all
      #
      if not os.path.exists(target_base_folder + "/" + rfile["name"]):
        print "Move State...: Already moved to library"
        continue
      #
      # continue if it is a directory and there are .part files in it
      #
      if os.path.isdir(target_base_folder + "/" + rfile["name"]):
        if isThereUnfinishedDownloads(target_base_folder + "/" + rfile["name"]):
          print "Move State...: Unfinised files exists"
          continue

      #
      # mv finished downloads to library (assumption is: if not a tvshow, then it should be a movie)
      #
      tvshow = parseTvShowName(rfile["name"])
      if tvshow != False:
        print "Series Name....: " + tvshow["series_name"]
        fileTargetFolder = TVSHOWS_BASEDIR + "/" + tvshow["series_name"] + "/" + str(tvshow["season_number"])
        print "Moving State...: To " + fileTargetFolder
        print "==>> mv \"" + target_base_folder + "/" + rfile["name"] + "\" \"" + fileTargetFolder + "/" + rfile["name"] + "\""
        if not os.path.isdir(fileTargetFolder): os.makedirs(fileTargetFolder)
        os.renames(target_base_folder + "/" + rfile["name"], fileTargetFolder + "/" + rfile["name"])
        continue
      movie = tmdb.isAMovie(rfile["name"])
      if movie != False:
        fileTargetFolder = MOVIES_BASEDIR
        print "Movie Name.....: " + movie["title"]
        print "Moving State...: To " + fileTargetFolder
        print "==>> mv \"" + target_base_folder + "/" + rfile["name"] + "\" \"" + fileTargetFolder + "/" + rfile["name"] + "\""
        if not os.path.isdir(fileTargetFolder): os.makedirs(fileTargetFolder)
        os.renames(target_base_folder + "/" + rfile["name"], fileTargetFolder + "/" + rfile["name"])




if __name__=="__main__": 
  signal.signal(signal.SIGINT, signal_handler)
  client = putio2.Client(OAUTH_KEY)
  sourceDirId = getSourceDirId()
  syncFiles(sourceDirId, LOCAL_TARGETDIR)
