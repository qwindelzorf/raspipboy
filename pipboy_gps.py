# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# GPS/position functions

import os
import time
import math
import urllib
import urllib2
import StringIO
import json
import config

if config.USE_GPS:
    # Load libraries used by GPS, if present:
    def loadGPS():
        try:
            global gps
            import gps
        except:
            # Deactivate GPS-related systems if load failed:
            print("GPS LIBRARY NOT FOUND!")
            config.USE_GPS = False
    loadGPS()


class GpsModuleClass:

    saveVersion = 1

    cacheFilename = ("%s/map_coords.txt" % (config.CACHEPATH))

    lat, lon = 0, 0
    locality = ""
    localityLat, localityLon = 0, 0

    @classmethod
    def cmdLinePrint(self, cmdLine, msg):
        '''Do rendered-commandline print if cmdLine object is available, otherwise do a plain print:'''
        if cmdLine == 0:
            print(msg)
        else:
            cmdLine.printText(msg)

    @classmethod
    def addressToLatLong(self, address):
        '''Return Lat/Lon value for a given address:'''
        urlParams = {
            'address': address,
            'sensor': 'false',
        }
        url = 'http://maps.google.com/maps/api/geocode/json?' + urllib.urlencode(urlParams)
        print(url)
        response = urllib2.urlopen(url)
        responseBody = response.read()

        body = StringIO.StringIO(responseBody)
        result = json.load(body)
        if 'status' not in result or result['status'] != 'OK':
            return None
        else:
            return result['results'][0]['geometry']['location']['lat'], result['results'][0]['geometry']['location']['lng']

    @classmethod
    def latLongToLocality(self, lat, lon):
        '''Return Locality for a given lat/lon value:'''
        urlParams = {
            'latlng': (str(lat) + "," + str(lon)),
            'sensor': 'false',
        }
        url = 'http://maps.google.com/maps/api/geocode/json?' + urllib.urlencode(urlParams)
        print("latLongToLocality:")
        print(url)
        response = urllib2.urlopen(url)
        responseBody = response.read()

        body = StringIO.StringIO(responseBody)
        result = json.load(body)
        if 'status' not in result or result['status'] != 'OK':
            return None
        else:
            addressComps = result['results'][0]['address_components']

            notLocality = True
            compNum = 0
            retVal = ""
            while notLocality and compNum < len(addressComps):
                addressComp = addressComps[compNum]
                retVal = addressComp['long_name']
                for compType in addressComp['types']:
                    if compType == 'locality':
                        notLocality = False
                compNum += 1
            return retVal

    def hasCoords(self):
        badCoords = (((self.lat == 0) or math.isnan(self.lat)))
        return not badCoords

    def getCoords(self, *args):
        cmdLine = 0
        if args:
            cmdLine = args[0]

        # Do initial GPS-fix:
        self.cmdLinePrint(cmdLine, ">GPSD.LOCATE")
        self.cmdLinePrint(cmdLine, "Acquiring GPS Fix...")

        if config.USE_GPS:
            # Play sound until we have a GPS location locked:
            if (config.USE_SOUND) and (cmdLine != 0):
                # downloadSound = config.SOUNDS["static"]
                downloadSound = config.SOUNDS["beacon"]
                # config.SOUNDS["static"].play(loops=-1)
                downloadSound.play(loops=-1)

            # Initialise GPS module:
            session = gps.gps(host="localhost", port="2947")
            session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

            time.sleep(1)

            # Don't use GPS if no devices were found:
            if len(session.devices) == 0:
                config.USE_GPS = False
                print("GPS MODULE NOT FOUND!")

            if config.USE_GPS:
                try:
                    while (self.lat == 0) and (self.lat == 0):
                        session.next()
                        self.lat = session.fix.latitude
                        self.lon = session.fix.longitude
                        self.cmdLinePrint(cmdLine, "\t(%s,%s)" % (str(self.lat), str(self.lon)))
                except StopIteration:
                    self.cmdLinePrint(cmdLine, "GPSD has terminated")
                    config.USE_GPS = False

            del session

            if (config.USE_SOUND) and (cmdLine != 0):
                downloadSound.stop()

        newCoords = True

        if not self.hasCoords():
            # If GPS-fix wasn't available, load it from cached coords:
            if os.path.exists(self.cacheFilename):
                self.cmdLinePrint(cmdLine, ">GPSD.LOADCACHE %s" % (config.defaultPlace))
                self.cmdLinePrint(cmdLine, "Getting cached coords from %s..." % (self.cacheFilename))
                with open(self.cacheFilename, 'r') as f:
                    savedVersion = eval(f.readline())

                    # Only use coordinates-cache file if its version matches current version:
                    if savedVersion == self.saveVersion:
                        self.lat = eval(f.readline())
                        self.lon = eval(f.readline())
                        self.locality = (f.readline()).rstrip()
                        self.localityLat = eval(f.readline())
                        self.localityLon = eval(f.readline())
                        self.cmdLinePrint(cmdLine, "\t(%s,%s)" % (str(self.lat), str(self.lon)))
                        newCoords = False
                    else:
                        self.cmdLinePrint("\tInvalid cache-version, ignoring file")

            # If cache wasn't available, generate coords from defaultPlace:
            if newCoords:
                self.cmdLinePrint(cmdLine, ">GPSD.DEFAULTLOC %s" % (config.defaultPlace))
                self.cmdLinePrint(cmdLine, "Getting coords via geocode for Default Location %s..." % config.defaultPlace)

                self.lat, self.lon = self.addressToLatLong(config.defaultPlace)
                self.cmdLinePrint(cmdLine, "\t(%s,%s)" % (str(self.lat), str(self.lon)))

                self.locality = self.latLongToLocality(self.lat, self.lon)

                # Get map-centre coordinates for Locality:
                self.localityLat, self.localityLon = self.addressToLatLong(self.locality)

        # Get locality (i.e. city) for current coordinates via reverse-geocoding, if connection is available:
        self.cmdLinePrint(cmdLine, ">GPSD.LOCALITY")
        if not self.locality:
            self.locality = self.latLongToLocality(self.lat, self.lon)
            newCoords = True

        self.cmdLinePrint(cmdLine, "\tLocality: \"%s\"" % (self.locality))

        # Output new coordinates/locality to cache-file:
        if newCoords:
            self.cmdLinePrint(cmdLine, ">GPSD.SAVECACHE %s" % (self.cacheFilename))
            with open(self.cacheFilename, 'w') as out:
                out.write("%s\n%s\n%s\n%s\n%s\n%s\n" % (self.saveVersion,
                                                        repr(self.lat),
                                                        repr(self.lon),
                                                        self.locality,
                                                        repr(self.localityLat),
                                                        repr(self.localityLon)))

        return self.lat, self.lon
