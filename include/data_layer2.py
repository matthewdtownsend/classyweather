from include.xml import *

class Site(object):
    def __init__(self, data):
        self.base_url = "http://dd.weather.gc.ca/citypage_weather/xml"
        self.lang_suffix = {
            'En': '_e',
            'Fr': '_f' 
        }
        self.province = data.find("provinceCode").text
        self.nameEn = data.find("nameEn").text
        self.nameFr = data.find("nameFr").text
        self.code = data.attrib['code']

    def load(self, lang='En'):
        xml_url = "%s/%s.xml" % (self.base_url, self.lang_suffix[lang])
        xml = get_xml(xml_url)
        timestamp = xml.find("dateTime").find("timeStamp").text
        timetext = xml.find("dateTime").find("textSummary").text    
        return (xml, timestamp, timetext)

    def current(self, field):
        xml, timestamp, timetext = self.load()
        return xml.findall('currentConditions')[0]

    def query(self, container, field):
        xml, timestamp, timetext = self.load()
        return xml.find(container).find(field).text

    def __str__(self):
        return "Canada Environment site %s" % self.code


class CanadaEnvironment(object):
    def __init__(self):
        sitelist_xml = get_xml('http://dd.weather.gc.ca/citypage_weather/xml/siteList.xml')
        self.sites = {}
        self.provinces = {}

        for i in sitelist_xml.findall("site"):
            site_object = Site(i)
            site_code = i.attrib['code']
            self.sites[site_code] = site_object
            province_list = self.provinces.get(site_code, [])
            self.provinces[site_code] = province_list.append(site_object)

    def get_sites_by_name(self):
        site_names = {v.nameEn: v for k,v in self.sites}
        return site_names
