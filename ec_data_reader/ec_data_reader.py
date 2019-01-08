import sys
import urllib
import urlparse
import time
import re
import requests
from lxml import etree
from bs4 import BeautifulSoup

# Note: the Canadian government suggests MSC Geomet for data, but right now we're getting this from HTTP.

# Fetch remote XML and parse into object

class ecSiteList:
  def __init__(self):
    url = 'http://dd.weather.gc.ca/citypage_weather/xml/siteList.xml'
    response = urllib.urlopen(url)
    self.xml = response.read()
    self.root = etree.fromstring(self.xml)
    self.url = url

class ecSiteData:
  def __init__(self, site, lang='En'):
    url = "http://dd.weather.gc.ca/citypage_weather/xml/%s/%s%s.xml" % (site.province, site.code, site.lang_suffix[lang])
    response = urllib.urlopen(url)
    self.xml = response.read()
    self.root = etree.fromstring(self.xml)
    self.url = url
    self.timetext =  self.root.xpath("dateTime[not(@zone = 'UTC')]/textSummary")[0].text
    self.timezone =  int(self.root.xpath("dateTime[not(@zone = 'UTC')]/@UTCOffset")[0])

# Determine the weather station associated with a city. This requires (so far as I can tell) checking the list
# of cities for a URL to an individual city page, and then checking that page for a radar link. None of this
# seems to be in XML.

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

# Get a list of most recent radar files for a given weather station. A directory listing is available.

class ecRadarList:
  def __init__(self, station, type = "PRECIPET"):
    radar_url = "http://dd.weather.gc.ca/radar/%s/GIF/%s" % (type, station)
    response = requests.get(radar_url)
    radar_list_page = BeautifulSoup(response.content, 'html.parser')
    self.radar_list = []
    for link in radar_list_page.find_all("a", {'href': re.compile(r'%s_%s_[A-Z][A-Z][A-Z][A-Z].gif' % (station, type))}):
      self.radar_list.append("%s/%s" % (radar_url, link.attrs['href']))
    self.radar_list.sort(reverse=True)