
import math

from PyQt5.QtGui import QPixmap, QPainter

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

def getPixmap(lat_deg, lon_deg, zoom, width, height):

    tilePath = r"/home/fp/reichswalde/hydranten/tiles/{0}/{1}/{2}.png"
    print(lat_deg, lon_deg)
    x, y = deg2num(lat_deg, lon_deg, zoom)
    print(x, y)
    lat, lon = num2deg(x, y, zoom)
    print(lat, lon)
    #xmax, ymin = deg2num(lat_deg + delta_lat, lon_deg + delta_lon, zoom)

    tiles_per_width = int(width / 256)
    xmin = int(x - tiles_per_width / 2.0)
    xmax = xmin + tiles_per_width
    print(x, width, tiles_per_width, xmin, xmax)

    tiles_per_height = int(height / 256)
    ymin = int(y - tiles_per_height / 2.0)
    ymax = ymin + tiles_per_height

    pixmap = QPixmap(width, height)

    painter = QPainter()
    painter.begin(pixmap)

    for xtile in range(xmin, xmax + 1):
        for ytile in range(ymin, ymax + 1):
            try:
                path = tilePath.format(zoom, xtile, ytile)
                print("Opening: " + path)
                tile = QPixmap()
                tile.load(path)
                x = (xtile - xmin) * 256
                y = (ytile - ymin) * 256
                painter.drawPixmap(x, y, tile)
                painter.drawRect(x, y, 256, 256)
            except:
                print("Couldn't open image")
                tile = None
    painter.end()

    return pixmap
