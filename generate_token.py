import json

import gkeepapi


config = json.load(open('.config.json'))

keep = gkeepapi.Keep()

keep.login(config['email'], config['password'])

config['token'] = keep.getMasterToken()

json.dump(config, open('.config.json', 'w'), indent=2)
