'''
Created on Sep 5, 2017

@author: theo
'''
import requests
from django.conf import settings

class PostcodeException(Exception):
    def __init__(self,response):
        self.code = response.status_code
        self.error = response.json().get('error',response.text)

    def __str__(self):
        return self.error

def check_address(postcode,huisnummer):
    ''' check geldig adres '''
    response = requests.get(url='https://postcode-api.apiwise.nl/v2/addresses',
                            params={'postcode':postcode,'number': huisnummer},
                            headers={'X-Api-Key':settings.POSTCODE_API_KEY})
    # TODO: check toevoeging (letter)
    if response.status_code == 200:
        adrs = response.json()['_embedded']['addresses']
        return adrs
    else:
        raise PostcodeException(response)

def check_postcode(postcode):
    ''' check voor geldige postcode '''
    response = requests.get(url='https://postcode-api.apiwise.nl/v2/postcodes/'+postcode,
                            headers={'X-Api-Key':settings.POSTCODE_API_KEY})
    if response.status_code == 200:
        # OK
        return True
    elif response.status_code == 404:
        # Not found
        return False
    else:
        raise PostcodeException(response)

def get_address_lonlat(lon,lat):
    ''' haal adres gegevens op voor lonlat coordinaten '''
    url = 'https://api.postcode.nl/rest/addresses/latlon/{latitude}/{longitude}'.format(latitude=lat,longitude=lon)
    response = requests.get(url=url,headers={'X-Api-Key':settings.POSTCODE_API_KEY})
    if response.ok:
        data = response.json()
        return data
    else:
        raise PostcodeException(response)

def get_address_rd(x,y):
    ''' haal adres gegevens op voor RD coordinaten '''
    #url = 'https://api.postcode.nl/rest/addresses/rd/{rdX}/{rdY}'.format(rdX=x,rdY=y)
    url = 'https://postcode-api.apiwise.nl/v2/addresses/rd/{rdX}/{rdY}'.format(rdX=x,rdY=y)
    response = requests.get(url=url,headers={'X-Api-Key':settings.POSTCODE_API_KEY})
    if response.ok:
        data = response.json()
        return data
    else:
        raise PostcodeException(response)

def get_address_google(lon, lat):        
    ''' haal adres gegevens op met google maps geocoding api '''
    url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={key}'.format(lon=lon,lat=lat,key=settings.GOOGLE_MAPS_API_KEY2)
    #url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&location_type=ROOFTOP&key={key}'.format(lon=lon,lat=lat,key=settings.GOOGLE_MAPS_API_KEY2)
    response = requests.get(url=url)
    if response.ok:
        data = response.json()
        if data['status'] == 'OK':
            return data
    raise PostcodeException(response)
