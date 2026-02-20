"""
Geohash Utility for Geophysical Caching
Implements a base32 geohash algorithm for location-based caching of climate data.
"""

import math
from typing import Tuple

BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
DECODE_MAP = {char: i for i, char in enumerate(BASE32)}

def encode(latitude: float, longitude: float, precision: int = 6) -> str:
    """
    Encode a latitude and longitude into a geohash string.
    
    Args:
        latitude: Latitude in degrees (-90 to 90)
        longitude: Longitude in degrees (-180 to 180)
        precision: Desired length of the geohash string
        
    Returns:
        Geohash string
    """
    lat_interval = (-90.0, 90.0)
    lon_interval = (-180.0, 180.0)
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True
    
    while len(geohash) < precision:
        if even:
            mid = (lon_interval[0] + lon_interval[1]) / 2
            if longitude > mid:
                ch |= bits[bit]
                lon_interval = (mid, lon_interval[1])
            else:
                lon_interval = (lon_interval[0], mid)
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if latitude > mid:
                ch |= bits[bit]
                lat_interval = (mid, lat_interval[1])
            else:
                lat_interval = (lat_interval[0], mid)
        
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(BASE32[ch])
            bit = 0
            ch = 0
            
    return "".join(geohash)

def decode(geohash: str) -> Tuple[float, float]:
    """
    Decode a geohash string into latitude and longitude.
    
    Args:
        geohash: Geohash string
        
    Returns:
        Tuple of (latitude, longitude) center point
    """
    lat_interval = (-90.0, 90.0)
    lon_interval = (-180.0, 180.0)
    even = True
    
    for char in geohash:
        cd = DECODE_MAP[char]
        for mask in [16, 8, 4, 2, 1]:
            if even:
                mid = (lon_interval[0] + lon_interval[1]) / 2
                if cd & mask:
                    lon_interval = (mid, lon_interval[1])
                else:
                    lon_interval = (lon_interval[0], mid)
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2
                if cd & mask:
                    lat_interval = (mid, lat_interval[1])
                else:
                    lat_interval = (lat_interval[0], mid)
            even = not even
            
    return (lat_interval[0] + lat_interval[1]) / 2, (lon_interval[0] + lon_interval[1]) / 2
