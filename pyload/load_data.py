#!/usr/bin/env python
# coding: utf-8

# In[66]:


import requests
import json
import pandas as pd


# In[67]:


client_id = '07bd2676-f950-48c0-8b12-ebd5e8b1491d'
client_secret = 'b874aa02-4333-4a4a-be10-55b44fc94eb3'
owner = "gitfeedV3"
thing = "github"
nodes = ['pulls', 'issues', 'commits']
# nodes = ['pulls', 'issues']
start_date = '2020-09-01T00:00:00-03:00'
end_date = '2020-09-15T23:59:59-03:00'


# In[68]:


def auth():
    _auth_url = 'http://agrows-keycloak.labbs.com.br/auth/realms/agroWS/protocol/openid-connect/token'
    _auth_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    _auth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    _auth_request = requests.post(_auth_url, data=_auth_data, headers=_auth_headers)
    return json.loads(_auth_request.text)['access_token']


# In[69]:


def load_data(_owner, _thing, _node, _token, _start_date, _end_date):
    _data_api_url = f'https://agrows-data-api.labbs.com.br/v1/owner/{_owner}/thing/{_thing}/node/{_node}'
    _data_api_params = {
        'startDateTime': _start_date,
        'endDateTime': _end_date
    }
    _data_api_headers = {
        'content-type': 'application/json',
        'Authorization' : f'Bearer {_token}'
    }
    _data_api_request = requests.get(_data_api_url, params=_data_api_params, headers=_data_api_headers)
    _data = json.loads(_data_api_request.text)['data']
    # data_source = json.dumps(data, indent=4, sort_keys=True)
    return _data


# In[70]:


def load_mongo_data(_repo_list):
    _data_api_url = f'http://localhost:3002/mongo/data'
    _data_api_params = {
        'repoList': _repo_list
    }
    _data_api_headers = {
        'content-type': 'application/json'
    }
    _data_api_request = requests.get(_data_api_url, json=_data_api_params, headers=_data_api_headers)
    _data = json.loads(_data_api_request.text)
    # _data_source = json.dumps(_data, indent=4, sort_keys=True)
    if 'data' in _data:
        return _data['data']
    return _data


# In[71]:


def load_raw_data(url):
    _data_api_headers = {
        'content-type': 'application/json'
    }
    _data_api_request = requests.get(url, headers=_data_api_headers)
    _data = json.loads(_data_api_request.text)
    return _data


# In[72]:


def calc_popularity(_qty):
    if _qty < 20:
        return 10
    elif _qty in range(20, 49):
        return 30
    elif _qty in range(50, 99):
        return 60
    elif _qty >= 100:
        return 90


# In[73]:


access_token = auth()

data = {}
for node in nodes:
    raw_data = load_data(owner, thing, node, access_token, start_date, end_date)
    raw_data = [{'dateTime': x['dateTime'], **x.get('attributes')} for x in raw_data]
    for r in raw_data:
        if 'dono' not in r:
            del r
            continue
        r['owner'] = r.pop('dono')
        for k in ['owner', 'name', 'participants', 'comments', 'author', 'labels', 'message']:
            if k in r and ':' in r[k]:
                r[k] = r[k].split(":")[1]
            if k in r and r[k] == 'no-string':
                r[k] = ''
    # Keeping last version of itens
    if node in 'commits':
        data[node] = pd.DataFrame.from_dict(raw_data)
    else:
        data[node] = pd.DataFrame.from_dict(raw_data).sort_values('dateTime').groupby('number').tail(1)


# In[74]:


# Getting owner and name from all nodes to request data from Mongo
frames = []
for k in data:
    frames.append(data[k][['owner', 'name']])

result = pd.concat(frames).drop_duplicates().to_json(orient="table", index=None)
repoList = json.loads(result)['data']

code_data = load_mongo_data(repoList)
data['code'] = pd.DataFrame.from_dict(code_data)


