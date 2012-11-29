"""
Module containing common geodetic formulas
"""

#!/usr/bin/env python

import math


def distance(origin, destination):
    """
    Source: http://www.platoscave.net/blog/2009/oct/5/calculate-distance-latitude-longitude-python/
    # Haversine formula example in Python
    # Author: Wayne Dyck
    """
    lon1, lat1 = origin[:2]
    lon2, lat2 = destination[:2]
    radius = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d


def bearing(pointA, pointB):
    """
    Calculate the compass bearing between two points.
    Source: https://gist.github.com/2005586

    :Parameters:
        - `pointA: The tuple representing the longitude/latitude for the
        first point. Latitude and longitude must be in decimal degrees
        - `pointB: The tuple representing the longitude/latitude for the
        second point. Latitude and longitude must be in decimal degrees

    :Returns:
        The bearing in degrees

    :Returns Type:
        float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[1])
    lat2 = math.radians(pointB[1])

    dlon = math.radians(pointB[0] - pointA[0])

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180 to + 180 which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


def get_point_at(origin, distance, azimuth):
    """
    Get point at given distance and azimuth from origin.

    :param origin:
        (lon, lat) tuple in degrees
    :param distance:
        distance in km
    :param azimuth:
        azimuth in degrees
    """
    lon1, lat1 = origin[:2]
    lon1, lat1 = math.radians(lon1), math.radians(lat1)
    azimuth = math.radians(azimuth)
    pi = math.pi

    earth_radius = 6371.
    b = distance / earth_radius
    a = math.acos(math.cos(b) * math.cos(pi/2-lat1) + math.sin(pi/2-lat1) * math.sin(b) * math.cos(azimuth))
    B = math.asin(math.sin(b) * math.sin(azimuth) / math.sin(a))
    lat2 = 90 - math.degrees(a)
    lon2 = math.degrees(lon1 + B)
    return (lon2, lat2)
