#!/usr/bin/python

import os
import jinja2
from include.data_layer import *
from flask import Flask
import markup

# Setup Flask and Jinja2 variables
app = Flask(__name__)
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

# Definite Flask URLs
@app.route("/")
def city_weather():
  template = jinja_env.get_template("index.html")
  list = []
  for i in data.provinces:
    province = {'name': i, 'sites':[]} 
    for site in [x for x in data.sites if x.province == i]:
      province['sites'].append({"code": site.code, "nameEn": site.nameEn})
    list.append(province)
  return template.render(
    list = list
  )

@app.route("/site/<code>")
def site_page(code):
  # Find a site that matches this code
  site = next((x for x in data.sites if x.code == code), None)
  weather = site.weather['En']
  # Load weather data for this site. Data is not preloaded to avoid
  # downloading entire batch of Environment Canada data on first run.
  weather.load()
  template = jinja_env.get_template("site.html")
  return template.render(
    nameEn = site.nameEn,
    province = site.province,
    temp_c = weather.current('temperature'),
    temp_f = c_to_f(weather.current('temperature')),
    pressure = weather.current('pressure'),
    forecast = weather.forecast(),
    home = home(),
    url = site.weather['En'].xml_url,
    timetext = weather.timetext,
  )

def home():
  return "<a href='/'>Home</a>"
