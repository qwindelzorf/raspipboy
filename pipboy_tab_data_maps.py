# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# Bits dealing with maps

import pygame
import os
import time
import datetime
import random
import math
import numpy
import urllib
from PIL import Image, ImageEnhance
from gdal2tiles import GlobalMercator
from pygame.locals import *
import config
import pipboy_places


class Mode_Map:

    mapType = 0
    places = []
    changed = True

    saveVersion = 1

    # User-view's zoom/position:
    viewZoom = 1.0
    viewPosX = 0.0
    viewPosY = 0.0

    cursorRadius = 32
    cursorPosX = 0.0
    cursorPosY = 0.0

    mapType = 0
    mapImage = 0
    mapSize = 640
    mapScale = 2

    cursorSize = 16
    markerSizeSm = 32
    markerSizeBg = 48
    halfMarkerSizeSm = (markerSizeSm / 2)
    halfMarkerSizeBg = (markerSizeBg / 2)

    # Used to implement mouse-acceleration:
    moveStartTick = 0
    lastMoveTick = 0

    mapImageSize = (mapSize * mapScale)

    def __init__(self, *args, **kwargs):
        self.parent = args[0]
        self.rootParent = self.parent.rootParent

        self.pageCanvas = pygame.Surface((config.WIDTH, config.HEIGHT))
        self.mapCanvas = pygame.Surface((config.WIDTH, config.HEIGHT * 0.91))
        self.canvasWidth = self.mapCanvas.get_width()
        self.canvasHeight = self.mapCanvas.get_height()

        self.mapType = args[1]

        # Generate cursor-box image:
        cursBoxSize = (2 * self.cursorRadius)
        thirdSize = (cursBoxSize / 3)
        self.cursorBox = pygame.Surface((cursBoxSize, cursBoxSize))
        self.cursorBox.fill((0, 0, 0))
        lnSize = 2
        pygame.draw.rect(self.cursorBox,
                         (255, 255, 255),
                         (self.cursorRadius-(lnSize/2), self.cursorRadius-(lnSize/2), lnSize, lnSize),
                         0)
        pygame.draw.lines(self.cursorBox,
                          (255, 255, 255),
                          False,
                          [(lnSize, thirdSize),
                           (lnSize, lnSize),
                           (thirdSize, lnSize)],
                          lnSize)
        pygame.draw.lines(self.cursorBox,
                          (255, 255, 255),
                          False,
                          [(cursBoxSize-thirdSize, lnSize),
                           (cursBoxSize-lnSize, lnSize),
                           (cursBoxSize-lnSize, thirdSize)],
                          lnSize)
        pygame.draw.lines(self.cursorBox,
                          (255, 255, 255),
                          False,
                          [(lnSize, cursBoxSize-thirdSize),
                           (lnSize, cursBoxSize-lnSize),
                           (thirdSize, cursBoxSize-lnSize)],
                          lnSize)
        pygame.draw.lines(self.cursorBox,
                          (255, 255, 255),
                          False,
                          [(cursBoxSize-thirdSize, cursBoxSize-lnSize),
                           (cursBoxSize-lnSize, cursBoxSize-lnSize),
                           (cursBoxSize-lnSize, cursBoxSize-thirdSize)],
                          lnSize)
        self.cursorBox = self.cursorBox.convert()
        self.resetCursorPos()

        if self.mapType == 0:
            # LOCAL MAP DATA:
            self.rootParent.localMapPage = self
            self.name = "Local Map"
            self.mapFilename = ("%s/map_local.jpg" %(config.CACHEPATH))
            self.dataFilename = ("%s/map_local.txt" %(config.CACHEPATH))
            self.mapArgs = "&maptype=satellite&style=feature:road|visibility:off"
            self.mapZoom = 18

            self.images = {
                "door":     pygame.image.load('images/mapmarkers/icon_local_door.png'),
            }

            self.places = [
                {'name': 'The Chandlers', 'icon': 'door', 'lat': 53.79434365352854, 'lon': -1.534639431799627},
                {'name': 'The Chandlers', 'icon': 'door', 'lat': 53.79440308538747, 'lon': -1.534735671499546},
                {'name': 'The Chandlers', 'icon': 'door', 'lat': 53.79425970871591, 'lon': -1.534675876957149},
                {'name': 'The Chandlers', 'icon': 'door', 'lat': 53.79425970871591, 'lon': -1.534675876957149},
                {'name': 'The Chandlers', 'icon': 'door', 'lat': 53.79427513360326, 'lon': -1.534645089591352},
            ]

        else:
            # WORLD MAP DATA:
            self.rootParent.worldMapPage = self
            self.name = "World Map"
            self.mapFilename = ("%s/map_world.jpg" % (config.CACHEPATH))
            self.dataFilename = ("%s/map_world.txt" % (config.CACHEPATH))
            self.mapArgs = "&maptype=hybrid&style=feature:road|element:geometry|color:0xDDDDDD&style=element:labels|visibility:off"
            self.mapZoom = 14

            # Load map-marker icons:
            self.images = {
                "door":             pygame.image.load('images/mapmarkers/icon_local_door.png'),
                "encampment":       pygame.image.load('images/mapmarkers/icon_map_encampment.png'),
                "military":         pygame.image.load('images/mapmarkers/icon_map_military.png'),
                "office":           pygame.image.load('images/mapmarkers/icon_map_office.png'),
                "urban":            pygame.image.load('images/mapmarkers/icon_map_ruins_urban.png'),
                "vault":            pygame.image.load('images/mapmarkers/icon_map_vault.png'),
                "cave":             pygame.image.load('images/mapmarkers/icon_map_cave.png'),
                "factory":          pygame.image.load('images/mapmarkers/icon_map_factory.png'),
                "monument":         pygame.image.load('images/mapmarkers/icon_map_monument.png'),
                "ruins_sewer":      pygame.image.load('images/mapmarkers/icon_map_ruins_sewer.png'),
                "settlement":       pygame.image.load('images/mapmarkers/icon_map_settlement.png'),
                "city":             pygame.image.load('images/mapmarkers/icon_map_city.png'),
                "metro":            pygame.image.load('images/mapmarkers/icon_map_metro.png'),
                "natural_landmark": pygame.image.load('images/mapmarkers/icon_map_natural_landmark.png'),
                "ruins_town":       pygame.image.load('images/mapmarkers/icon_map_ruins_town.png'),
                "ruins_urban":      pygame.image.load('images/mapmarkers/icon_map_ruins_urban.png'),
                "undiscovered":     pygame.image.load('images/mapmarkers/icon_map_undiscovered.png'),
            }

        # Scale images down to 32x32:
        self.imagesSm = {}
        for imgName in self.images:
            img = self.images[imgName]
            smImage = pygame.transform.scale(img, (self.markerSizeSm, self.markerSizeSm))
            self.imagesSm[imgName] = smImage.convert()
            bgImg = pygame.transform.scale(img, (self.markerSizeBg, self.markerSizeBg))
            self.images[imgName] = bgImg.convert()

        # Scale cursor down to 16x16
        self.mapCursor = pygame.image.load('images/cursor.png')
        self.mapCursor = pygame.transform.scale(self.mapCursor, (self.cursorSize, self.cursorSize))
        self.mapCursor = self.mapCursor.convert_alpha()

    def getMapBounds(self, lat, lon, zoom, mapSize):
        '''Get latitude/longitude boundaries for a given map-image:'''

        # Make instance of coordinates-converter:
        mercator = GlobalMercator()

        # Convert latitude/longitude to meters, and then to global-image pixel-coordinates:
        mx, my = mercator.LatLonToMeters(lat, lon)
        px, py = mercator.MetersToPixels(mx, my, zoom)

        # Find pixel coords for static-map's bounds:
        halfMapSize = mapSize / 2
        mapMinX = px - halfMapSize
        mapMaxX = px + halfMapSize
        mapMinY = py - halfMapSize
        mapMaxY = py + halfMapSize

        minmx, minmy = mercator.PixelsToMeters(mapMinX, mapMinY, zoom)
        maxmx, maxmy = mercator.PixelsToMeters(mapMaxX, mapMaxY, zoom)

        self.minLat, self.minLon = mercator.MetersToLatLon(minmx, minmy)
        self.maxLat, self.maxLon = mercator.MetersToLatLon(maxmx, maxmy)

        return self.minLat, self.minLon, self.maxLat, self.maxLon

    def setViewToCentre(self):
        '''Set default user-view position:'''
        self.viewPosX = (-0.5 * (self.mapImage.get_width()-config.WIDTH)) - 1
        self.viewPosY = (-0.5 * (self.mapImage.get_height()-config.HEIGHT)) - 1

    def setViewToCurPos(self):
        '''Set user-view to centre in on current location:'''
        # Get position on map:
        px = (self.rootParent.gpsModule.lon - self.minLon) * self.xPerLon
        py = self.mapImage.get_width() - ((self.rootParent.gpsModule.lat - self.minLat) * self.yPerLat)

        self.viewPosX = (0.5 * config.WIDTH) - px
        self.viewPosY = (0.5 * config.HEIGHT) - py

    def getMap(self, doDownload=config.USE_INTERNET):

        lat, lon = 0, 0

        if self.mapType == 0:
            lat = self.rootParent.gpsModule.lat
            lon = self.rootParent.gpsModule.lon
            self.mapLocation = ("%s,%s" % (str(lat), str(lon)))
        else:
            self.mapLocation = self.rootParent.gpsModule.locality
            lat = self.rootParent.gpsModule.localityLat
            lon = self.rootParent.gpsModule.localityLon

        # Load cached data, if found:
        if (not config.FORCE_DOWNLOAD) and (os.path.exists(self.dataFilename)) and (os.path.exists(self.mapFilename)):
            print("  Reading data: %s" % (self.dataFilename))
            with open(self.dataFilename, 'r') as f:
                savedVersion = eval(f.readline())
                savedMapLocation = (f.readline()).rstrip()

                # Only use coordinates-cache file if its version matches current version:
                if savedVersion == self.saveVersion:
                    if savedMapLocation == self.mapLocation:
                        print("  Map-file is up-to-date, no need to download")
                        self.minLat = eval(f.readline())
                        self.minLon = eval(f.readline())
                        self.maxLat = eval(f.readline())
                        self.maxLon = eval(f.readline())

                        self.places = []
                        for item in f.readlines():
                            self.places.append(eval(item))
                        # print "YAY!"
                        # print self.places

                        doDownload = False
                    True
                else:
                    print("  Invalid cache-version, ignoring file")

        if doDownload:
            print("DOWNLOADING:")
            mapUrl = "http://maps.googleapis.com/maps/api/staticmap?center=%s" % (self.mapLocation)
            mapUrl += ("&zoom=%s&scale=%s&size=%sx%s%s&sensor=true" % (str(self.mapZoom), str(self.mapScale), str(self.mapSize), str(self.mapSize), self.mapArgs))
            print(mapUrl)
            urllib.urlretrieve(mapUrl, self.mapFilename)

            if self.mapType == 1:
                # Download a set of places from Google for markers:
                self.places = pipboy_places.getPlaces(lat,lon)

            # Work out coordinates for map's corners:
            self.getMapBounds(lat, lon, self.mapZoom, self.mapSize)
            print("  Lat/Lon Min:(%s,%s) Max:(%s,%s)" % (self.minLat, self.minLon, self.maxLat, self.maxLon))
            print("  Writing to file: %s" % (self.dataFilename))
            with open(self.dataFilename, 'w') as f:
                f.write("%s\n" % (self.saveVersion))
                f.write("%s\n" % (self.mapLocation))
                f.write("%s\n%s\n%s\n%s\n" % (repr(self.minLat), repr(self.minLon), repr(self.maxLat), repr(self.maxLon)))

                for place in self.places:
                    f.write("%s\n" % (repr(place)))

            # Load downloaded image via PIL, and tweak contrast/brightness:
            im = Image.open(self.mapFilename)
            im = ImageEnhance.Contrast(im).enhance(1.5)
            im = ImageEnhance.Brightness(im).enhance(0.2)
            im = im.convert("RGB")

            # Convert PIL image to Pygame surface:
            self.mapImage = pygame.image.frombuffer(im.tostring(), im.size, "RGB")

            # Add lines to World Map:
            if self.mapType == 1:
                imageSize = self.mapImage.get_width()
                stepCount = 16
                stepSize = (imageSize / stepCount)
                lineWidth = 2
                gridPos = stepSize

                # Add large-pixel noise, on two levels of gridding:
                for n in [1, 2]:
                    mapArray = pygame.surfarray.pixels3d(self.mapImage)
                    noisePixSize = (stepSize * n)
                    noise_small = numpy.random.random((imageSize/noisePixSize, imageSize/noisePixSize)) * 0.6 + 0.5
                    noise_big = noise_small.repeat(noisePixSize, 0).repeat(noisePixSize, 1)
                    mapArray *= noise_big[:, :, numpy.newaxis]

                gridVal = 40
                gridColour = (gridVal, gridVal, gridVal)

                while gridPos < imageSize:
                    pygame.draw.lines(self.mapImage, gridColour, False, [(0, gridPos), (imageSize, gridPos)], lineWidth)
                    pygame.draw.lines(self.mapImage, gridColour, False, [(gridPos, 0), (gridPos, imageSize)], lineWidth)
                    gridPos += stepSize
                pygame.draw.rect(self.mapImage, (255, 255, 255), (0, 0, imageSize, imageSize), lineWidth)
                print("GRIDDED!")

            # Save processed image to cache-folder:
            pygame.image.save(self.mapImage, self.mapFilename)
        else:
            # Load pre-processed image:
            self.mapImage = pygame.image.load(self.mapFilename)

        # Work out values for quickly converting Lat/Lon to X/Y:
        self.xPerLon = (self.mapScale * self.mapSize)/(self.maxLon - self.minLon)
        self.yPerLat = (self.mapScale * self.mapSize)/(self.maxLat - self.minLat)
        print("xPerLon: %s  yPerLat:%s" % (self.xPerLon, self.yPerLat))

        self.setViewToCurPos()

    def drawCurrentPosToCanvas(self):
        '''Draw current-position marker:'''
        # Get position on map:
        px = (self.rootParent.gpsModule.lon - self.minLon) * self.xPerLon
        py = self.mapImageSize - ((self.rootParent.gpsModule.lat - self.minLat) * self.yPerLat)

        # Get position on screen:
        px += self.viewPosX
        py += self.viewPosY

        # Draw to map:
        self.mapCanvas.blit(self.mapCursor, (px, py))


    def drawMarkerToCanvas(self, placeItem):
        '''Draw a given marker to mapCanvas at specific latitude/longitude coordinates:'''

        # self.drawMarkerToCanvas (self.imagesSm[markerType], , )

        # Get position on map:
        px = (placeItem['lon'] - self.minLon) * self.xPerLon
        py = self.mapImage.get_width() - ((placeItem['lat'] - self.minLat) * self.yPerLat)

        # Get position on screen:
        px += self.viewPosX
        py += self.viewPosY

        # Is this inside the cursor-box?
        highlighted = (abs(px - self.cursorPosX) < self.cursorRadius) and (abs(py - self.cursorPosY) < self.cursorRadius)

        # Get appropriately-sized marker-icon/radius:
        markerType = placeItem['icon']
        if highlighted:
            markerImg, markerSize, halfMarkerSize = self.images[markerType], self.markerSizeBg, self.halfMarkerSizeBg
            self.cursorName = placeItem['name']
        else:
            markerImg, markerSize, halfMarkerSize = self.imagesSm[markerType], self.markerSizeSm, self.halfMarkerSizeSm

        px -= halfMarkerSize
        py -= halfMarkerSize

        # Draw marker if it is on-screen:
        if ((px+markerSize) >= 0) and (px <= config.WIDTH) and ((py+markerSize) >= 0) and (py <= config.HEIGHT):
            self.mapCanvas.blit(markerImg, (px, py), None, pygame.BLEND_RGB_ADD)

    def drawPage(self):

        pageChanged = self.changed
        self.changed = False

        if pageChanged:

            self.mapCanvas.fill((30, 30, 30))

            # Download map if required:
            if self.mapImage == 0:
                self.getMap()

            # Blit map-texture to canvas:
            self.mapCanvas.blit(self.mapImage, (self.viewPosX, self.viewPosY))

            # Draw current-position marker:
            self.drawCurrentPosToCanvas()

            # Set blank cursorName:
            self.cursorName = ""

            # Draw location-markers:
            for item in self.places:
                self.drawMarkerToCanvas(item)

            # Draw cursor-box:
            self.mapCanvas.blit(self.cursorBox, (self.cursorPosX-self.cursorRadius, self.cursorPosY-self.cursorRadius), None, pygame.BLEND_RGB_ADD)

            if self.cursorName != "":
                textImg = config.FONT_LRG.render(self.cursorName, True, config.DRAWCOLOUR, (0, 0, 0))
                textX = self.cursorPosX-(textImg.get_width() / 2)
                textY = self.cursorPosY+self.cursorRadius+(config.charHeight / 2)
                self.mapCanvas.blit(textImg, (textX, textY), None, pygame.BLEND_ADD)

            # Blit to page-canvas:
            self.pageCanvas.blit(self.mapCanvas, (0, 0))

        return self.pageCanvas, pageChanged

    def resetCursorPos(self):
        self.cursorPosX = (self.canvasWidth / 2)
        self.cursorPosY = (self.canvasHeight / 2)

    def resetPage(self):
        '''Called every time view is changed to this page:'''
        self.resetCursorPos()
        self.setViewToCurPos()

    def ctrlEvents(self, events):
        '''Consume events that have been passed to map-page:'''

        for event in events:
            if event == 'sel':

                self.setViewToCurPos()
                self.changed = True
            elif (type(event) is list):
                mx, my, mzoom = event[0], event[1], event[2]

                # Mouse acceleration feature:
                accelTime = 5000
                maxAccel = 400
                minAccel = 2

                currentTick = pygame.time.get_ticks()

                if (currentTick - self.lastMoveTick) > 500:
                    self.moveStartTick = currentTick

                moveTime = (currentTick - self.moveStartTick)
                if moveTime > accelTime:
                    moveTime = accelTime

                accelMult = minAccel + ((maxAccel - minAccel) * (moveTime / accelTime))
                self.lastMoveTick = currentTick
                # End mouse acceleration

                self.cursorPosX += (accelMult * mx)
                cursMinX, cursMaxX = (self.cursorPosX-self.cursorRadius), (self.cursorPosX+self.cursorRadius)
                if cursMinX < 0:
                    self.viewPosX -= (cursMinX)
                    self.cursorPosX = self.cursorRadius
                elif cursMaxX > self.canvasWidth:
                    self.viewPosX += (self.canvasWidth - cursMaxX)
                    self.cursorPosX = (self.canvasWidth - self.cursorRadius)

                self.cursorPosY += (accelMult * my)
                cursMinY, cursMaxY = (self.cursorPosY-self.cursorRadius), (self.cursorPosY+self.cursorRadius)
                if cursMinY < 0:
                    self.viewPosY -= (cursMinY)
                    self.cursorPosY = self.cursorRadius
                elif cursMaxY > self.canvasHeight:
                    self.viewPosY += (self.canvasHeight - cursMaxY)
                    self.cursorPosY = (self.canvasHeight - self.cursorRadius)

                self.changed = True
