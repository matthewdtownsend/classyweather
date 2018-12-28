import sys
import urllib
import hashlib
import os
import time
from lxml import etree

# Determine whether we have a recently fetched version of an XML file on server 
# and fetch it, if not. Not sure if this caching layer is needed, yet.

class ecXML:
  def __init__(self, url):
    url_hash = hashlib.md5(url)
    self.file = "cache/" + url_hash.hexdigest() + ".xml"
    self.xml = False
    if os.path.isfile(self.file):
      self.read_xml_cache()
    if self.xml is False:
      response = urllib.urlopen(url)
      self.xml = response.read()
      self.write_xml_cache()
    self.root = etree.fromstring(self.xml)

  def read_xml_cache(self):
    mtime = os.path.getmtime(self.file)
    expiration_seconds = 1200
    if (time.time() - mtime) > 1200:
      os.remove(self.file)
      self.xml = False
    else:
      f = open(self.file,'r')
      self.xml = "".join(f.readlines())

  def write_xml_cache(self):
      f = open(self.file,"w+")
      f.write(self.xml)
      f.close()