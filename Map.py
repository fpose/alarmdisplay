#-----------------------------------------------------------------------------
#
# Map helper functions
#
# Copyright (C) 2018 Florian Pose
#
# This file is part of Alarm Display.
#
# Alarm Display is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alarm Display is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Alarm Display. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------------

import os
import time
import math
import numpy as np

from PyQt5.QtGui import QPixmap, QPainter, QPolygonF, QPen, QColor
from PyQt5.QtCore import QPoint, QRect, QSize

import urllib3
import json

from Projection import MercatorProjection

#-----------------------------------------------------------------------------

tileDim = 256

#-----------------------------------------------------------------------------

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + \
                    (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

#-----------------------------------------------------------------------------

def num2deg(xtile, ytile, zoom):
    """
    http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    This returns the NW-corner of the square.
    Use the function with xtile+1 and/or ytile+1 to get the other corners.
    With xtile+0.5 & ytile+0.5 it will return the center of the tile.
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

#-----------------------------------------------------------------------------

def meters_per_pixel(zoom, lat_deg):
    r = 6372798.2
    C = 2 * math.pi * r
    lat_rad = math.radians(lat_deg)
    #return C * math.cos(lat_rad) / (2 ** (zoom + 8))
    return C / (2 ** (zoom + 8)) #equator

#-----------------------------------------------------------------------------

def getTargetPixmap(lat_deg, lon_deg, width, height, route, config, logger):

    zoom = config.getint("destination_map", "zoom", fallback = 17)

    x, y = deg2num(lat_deg, lon_deg, zoom)
    tile_lat_deg, tile_lon_deg = num2deg(x, y, zoom)
    next_tile_lat_deg, next_tile_lon_deg = num2deg(x + 1, y + 1, zoom)

    proj = MercatorProjection(tile_lon_deg, next_tile_lat_deg,
            next_tile_lon_deg, tile_lat_deg)
    coord = proj(lon_deg, lat_deg)
    mpp = meters_per_pixel(zoom, lat_deg)
    px = np.array(coord) / mpp

    center = QPoint(width / 2, height / 2)
    offset = QPoint(px[0], tileDim - px[1])
    centerTilePoint = center - offset

    xd = math.ceil(centerTilePoint.x() / tileDim)
    if xd < 0:
        xd = 0
    minX = x - xd

    yd = math.ceil(centerTilePoint.y() / tileDim)
    if yd < 0:
        yd = 0
    minY = y - yd

    originX = centerTilePoint.x() - xd * tileDim
    originY = centerTilePoint.y() - yd * tileDim

    numX = math.ceil((width - originX) / tileDim)
    numY = math.ceil((height - originY) / tileDim)
    totHeight = numY * tileDim

    lllat, lllon = num2deg(minX, minY + numY, zoom)
    urlat, urlon = num2deg(minX + numX, minY, zoom)
    totProj = MercatorProjection(lllon, lllat, urlon, urlat)

    pixmap = QPixmap(width, height)
    pixmap.fill() # white
    painter = QPainter()
    painter.begin(pixmap)

    for i in range(0, numX):
        for j in range(0, numY):
            tile = getTile(minX + i, minY + j, zoom, config, logger)
            xp = originX + i * tileDim
            yp = originY + j * tileDim
            painter.drawPixmap(xp, yp, tile)
            #painter.drawRect(xp, yp, tileDim, tileDim)

    poly = QPolygonF()
    for point in route:
        coord = totProj(point[0], point[1])
        px = np.array(coord) / mpp
        pos = QPoint(originX + px[0], originY + totHeight - px[1])
        poly.append(pos)
    pen = QPen()
    pen.setWidth(config.getint("destination_map", "route_width",
        fallback = 7))
    pen.setColor(QColor(config.get("maps", "route_color",
        fallback = "#400000c0")))
    painter.setPen(pen)
    painter.drawPolyline(poly)

    marker = QPixmap()
    imageDir = config.get("display", "image_dir", fallback = "images")
    marker.load(os.path.join(imageDir, config.get("maps",
        "destination_marker", fallback = "marker1.png")))
    markerOffset = QPoint(marker.width() / 2, marker.height())
    painter.drawPixmap(center - markerOffset, marker)
    painter.end()

    return pixmap

#-----------------------------------------------------------------------------

def getRoutePixmap(dest_lat_deg, dest_lon_deg, width, height, route, config,
        logger):

    # Home / Start point
    home_lon_deg = config.getfloat("route", "home_longitude",
            fallback = 6.09806)
    home_lat_deg = config.getfloat("route", "home_latitude",
            fallback = 51.76059)

    # mean shall be center
    lat_deg = (home_lat_deg + dest_lat_deg) / 2
    lon_deg = (home_lon_deg + dest_lon_deg) / 2
    lat_cos = math.cos(math.radians(lat_deg))

    marginFactor = 1.3
    min_lon_deg = min(home_lon_deg, dest_lon_deg)
    max_lon_deg = max(home_lon_deg, dest_lon_deg)
    lon_diff = (max_lon_deg - min_lon_deg) * marginFactor

    min_lat_deg = min(home_lat_deg, dest_lat_deg)
    max_lat_deg = max(home_lat_deg, dest_lat_deg)
    lat_diff = (max_lat_deg - min_lat_deg) * marginFactor / lat_cos

    min_x_tiles = math.ceil(width / tileDim) + 1
    min_y_tiles = math.ceil(height / tileDim) + 1

    # n = 2 ** z
    # M = al / 360 * 2 ** z
    # 2 ** z = M * 360 / al
    # z = log2(M * 360 / al)

    zoom_x = math.log(min_x_tiles * 360.0 / lon_diff, 2.0)
    zoom_y = math.log(min_y_tiles * 360.0 / lat_diff, 2.0)
    zoom = round(min(zoom_x, zoom_y)) - 1
    logger.debug('Zoom: %f x %f => %u', zoom_x, zoom_y, zoom)
    mpp = meters_per_pixel(zoom, lat_deg)

    x, y = deg2num(lat_deg, lon_deg, zoom)
    tile_lat_deg, tile_lon_deg = num2deg(x, y, zoom)
    next_tile_lat_deg, next_tile_lon_deg = num2deg(x + 1, y + 1, zoom)

    proj = MercatorProjection(tile_lon_deg, next_tile_lat_deg,
            next_tile_lon_deg, tile_lat_deg)
    coord = proj(lon_deg, lat_deg)
    px = np.array(coord) / mpp

    center = QPoint(width / 2, height / 2)
    offset = QPoint(px[0], tileDim - px[1])
    centerTilePoint = center - offset

    xd = math.ceil(centerTilePoint.x() / tileDim)
    if xd < 0:
        xd = 0
    minX = x - xd

    yd = math.ceil(centerTilePoint.y() / tileDim)
    if yd < 0:
        yd = 0
    minY = y - yd

    originX = centerTilePoint.x() - xd * tileDim
    originY = centerTilePoint.y() - yd * tileDim

    numX = math.ceil((width - originX) / tileDim)
    numY = math.ceil((height - originY) / tileDim)
    totHeight = numY * tileDim

    lllat, lllon = num2deg(minX, minY + numY, zoom)
    urlat, urlon = num2deg(minX + numX, minY, zoom)
    totProj = MercatorProjection(lllon, lllat, urlon, urlat)

    pixmap = QPixmap(width, height)
    pixmap.fill() # white
    painter = QPainter()
    painter.begin(pixmap)

    for i in range(0, numX):
        for j in range(0, numY):
            tile = getTile(minX + i, minY + j, zoom, config, logger)
            xp = originX + i * tileDim
            yp = originY + j * tileDim
            painter.drawPixmap(xp, yp, tile)
            #painter.drawRect(xp, yp, tileDim, tileDim)

    poly = QPolygonF()
    for point in route:
        coord = totProj(point[0], point[1])
        px = np.array(coord) / mpp
        pos = QPoint(originX + px[0], originY + totHeight - px[1])
        poly.append(pos)
    pen = QPen()
    pen.setWidth(config.getint("route_map", "route_width", fallback = 5))
    pen.setColor(QColor(config.get("maps", "route_color",
        fallback = "#400000c0")))
    painter.setPen(pen)
    painter.drawPolyline(poly)

    markerRects = []

    marker = QPixmap()

    imageDir = config.get("display", "image_dir", fallback = "images")

    marker.load(os.path.join(imageDir, config.get("maps", "home_marker",
        fallback = "marker_home.png")))
    markerOffset = QPoint(marker.width() / 2, marker.height())
    coord = totProj(home_lon_deg, home_lat_deg)
    px = np.array(coord) / mpp
    pos = QPoint(originX + px[0], originY + totHeight - px[1])
    markerPos = pos - markerOffset
    painter.drawPixmap(markerPos, marker)
    markerRect = QRect(markerPos, marker.size())
    markerRects.append(markerRect)

    marker.load(os.path.join(imageDir, config.get("maps",
        "destination_marker", fallback = "marker1.png")))
    markerOffset = QPoint(marker.width() / 2, marker.height())
    coord = totProj(dest_lon_deg, dest_lat_deg)
    px = np.array(coord) / mpp
    pos = QPoint(originX + px[0], originY + totHeight - px[1])
    markerPos = pos - markerOffset
    painter.drawPixmap(markerPos, marker)
    markerRect = QRect(markerPos, marker.size())
    markerRects.append(markerRect)

    painter.end()

    return pixmap, markerRects

#-----------------------------------------------------------------------------

def getTile(x, y, zoom, config, logger):
    tilesDir = config.get("maps", "tiles_dir", fallback = "tiles")
    path = os.path.join(tilesDir, str(zoom), str(x), str(y) + '.png')
    #logger.debug("Opening %s", path)
    tile = QPixmap()
    try:
        tile.load(path)
    except:
        logger.debug("Couldn't open image %s", path)
    return tile

#-----------------------------------------------------------------------------

def getRoute(dest_lat_deg, dest_lon_deg, config, logger):

    # Home / Start point
    home_lon_deg = config.getfloat("route", "home_longitude",
            fallback = 6.09806)
    home_lat_deg = config.getfloat("route", "home_latitude",
            fallback = 51.76059)
    api_key = config.get("route", "ors_api_key", fallback = "")

    headers = {
      'Accept': 'text/json; charset=utf-8'
    }

    http = urllib3.PoolManager()

    url = 'https://api.openrouteservice.org/directions?' \
        'api_key={4}&' \
        'coordinates={0},{1}|{2},{3}&' \
        'profile=driving-car&' \
        'geometry_format=polyline&' \
        'instructions=false&'.format(home_lon_deg, home_lat_deg, \
            dest_lon_deg, dest_lat_deg, api_key)

    try:
        request = http.request('GET', url, headers = headers, timeout = 5.0)
    except:
        logger.error('Route request failed.', exc_info = True)
        return ([], None, None)

    logger.debug('Received route response with status %u.', request.status)

    try:
        content = request.data.decode('utf-8')
    except:
        logger.error('Failed to decode route response data.', exc_info = True)
        return ([], None, None)

    try:
        data = json.loads(content)
    except:
        logger.error('Failed to load route JSON.', exc_info = True)
        return ([], None, None)

    #logger.debug(json.dumps(data, sort_keys=True, indent = 4,
    #    separators = (',', ': ')))

    try:
        route = data["routes"][0]["geometry"]
    except:
        logger.error('Route is empty.')
        route = []

    try:
        distance = float(data["routes"][0]["summary"]["distance"])
    except:
        logger.error('Distance is empty.')
        distance = None

    try:
        duration = float(data["routes"][0]["summary"]["duration"])
    except:
        logger.error('Duration is empty.')
        duration = None

    return (route, distance, duration)

#-----------------------------------------------------------------------------
