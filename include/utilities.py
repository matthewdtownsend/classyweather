#!/usr/bin/python

def c_to_f( c ):
  try:
    f = 1.8*float(c) + 32
    return str(round(f,1))
  except:
    return "No data"

def icon_url(icon_code):
  icon_base_url = "https://weather.gc.ca/weathericons"
  extension = "gif"
  return "%s/%s.%s" % (icon_base_url, icon_code, extension) 