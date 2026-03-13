#!/usr/bin/env python3
import requests, json, warnings
warnings.filterwarnings('ignore')

TOKEN = 'd59387ad-25d3-4707-bca5-f06acfcbe112'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
API = 'https://backboard.railway.app/graphql/v2'
SERVICE_ID = 'ba2312aa-98c8-406f-b30b-e6ef9d44cbca'

def gql(query, variables=None):
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, headers=HEADERS, timeout=15, verify=False)
    return r.json()

# Take down the service
result = gql('''
mutation($id: String!) {
  serviceInstanceRedeploy(serviceId: $id)
}''', {'id': SERVICE_ID})
print("Service stopped:", json.dumps(result))
