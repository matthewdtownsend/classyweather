import sys
import urllib
import urlparse
import time
import re
import requests
from lxml import etree
from bs4 import BeautifulSoup

# Determine whether we have a recently fetched version of an XML file on server 
# and fetch it, if not. Not sure if this caching layer is needed, yet.

class ecXML:
  def __init__(self, url):
    response = urllib.urlopen(url)
    self.xml = response.read()
    self.root = etree.fromstring(self.xml)

class ecStation:
  def __init__(self, site):
    index_url = "https://weather.gc.ca/forecast/canada/index_e.html?id=%s" % (site.province)
    response = requests.get(index_url)
    index_url_bs = BeautifulSoup(response.content, 'html.parser')
    try:
      self.weather_home = "https://weather.gc.ca" + index_url_bs.find("a", text = site.nameEn)['href']
      response = requests.get(self.weather_home)
      weather_home_bs = BeautifulSoup(response.content, 'html.parser')
      station_url = weather_home_bs.find("a", text = "Weather Radar")['href']
      url = urlparse.urlparse(station_url)
      params = urlparse.parse_qs(url.query)
      self.station_code = params['id'][0].upper()
    except:
      self.station_code = None



class ecRadarList:
  def __init__(self, type = "PRECIPET"):
    radar_url = "http://dd.weather.gc.ca/radar/%s/GIF/%s" % (type, self.weather_station)
    response = requests.get(radar_url)
    radar_list_page = BeautifulSoup(response.content, 'html.parser')
    radar_list = []
    for link in radar_list_page.find_all("a", {'href': re.compile(r'%s_%s_[A-Z][A-Z][A-Z][A-Z].gif' % (self.weather_station, type))}):
      radar_list.append("%s/%s" % (radar_url, link.attrs['href']))
    radar_list.sort(reverse=True)
    return radar_list