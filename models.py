import collections
from data_layer import WeatherDB
import sys
import re
import time
import datetime
import pytz
from utilities import icon_url, c_to_f

ec_data = WeatherDB()
# ec_data.install_ecdata() # Uncomment this line to reinitialize the database.

# Object to generate site list

class SiteList:
    def __init__(self):
        site_dict = {}
        provinces = ec_data.list_provinces()
        for province in provinces:
            site_dict[province[0]] = ec_data.list_sites_by_province(province)
        self.list = site_dict

# Holds pertinent info for a weather site, with French and English instant-
# iations of Weather objects.

class Site:
  def __init__(self,code):
    site_data = ec_data.get_site(code)
    self.lang_suffix = {
      'En': '_e',
      'Fr': '_f' 
    }
    self.province = site_data['province']
    self.nameEn = site_data['nameEn']
    self.nameFr = site_data['nameFr']
    self.code = site_data['code']
    if site_data['timezone'] is not None:
      self.timezone = int(site_data['timezone'])
    if site_data['weather_station'] is not None:
      self.weather_station = site_data['weather_station']
    else:
      self.weather_station = ec_data.set_weather_station(self)

  def load_weather(self, lang='En'):
    weather = ec_data.get_weather(self)
    if weather is None:
        weather = ec_data.add_weather(self)
    return (weather['xml'], weather['timestamp'], weather['timetext'])

  def longterm_forecast(self):
    forecast = []
    xml, timestamp, timetext = self.load_weather()
    for i in xml.xpath('forecastGroup/forecast'):
      forecast.append(LongtermForecast(i))
    return forecast

  def hourly_forecast(self):
    hourly_forecast = []
    xml, timestamp, timetext = self.load_weather()
    for i in xml.xpath('hourlyForecastGroup/hourlyForecast'):
      hourly_forecast.append(HourlyForecast(i, self.timezone))
    return hourly_forecast

  def current_conditions(self):
    xml, timestamp, timetext = self.load_weather()
    return CurrentConditions(xml)

  def query(self, query):
    xml, timestamp, timetext = self.load_weather()
    return xml.xpath(query)[0].text
  
  def radar(self):
    if self.weather_station:
      return Radar(self.weather_station)

  def __str__(self):
    return "Canada Environment site %s" % self.code

# Objects for various weather data components

class CurrentConditions:
  def __init__(self, xml):
    if xml.xpath('currentConditions')[0]:
      self.temp_c = xml.xpath('currentConditions/temperature')[0].text
      self.temp_f = c_to_f(xml.xpath('currentConditions/temperature')[0].text)
      self.pressure = xml.xpath('currentConditions/pressure')[0].text
      self.icon = icon_url(xml.xpath("currentConditions/iconCode")[0].text)

class LongtermForecast:
  def __init__(self, xml):
    if xml.xpath("period"):
      self.name = xml.xpath("period")[0].text
    if xml.xpath("abbreviatedForecast/iconCode"):
      self.icon = icon_url(xml.xpath("abbreviatedForecast/iconCode")[0].text)
    if xml.xpath("textSummary"):
      self.textSummary = xml.xpath("textSummary")[0].text

class HourlyForecast:
  def __init__(self, xml, timezone):
    fixed_offset = pytz.FixedOffset(timezone * 60)
    forecast_date = pytz.utc.localize(datetime.datetime.strptime(xml.xpath("@dateTimeUTC")[0], '%Y%m%d%H%M'))
    self.time = "{:%I %p (%A, %B %d)}".format(forecast_date.astimezone(fixed_offset)).lstrip("0").replace(" 0", " ")
    self.condition = xml.xpath("condition")[0].text
    self.icon = icon_url(xml.xpath("iconCode")[0].text)
    self.temperature = xml.xpath("temperature")[0].text

class Radar:
  def __init__(self, station):
    self.station = station
    self.bg = "https://weather.gc.ca/cacheable/images/radar/layers/default_cities/%s_towns.gif" % (station.lower())
    self.precipet_list = self.radar_list()

  def radar_list(self, type = "PRECIPET"):
    return ec_data.get_radar_list(self.station)