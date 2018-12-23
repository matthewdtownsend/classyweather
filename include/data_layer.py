#!/usr/bin/python

from include.xml import *
from include.utilities import *
import collections

# Holds pertinent info for a weather site, with French and English instant-
# iations of Weather objects.

class Site:
  def __init__(self,data):
    self.base_url = "http://dd.weather.gc.ca/citypage_weather/xml"
    self.lang_suffix = {
      'En': '_e',
      'Fr': '_f' 
    }
    self.province = data.find("provinceCode").text
    self.nameEn = data.find("nameEn").text
    self.nameFr = data.find("nameFr").text
    self.code = data.attrib['code']

  def load_weather(self, lang='En'):
    xml_url = self.data_url()
    xml = get_xml(xml_url)
    timestamp =  xml.xpath("dateTime[not(@zone = 'UTC')]/timeStamp")[0].text
    timetext =  xml.xpath("dateTime[not(@zone = 'UTC')]/textSummary")[0].text
    return (xml, timestamp, timetext)

  def data_url(self, lang='En'):
    return "%s/%s/%s%s.xml" % (self.base_url, self.province, self.code, self.lang_suffix[lang])

  def forecast(self):
    forecast = []
    xml, timestamp, timetext = self.load_weather()
    for i in xml.xpath('forecastGroup/forecast'):
      forecast.append(Forecast(i))
    return forecast

  def current_conditions(self):
    xml, timestamp, timetext = self.load_weather()
    return CurrentConditions(xml)

  def query(self, query):
    xml, timestamp, timetext = self.load_weather()
    return xml.xpath(query)[0].text

  def __str__(self):
    return "Canada Environment site %s" % self.code

class CurrentConditions:
  def __init__(self, xml):
    self.temp_c = xml.xpath('currentConditions/temperature')[0].text
    self.temp_f = c_to_f(xml.xpath('currentConditions/temperature')[0].text)
    self.pressure = xml.xpath('currentConditions/pressure')[0].text

class Forecast:
  def __init__(self, xml):
    self.name = xml.xpath("period")[0].text
    self.icon_code = icon_url(xml.xpath("abbreviatedForecast/iconCode")[0].text)
    self.textSummary = xml.xpath("textSummary")[0].text

# No place for helper functions to live yet - haven't decided if I want tied
# to objects.

# Data object, to emulate a database on top of Environment of Canada XML files.
# Treating all data as a child of Data object. Perhaps not helpful, as we don't
# strictly need to load the sitelist file into memory. However, validation of
# site URLs would need this list, so I see sense in loading it into memory no
# matter what. 
# Database layer to come later.

class EnvironmentCanadaData:
  def __init__(self):
    sitelist_xml = get_xml('http://dd.weather.gc.ca/citypage_weather/xml/siteList.xml')
    self.sites = {}
    self.provinces = {}

    for i in sitelist_xml.findall("site"):
      # We need a list of provinces (for convenience), in addition to a list of
      # site objects.
      site_object = Site(i)
      site_code = i.attrib['code']
      province = site_object.province
      self.sites[site_code] = site_object
      province_list = self.provinces.get(province, [])
      province_list.append(site_object)
      self.provinces[province] = province_list
    # self.sites.sort(key=lambda x: x.nameEn)

  def get_sites_by_name(self):
    site_names = {v.nameEn: v for k,v in self.sites}
    return site_names

def icon_url(icon_code):
  icon_base_url = "https://weather.gc.ca/weathericons"
  extension = "gif"
  return "%s/%s.%s" % (icon_base_url, icon_code, extension)