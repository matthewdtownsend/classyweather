import collections
from xml_manager import ecXML
from bs4 import BeautifulSoup
import requests
import re
import psycopg2
import json
import sys

reload(sys)  
sys.setdefaultencoding('utf8')

# Database

class WeatherDB:
  def __init__(self):
    try:
      with open('config.json', 'r') as f:
        dbconfig = json.load(f)
        db = dbconfig['DATABASE']
        dbuser = dbconfig['USER']
        dbpass = dbconfig['PASSWORD']
        dbhost = dbconfig['HOST']
        dbport = dbconfig['PORT']

    except Exception, e:
      print(str(e))
      print("Fatal error. Cannot parse config file.")
      sys.exit()
      
    try:
      self.conn = psycopg2.connect(database = db, user = dbuser, password = dbpass, host = dbhost, port = dbport)
      self.cur = self.conn.cursor()
    except Exception, e:
      print(str(e))
      print("Unable to connect to the database")
      sys.exit()

    try:
      self.cur.execute("DROP TABLE sites")
      self.cur.execute("DROP TABLE provinces")
      self.cur.execute("DROP TABLE weather")
      self.cur.execute("""
        CREATE TABLE IF NOT EXISTS sites (
          id serial PRIMARY KEY,
          code varchar NOT NULL UNIQUE,
          nameEn varchar,
          nameFr varchar,
          province varchar,
          weather_station varchar
        );
      """)
      self.cur.execute("""
        CREATE TABLE IF NOT EXISTS weather (
          id serial PRIMARY KEY,
          site varchar NOT NULL UNIQUE,
          xml varchar,
          timestamp timestamp
        );
      """)
      self.cur.execute("""
        CREATE TABLE IF NOT EXISTS provinces (
          id serial PRIMARY KEY,
          code varchar NOT NULL UNIQUE,
          long_name varchar
        );
      """)
      self.cur.execute("""
        CREATE TABLE IF NOT EXISTS variables (
          id serial PRIMARY KEY,
          name varchar NOT NULL UNIQUE,
          value varchar
        );
      """)
      self.conn.commit()
    except Exception, e:
      print("Can't create database table")
      print (str(e))
      sys.exit()

  def init_xml(self):
    sitelist_xml = ecXML('http://dd.weather.gc.ca/citypage_weather/xml/siteList.xml').root
    self.sites = {}
    self.provinces = {}

    for i in sitelist_xml.findall("site"):
      # We need a list of provinces (for convenience), in addition to a list of
      # site objects.
      site_code = i.attrib['code']
      province = i.find("provinceCode").text
      nameEn = i.find("nameEn").text
      nameFr = i.find("nameFr").text
      self.add_site(site_code, province, nameEn, nameFr)
      self.add_province(province)
    # self.sites.sort(key=lambda x: x.nameEn)

  def select_all(self, table, fields='*'):
    self.cur.execute("SELECT %s from {}".format(table),fields)
    return cur.fetchall()

  def add_site(self, site_code, province, nameEn, nameFr):
    self.cur.execute("""INSERT INTO sites (code, province, nameEn, nameFr)
      VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""", (site_code, province, nameEn, nameFr))
    self.conn.commit()

  def add_province(self, province):
    self.cur.execute("INSERT INTO provinces (code) VALUES (%s) ON CONFLICT DO NOTHING", (province,))
    self.conn.commit()

  def list_provinces(self):
    self.cur.execute("SELECT code from provinces ORDER BY code ASC")
    return self.cur.fetchall()

  def list_sites_by_province(self, province):
    self.cur.execute("SELECT code,nameEn from sites WHERE province = %s ORDER BY nameEn", (province,))
    sites = []
    records = self.cur.fetchall()
    for record in records:
      sites.append({
        'code': record[0],
        'nameEn': record[1]
      })
    return sites

  def get_site(self, code):
    self.cur.execute("SELECT code,nameEn,nameFr,weather_station, province from sites WHERE code = %s", (code,))
    record = self.cur.fetchone()
    return {
      'code': record[0],
      'nameEn': record[1],
      'nameFr': record[2],
      'weather_station': record[3],
      'province': record[4]
    }