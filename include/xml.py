#!/usr/bin/python

import psycopg2
import sys
import urllib
import hashlib
import os
import time
from lxml import etree

# Determine whether we have a recently fetched version of an XML file on server 
# and fetch it, if not. Not sure if this caching layer is needed, yet.

def get_xml( url ):
  hash = hashlib.md5(url)
  file = "cache/" + hash.hexdigest() + ".xml"
  xml = False
  if os.path.isfile(file):
    xml = read_xml_cache(file)
  if xml is False:
    response = urllib.urlopen(url)
    xml = response.read()
    write_xml_cache(file, xml)
  root = etree.fromstring(xml)
  return root

def read_xml_cache( file ):
  mtime = os.path.getmtime(file)
  expiration_seconds = 1200
  if (time.time() - mtime) > 1200:
    os.remove(file)
    return False
  else:
    f = open(file,'r')
    xml = "".join(f.readlines())
    return xml

def write_xml_cache( file, xml ):
    f = open(file,"w+")
    f.write(xml)
    f.close()
