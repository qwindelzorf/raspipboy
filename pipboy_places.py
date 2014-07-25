# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# Map Place management

import time
import urllib
import urllib2
import StringIO
import json
import config

# Google Places custom-search documentation:
#  https://developers.google.com/places/documentation/search

# Place-types are listed here:
#  https://developers.google.com/places/documentation/supported_types

placeTypeIconNames = {
    'accounting': 'office',
    'airport': 'military',
    'amusement_park': 'encampment',
    'aquarium': 'monument',
    'art_gallery': 'monument',
    'atm': 'vault',
    'bakery': 'factory',
    'bank': 'vault',
    'bar': 'ruins_urban',
    'beauty_salon': 'ruins_town',
    'bicycle_store': 'office',
    'book_store': 'ruins_urban',
    'bowling_alley': 'ruins_urban',
    'bus_station': 'metro',
    'cafe': 'ruins_urban',
    'campground': 'encampment',
    'car_dealer': 'office',
    'car_rental': 'office',
    'car_repair': 'factory',
    'car_wash': 'factory',
    'casino': 'vault',
    'cemetery': 'monument',
    'church': 'monument',
    'city_hall': 'monument',
    'clothing_store': 'ruins_urban',
    'convenience_store': 'ruins_urban',
    'courthouse': 'monument',
    'dentist': 'office',
    'department_store': 'city',
    'doctor': 'office',
    'electrician': 'ruins_town',
    'electronics_store': 'city',
    'embassy': 'monument',
    'finance': 'office',
    'fire_station': 'military',
    'florist': 'ruins_town',
    'food': 'settlement',
    'funeral_home': 'monument',
    'furniture_store': 'ruins_urban',
    'gas_station': 'settlement',
    'general_contractor': 'settlement',
    'grocery_or_supermarket': 'ruins_urban',
    'gym': 'ruins_urban',
    'hair_care': 'ruins_town',
    'hardware_store': 'ruins_town',
    'health': 'ruins_town',
    'hindu_temple': 'monument',
    'home_goods_store': 'ruins_urban',
    'hospital': 'monument',
    'insurance_agency': 'ruins_urban',
    'jewelry_store': 'ruins_urban',
    'laundry': 'ruins_town',
    'lawyer': 'ruins_urban',
    'library': 'monument',
    'liquor_store': 'ruins_town',
    'local_government_office': 'monument',
    'locksmith': 'ruins_town',
    'lodging': 'settlement',
    'meal_delivery': 'ruins_town',
    'meal_takeaway': 'settlement',
    'mosque': 'monument',
    'movie_rental': 'ruins_urban',
    'movie_theater': 'monument',
    'moving_company': 'ruins_town',
    'museum': 'monument',
    'night_club': 'cave',
    'painter': 'settlement',
    'park': 'natural_landmark',
    'parking': 'metro',
    'pet_store': 'ruins_urban',
    'pharmacy': 'ruins_town',
    'physiotherapist': 'office',
    'place_of_worship': 'monument',
    'plumber': 'ruins_town',
    'police': 'military',
    'post_office': 'office',
    'real_estate_agency': 'ruins_urban',
    'restaurant': 'settlement',
    'rv_park': 'encampment',
    'school': 'monument',
    'shoe_store': 'ruins_town',
    'shopping_mall': 'monument',
    'spa': 'cave',
    'stadium': 'encampment',
    'storage': 'factory',
    'store': 'office',
    'subway_station': 'metro',
    'synagogue': 'monument',
    'taxi_stand': 'metro',
    'train_station': 'metro',
    'travel_agency': 'ruins_urban',
    'university': 'monument',
    'veterinary_care': 'office',
    'zoo': 'monument',
    'DEFAULT': 'ruins_town',
}

def getPlaces(lat, lon, radius=2000, types='establishment'):
    '''Gets list of up to 60 establishments in area'''
    places = []

    # These search-arguments will show the initial results-page:
    pageArgs = "location=%s,%s&radius=%s&types=%s" % (lat, lon, radius, types)
    pageNum = 0
    while not pageArgs:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?%s&sensor=false&key=%s" % (pageArgs, config.gKey)
        pageArgs = None

        pageNum += 1
        # print("Page %s: %s" %(pageNum, url))

        response = urllib2.urlopen(url)
        responseBody = response.read()

        body = StringIO.StringIO(responseBody)
        result = json.load(body)

        if 'results' in result:
            # print("Page results: %s" %(len(result['results'])))
            for thisPlace in result['results']:
                placeLoc = thisPlace['geometry']['location']
                placeTypes = thisPlace['types']

                # Get icon for place:
                iconName = None
                for thisType in placeTypes:
                    if iconName is None:
                        if thisType in placeTypeIconNames:
                            iconName = placeTypeIconNames[thisType]
                # Set default if name wasn't found:
                if iconName is None:
                    iconName = placeTypeIconNames['DEFAULT']

                placeItem = {
                    'name': thisPlace['name'],
                    'lat': placeLoc['lat'],
                    'lon': placeLoc['lng'],
                    'icon': iconName,
                    # 'types':placeTypes
                }

                places.append(placeItem)
                print(placeItem)

        # Set loop to download next page - there'll be up to 3 pages, of up to 20 results each:
        if 'next_page_token' in result:
            # print("Next page...")
            # Set up argument to download next page:
            pageArgs = "pagetoken=%s" % (result['next_page_token'])

            # Pause, as Google delays enabling the next page:
            time.sleep(2)

    return places

# getPlaces(53.79420270000001,-1.5356686)
