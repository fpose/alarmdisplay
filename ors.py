#!/usr/bin/python3

import urllib3
import json

headers = {
  'Accept': 'text/json; charset=utf-8'
}

http = urllib3.PoolManager()

url = 'https://api.openrouteservice.org/directions?' \
    'api_key=58d904a497c67e00015b45fc756c5baed3b94bf2a9cbfa35fb4e86ae&' \
    'coordinates=6.09806,51.76059|6.10695,51.78317&' \
    'profile=driving-car&' \
    'preference=&' \
    'units=&' \
    'language=de&' \
    'geometry=&' \
    'geometry_format=polyline&' \
    'geometry_simplify=&' \
    'instructions=false&' \
    'instructions_format=&' \
    'roundabout_exits=&' \
    'attributes=&' \
    'maneuvers=&' \
    'radiuses=&' \
    'bearings=&' \
    'continue_straight=&' \
    'elevation=&' \
    'extra_info=&' \
    'optimized=&' \
    'options=&' \
    'id='

print(url)

request = http.request('GET', url, headers = headers)

print(request.status)

print(request.data)

data = json.loads(request.data.decode('utf-8'))
print(json.dumps(data, sort_keys=True, indent = 4, separators = (',', ': ')))

print(data["routes"][0]["geometry"])
