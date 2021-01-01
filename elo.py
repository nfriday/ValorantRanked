import requests
import json
import re
import datetime
import yaml
import os

with open(os.path.dirname(__file__) + '\\config.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
    region = config['region']
    username = config['username']
    password = config['password']

session = requests.session()

# Set initial headers
headers = {
    'Content-type': 'application/json'
}

# Perform auth request to retrieve session cookies
uri = 'https://auth.riotgames.com/api/v1/authorization'
data = {
    'client_id': 'play-valorant-web-prod',
    'nonce': '1',
    'redirect_uri': 'https://beta.playvalorant.com/opt_in',
    'response_type': 'token id_token',
}
data_json = json.dumps(data)
response = session.post(uri, data=data_json, headers=headers)

# Login and set Authorization header
uri = 'https://auth.riotgames.com/api/v1/authorization'
data = {
    'type': 'auth',
    'username': username,
    'password': password
}
data_json = json.dumps(data)
response = session.put(uri, data=data_json, headers=headers)
pattern = re.compile('access_token=([a-zA-Z0-9.\-_]+)&.*id_token=([a-zA-Z0-9.\-_]+)&.*expires_in=(\d+)')
auth_data = pattern.findall(response.json()['response']['parameters']['uri'])[0]
headers['Authorization'] = 'Bearer ' + auth_data[0]

# Retrieve entitlements and set X-Riot-Entitlements-JWT header
uri = 'https://entitlements.auth.riotgames.com/api/token/v1'
response = session.post(uri, data={}, headers=headers)
headers['X-Riot-Entitlements-JWT'] = response.json()['entitlements_token']

# Retrieve user_id
uri = 'https://auth.riotgames.com/userinfo'
response = session.get(uri, headers=headers)
user_id = response.json()['sub']

# Request match history
uri = f'https://pd.{region}.a.pvp.net/mmr/v1/players/{user_id}/competitiveupdates?startIndex=0&endIndex=20'
response = session.get(uri, headers=headers)

rank_map = {
    0: 'UNKNOWN', 1: 'UNKNOWN 1', 2: 'UNKNOWN 2',
    3: 'IRON 1', 4: 'IRON 2', 5: 'IRON 3',
    6: 'BRON 1', 7: 'BRON 2', 8: 'BRON 3',
    9: 'SILV 1', 10: 'SILV 2', 11: 'SILV 3',
    12: 'GOLD 1', 13: 'GOLD 2', 14: 'GOLD 3',
    15: 'PLAT 1', 16: 'PLAT 2', 17: 'PLAT 3',
    18: 'DIAM 1', 19: 'DIAM 2', 20: 'DIAM 3',
    21: 'IMMO 1', 22: 'IMMO 2', 23: 'IMMO 3',
    24: 'RADIANT'
}

level_map = {
    'Bonsai': 'Split',
    'Port': 'Icebox',
    'Triad': 'Haven',
    'Duality': 'Bind',
    'Ascent': 'Ascent',
    '?': '?'
}

for match in response.json()['Matches']:
    value = match['TierProgressAfterUpdate']
    change = match['TierProgressAfterUpdate'] - match['TierProgressBeforeUpdate']
    rank = rank_map.get(match['TierAfterUpdate'])
    friendly_change = f'+{change}' if (change > 0) else f'{change}'
    friendly_time = datetime.datetime.utcfromtimestamp(match['MatchStartTime'] / 1000).strftime('%Y-%m-%d %H:%M')
    level = match['MapID'].split('/')[3] if match['MapID'] else '?'
    friendly_level = level_map.get(level)
    print(f'{friendly_time}    {str.rjust(friendly_level,6)}    {str.rjust(str(value),3)}  ({str.rjust(friendly_change,3)})    [{rank}]')

input("Press enter...")

