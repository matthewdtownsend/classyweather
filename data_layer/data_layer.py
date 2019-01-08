from ec_data_reader import ecSiteData, ecSiteList, ecStation, ecRadarList
import psycopg2
import json
import sys
import time
import io
import cPickle as pickle
from lxml import etree

# Bugfix: Frenchy names break the database functions in ASCII mode.

reload(sys)  
sys.setdefaultencoding('utf8')

# Database object - one object handle all database interactions.

class WeatherDB:

  # On load, ensure a config is installed, that the database can be reached, and that the database is setup.
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

    # Check to see if database_is_setup flag is set, and if not, run installation functions.
    try: 
      if self.variable_get('database_is_setup') is None:
        self.install_ecdata()
    except:
        self.install_ecdata()
    self.install_ecdata()

  # Installation functions

  def install_ecdata(self):
    self.configure_database()
    self.load_sitelist_xml()
    self.variable_set('database_is_setup',True)

  def configure_database(self):
    try:
      self.cur.execute("DROP TABLE IF EXISTS sites")
      self.cur.execute("DROP TABLE IF EXISTS provinces")
      self.cur.execute("DROP TABLE IF EXISTS weather")
      self.cur.execute("DROP TABLE IF EXISTS variables")
      self.cur.execute("""
        CREATE TABLE IF NOT EXISTS sites (
          id serial PRIMARY KEY,
          code varchar NOT NULL UNIQUE,
          nameEn varchar,
          nameFr varchar,
          province varchar,
          timezone varchar,
          weather_station varchar
        );
      """)
      self.cur.execute("""
        CREATE TABLE IF NOT EXISTS weather (
          id serial PRIMARY KEY,
          site_code varchar NOT NULL UNIQUE,
          xml varchar,
          timestamp varchar,
          timetext varchar
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
          name varchar NOT NULL UNIQUE,
          value varchar
        );
      """)
      self.conn.commit()
    except Exception, e:
      print("Can't create database table")
      print (str(e))
      sys.exit()

  # Site and site list functions

  def load_sitelist_xml(self):
    sitelist_xml = ecSiteList().root
    self.sites = {}
    self.provinces = {}
    for i in sitelist_xml.findall("site"):
      site_code = i.attrib['code']
      province = i.find("provinceCode").text
      nameEn = i.find("nameEn").text
      nameFr = i.find("nameFr").text
      self.add_site(site_code, province, nameEn, nameFr)
      self.add_province(province)

  def add_site(self, site_code, province, nameEn, nameFr):
    self.cur.execute("""INSERT INTO sites (code, province, nameEn, nameFr)
      VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""", (site_code, province, nameEn, nameFr))
    self.conn.commit()

  def get_site(self, code):
    self.cur.execute("SELECT code,nameEn,nameFr,weather_station, province, timezone from sites WHERE code = %s", (code,))
    record = self.cur.fetchone()
    return {
      'code': record[0],
      'nameEn': record[1],
      'nameFr': record[2],
      'weather_station': record[3],
      'province': record[4],
      'timezone': record[5]
    }

  # Provincial functions

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

  # Weather data functions

  def add_weather(self, site):
    siteData = ecSiteData(site)
    site.data_url = siteData.url
    f = io.BytesIO()
    pickle.dump(siteData.xml, f)
    self.cur.execute("""INSERT INTO weather (site_code, xml, timestamp, timetext)
      VALUES (%s, %s, %s, %s) ON CONFLICT (site_code) DO UPDATE
      SET xml = %s, timestamp = %s, timetext = %s""", 
      (site.code, f.getvalue(), time.time(), siteData.timetext, f.getvalue(), time.time(), siteData.timetext))
    self.conn.commit()
    self.cur.execute("""UPDATE sites SET timezone = %s WHERE code = %s""",
      (siteData.timezone, site.code))
    self.conn.commit()
    site.timezone = siteData.timezone
    return {
      'xml': f.getvalue(),
      'timestamp': time.time(),
      'timetext': siteData.timetext
    }

  def get_weather(self, site):
    self.cur.execute("SELECT xml, timestamp, timetext from weather WHERE site_code = %s", (site.code,))
    record = self.cur.fetchone()
    if record is None:
      result = self.add_weather(site)
    else:
      result = {
        'xml': record[0],
        'timestamp': record[1],
        'timetext': record[2]
      }
    diff = time.time() - float(result['timestamp'])
    if diff > 600:
      result = self.add_weather(site)
    f = io.BytesIO(result['xml'])
    xml = pickle.load(f)
    return {
      'xml': etree.fromstring(xml),
      'timestamp': result['timestamp'],
      'timetext': result['timetext']
    }

  # Weather station functions

  def set_weather_station(self, site):
    station = ecStation(site).station_code
    self.cur.execute("UPDATE sites SET weather_station = %s WHERE code = %s", (station,site.code))
    self.conn.commit()
    return station

  # Radar functions - currently a passthrough via ec_data_reader without database storage/caching

  def get_radar_list(self, station):
    radar_list = ecRadarList(station).radar_list
    if not radar_list:
      return False
    else:
      return radar_list

  # Stored variable functions

  def variable_get(self, var_name):
    self.cur.execute("SELECT value from variables WHERE name = %s", (var_name,))
    return self.cur.fetchone()[0]

  def variable_set(self, var_name, var_value):
    self.cur.execute("""INSERT INTO variables (name, value)
      VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET value = %s""", 
      (var_name, var_value, var_value))
    self.conn.commit()

  def variable_del(self, var_name):
    self.cur.execute("DELETE from variables WHERE name = %s", (var_name,))
    self.conn.commit()