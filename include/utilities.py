#!/usr/bin/python

def c_to_f( c ):
  try:
    f = 1.8*float(c) + 32
    return str(round(f,1))
  except:
    return "No data"

# https://weather.gc.ca/weathericons/16.gif