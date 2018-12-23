#!/usr/bin/python

import os
import jinja2
from include.data_layer import *
from include.utilities import *
from flask import Flask, request, send_from_directory
import markup

ec_data = EnvironmentCanadaData()

# Setup Flask and Jinja2 variables
app = Flask(__name__)
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

# Definite Flask URLs
@app.route("/")
def city_weather():
  template = jinja_env.get_template("index.html")
  return template.render(
    site_list = ec_data.provinces
  )

@app.route("/site/<code>")
def site_page(code):
  # Find a site that matches this code
  site = ec_data.sites[code]
  # Load weather data for this site. Data is not preloaded to avoid
  # downloading entire batch of Environment Canada data on first run.
  template = jinja_env.get_template("site.html")
  return template.render(
    nameEn = site.nameEn,
    province = site.province,
    temp_c = site.current('temperature'),
    temp_f = c_to_f(site.current('temperature')),
    pressure = site.current('pressure'),
    forecast = site.forecast(),
    home = home(),
    url = site.data_url(),
    timetext = site.load_weather()[2],
  )

@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory('assets', path)

def home():
  return "<a href='/'>Home</a>"
