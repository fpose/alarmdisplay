
import math
import numpy as np
from mpl_toolkits.basemap import Basemap

from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QPoint, QRect, QSize

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + \
                    (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

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

def meters_per_pixel(zoom, lat_deg):
    r = 6372798.2
    C = 2 * math.pi * r
    lat_rad = math.radians(lat_deg)
    #return C * math.cos(lat_rad) / (2 ** (zoom + 8))
    return C / (2 ** (zoom + 8)) #equator

def getPixmap(lat_deg, lon_deg, zoom, width, height):

    pixmap = QPixmap(width, height)
    painter = QPainter()
    painter.begin(pixmap)

    tileDim = 256
    x, y = deg2num(lat_deg, lon_deg, zoom)
    tile_lat_deg, tile_lon_deg = num2deg(x, y, zoom)
    next_tile_lat_deg, next_tile_lon_deg = num2deg(x + 1, y + 1, zoom)

    m = Basemap(
        llcrnrlon = tile_lon_deg,
        llcrnrlat = next_tile_lat_deg,
        urcrnrlon = next_tile_lon_deg,
        urcrnrlat = tile_lat_deg,
        projection='merc'
    )

    proj = m(lon_deg, lat_deg)

    mpp = meters_per_pixel(zoom, lat_deg)
    px = np.array(proj) / mpp

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

    for i in range(0, numX):
        for j in range(0, numY):
            tile = getTile(minX + i, minY + j, zoom)
            xp = originX + i * tileDim
            yp = originY + j * tileDim
            painter.drawPixmap(xp, yp, tile)
            #painter.drawRect(xp, yp, tileDim, tileDim)

    marker = QPixmap()
    marker.load("images/marker1.png")
    markerOffset = QPoint(marker.width() / 2, marker.height())
    painter.drawPixmap(center - markerOffset, marker)
    painter.end()

    return pixmap

def getTile(x, y, zoom):
    tilePath = r"/home/fp/reichswalde/hydranten/tiles/{0}/{1}/{2}.png"
    path = tilePath.format(zoom, x, y)
    print("Opening: " + path)
    tile = QPixmap()
    try:
        tile.load(path)
    except:
        print("Couldn't open image")
    return tile
