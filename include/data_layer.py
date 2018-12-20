#!/usr/bin/python

from include.xml import *

# Data object, to emulate a database on top of Environment of Canada XML files.
# Treating all data as a child of Data object. Perhaps not helpful, as we don't
# strictly need to load the sitelist file into memory. However, validation of
# site URLs would need this list, so I see sense in loading it into memory no
# matter what. 
# Database layer to come later.

class Data:
  def __init__(self):
    sitelist_xml = get_xml('http://dd.weather.gc.ca/citypage_weather/xml/siteList.xml')
    self.sites = []
    self.provinces = set([])
    for i in sitelist_xml.findall("site"):
      # We need a list of provinces (for convenience), in addition to a list of
      # site objects.
      self.sites.append(self.Site(i))
      self.provinces.add(i.find('provinceCode').text)
    self.sites.sort(key=lambda x: x.nameEn)
    self.provinces = sorted(list(self.provinces))

  # Holds pertinent info for a weather site, with French and English instant-
  # iations of Weather objects.

  class Site:
    def __init__(self,data):
      self.province = data.find("provinceCode").text
      self.nameEn = data.find("nameEn").text
      self.nameFr = data.find("nameFr").text
      self.code = data.attrib['code']
      self.weather = {
        'En': self.Weather('http://dd.weather.gc.ca/citypage_weather/xml/'+self.province+'/'+self.code+'_e.xml'),
        'Fr': self.Weather('http://dd.weather.gc.ca/citypage_weather/xml/'+self.province+'/'+self.code+'_f.xml')
      }

    # Weather object, holding URL needed for on-demand loading of site data,
    # plus functions to query said data.

    class Weather:
      def __init__(self, xml_url):
        self.xml_url = xml_url
   
      def load(self):
        self.xml = get_xml(self.xml_url)
        self.timestamp =  self.xml.xpath("dateTime[not(@zone = 'UTC')]/timeStamp")[0].text
        self.timetext =  self.xml.xpath("dateTime[not(@zone = 'UTC')]/textSummary")[0].text

      def current(self, field):
        return self.xml.xpath('currentConditions/'+field)[0].text

      def forecast(self):
        count = 1
        forecast = []
        for i in self.xml.xpath('forecastGroup/forecast'):
          forecast.append(self.Forecast(i))
        return forecast

      def query(self, query):
        return self.xml.xpath(query)[0].text

      class Forecast:
        def __init__(self, data):
          self.name = data.xpath("period")[0].text
          self.textSummary = data.xpath("textSummary")[0].text

# No place for helper functions to live yet - haven't decided if I want tied
# to objects.

def c_to_f( c ):
  f = 1.8*float(c) + 32
  return str(round(f,1))

# Kickstart the data loading

global data        
data = Data()       
