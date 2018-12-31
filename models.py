import collections
from bs4 import BeautifulSoup
import requests
from data_layer import WeatherDB
import sys
import re
from utilities import icon_url, c_to_f

ec_data = WeatherDB()

# Holds pertinent info for a weather site, with French and English instant-
# iations of Weather objects.

class Sites:
    def __init__(self):
        site_dict = {}
        provinces = ec_data.list_provinces()
        for province in provinces:
            site_dict[province[0]] = ec_data.list_sites_by_province(province)
        self.list = site_dict

class Site:
  def __init__(self,code):
    site_data = ec_data.get_site(code)
    self.base_url = "http://dd.weather.gc.ca/citypage_weather/xml"
    self.lang_suffix = {
      'En': '_e',
      'Fr': '_f' 
    }
    self.province = site_data['province']
    self.nameEn = site_data['nameEn']
    self.nameFr = site_data['nameFr']
    self.code = site_data['code']
    if site_data['weather_station'] is not None:
      self.weather_station = site_data['weather_station']
    else:
      self.weather_station = ec_data.set_weather_station(self)

  def load_weather(self, lang='En'):
    weather = ec_data.get_weather(self)
    if weather is None:
        weather = ec_data.add_weather(self)
    return (weather['xml'], weather['timestamp'], weather['timetext'])

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
  
  def radar(self):
    return Radar(self.weather_station)

  def __str__(self):
    return "Canada Environment site %s" % self.code

class CurrentConditions:
  def __init__(self, xml):
    self.temp_c = xml.xpath('currentConditions/temperature')[0].text
    self.temp_f = c_to_f(xml.xpath('currentConditions/temperature')[0].text)
    self.pressure = xml.xpath('currentConditions/pressure')[0].text
    self.icon = icon_url(xml.xpath("currentConditions/iconCode")[0].text)

class Forecast:
  def __init__(self, xml):
    self.name = xml.xpath("period")[0].text
    self.icon = icon_url(xml.xpath("abbreviatedForecast/iconCode")[0].text)
    self.textSummary = xml.xpath("textSummary")[0].text

class Radar:
  def __init__(self, station):
    self.station = station
    self.bg = "https://weather.gc.ca/cacheable/images/radar/layers/default_cities/%s_towns.gif" % (station.lower())
    self.precipet_list = self.radar_list()

  def radar_list(self, type = "PRECIPET"):
    radar_url = "http://dd.weather.gc.ca/radar/%s/GIF/%s" % (type, self.station)
    response = requests.get(radar_url)
    radar_list_page = BeautifulSoup(response.content, 'html.parser')
    radar_list = []
    for link in radar_list_page.find_all("a", {'href': re.compile(r'%s_%s_[A-Z][A-Z][A-Z][A-Z].gif' % (self.station, type))}):
      radar_list.append("%s/%s" % (radar_url, link.attrs['href']))
    radar_list.sort(reverse=True)
    return radar_list