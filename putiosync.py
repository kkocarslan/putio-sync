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



def syncFiles(parent_id, target_base_folder):
  rfiles = client.request("/files/list?parent_id=" + str(parent_id))["files"]
  for rfile in rfiles:
    rfile["name"] = rfile["name"].replace(":", " ")
    if rfile["content_type"] == "application/x-directory":
      syncFiles(rfile["id"], target_base_folder + "/" + rfile["name"])
    else:
      infoLine = target_base_folder + "/" + rfile["name"] + " (filesize: " + str(rfile["size"]) +  ", crc32: " + rfile["crc32"] + ", Type: " + rfile["content_type"] + ")"
      if checkIfDownloaded(str(rfile["id"])):
        print "\nSkipping: " + infoLine 
        continue
      else:
        print "\nStarting: " + infoLine 
        if not os.path.isdir(target_base_folder):
          os.mkdir(target_base_folder)
      downloadUrl = client.request("/files/" + str(rfile["id"]) + "/download", return_url=True)
      print downloadUrl
      if downloadfile.downloadfile(downloadUrl, rfile["name"], target_base_folder, rfile["size"], BW_LIMIT):
        if os.path.getsize(target_base_folder + "/" + rfile["name"]) >= rfile["size"]:
          markAsDownloaded(str(rfile["id"]) + "\n")
          subj = "[PutioSync] Download complete: " + rfile["name"]
          msg = target_base_folder + "/" + rfile["name"] + "\n\n filesize: " + str(rfile["size"]) +  "\n crc32: " + rfile["crc32"] + "\n Type: " + rfile["content_type"] + ""
          mailsender.sendMail(REPORT_FROM, REPORT_TO, SMTP_HOST, SMTP_USER, SMTP_PASS, subj, msg)



if __name__=="__main__": 
  signal.signal(signal.SIGINT, signal_handler)
  client = putio2.Client(OAUTH_KEY)
  sourceDirId = getSourceDirId()
  syncFiles(sourceDirId, LOCAL_TARGETDIR)
