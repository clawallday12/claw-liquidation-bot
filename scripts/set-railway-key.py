#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
PROJECT_ID = 'c7af4ad0-0b6e-436b-8105-8735892b4c5f'
SERVICE_ID = 'ba2312aa-98c8-406f-b30b-e6ef9d44cbca'
ENV_ID = '6f81b107-2734-4d1f-9958-c4191e5483e3'

PRIVATE_KEY = '54ad43c090d1f732abf1b6852ec4a88ceb131d8764b8ffe3a80d8384d02308fd'
WALLET_ADDRESS = '0xA8297c4B031022D8d8e3Ce76322139A0120D6931'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    try: return r.json()
    except: return {}

print('Setting environment variables in Railway...')
result = gql('''
mutation($input: VariableCollectionUpsertInput!) {
  variableCollectionUpsert(input: $input)
}''', {
    'input': {
        'projectId': PROJECT_ID,
        'serviceId': SERVICE_ID,
        'environmentId': ENV_ID,
        'variables': {
            'PRIVATE_KEY': PRIVATE_KEY,
            'WALLET_ADDRESS': WALLET_ADDRESS,
            'CHECK_INTERVAL': '60',
        }
    }
})
print(json.dumps(result, indent=2))
