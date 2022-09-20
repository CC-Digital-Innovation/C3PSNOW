import configparser
import secrets
from copy import deepcopy

import pysnow
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.params import Form
from fastapi.security import APIKeyHeader

app = FastAPI()

config = configparser.ConfigParser()
config.read('config.ini')

snow_client = pysnow.Client(config.get('snow', 'instance'), user=config.get('snow', 'user'), password=config.get('snow', 'pass'))

api_key = APIKeyHeader(name='X-API-Key')

def authorize(key: str = Depends(api_key)):
    if not secrets.compare_digest(key, config.get('creds', 'token')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token')

@app.post('/sendOrder', dependencies=[Depends(authorize)])
async def send_order(name: str = Form(...),
                     cocktail: str = Form(...),
                     severity: str = Form(...),
                     quantity: int = Form(...),
                     spec_Instruct: str = Form(None),
                     hole_Num: str = Form(...)):

    #USe SNOW API to screate snow incident: Done

    location_Map = {
        '1'  : 'Hole 1',
        '2'  : 'Hole 2',
        '3'  : 'Hole 3',
        '4'  : 'Hole 4',
        '5'  : 'Hole 5',
        '6'  : 'Hole 6',
        '7'  : 'Hole 7',
        '8'  : 'Hole 8',
        '9'  : 'Hole 9',
        '10' : 'Hole 10',
        '11' : 'Hole 11',
        '12' : 'Hole 12',
        '13' : 'Hole 13',
        '14' : 'Hole 14',
        '15' : 'Hole 15',
        '16' : 'Hole 16',
        '17' : 'Hole 17',
        '18' : 'Hole 18'
    }

    inc = {'u_drink_requester':f'{name}',
        'u_drink':f'{cocktail}',
        'location':f'{location_Map[hole_Num]}',
        'u_quantity':f'{quantity}',
        'urgency':f'{severity}',
        'description' : f'{spec_Instruct}',
        'short_description':f'{name} ordered {quantity} {cocktail}(s) at {location_Map[hole_Num]}'}

    incident_resource = snow_client.resource('/table/incident')
    result = incident_resource.create(payload=inc)
    #Return status ie order failed/created
    #Use OpsGenie API to create OPsGenie alert

def _add_rank(payload: list[dict], key_name: str) -> list[dict]:
    '''Return new payload ranked based on key_name. Same values result
    in the same rank. This assumes the payload is already reverse sorted
    (descending order).

    Args:
        payload (list[dict]): payload to be ranked
        key_name (str): name of key to compare, value should be type int

    Returns:
        list[dict]: new payload with rank key-value
    '''
    ranked_payload = []
    curr_max = 0
    curr_rank = 1
    for p in payload:
        curr = deepcopy(p)
        curr_rank = curr['rank'] = curr_rank+1 if curr[key_name] < curr_max else curr_rank
        curr_max = curr[key_name]
        ranked_payload.append(curr)
    return ranked_payload

@app.get('/rank/requestors', dependencies=[Depends(authorize)])
async def get_top_requestors():
    aggregate_inc_resrc = snow_client.resource('/stats/incident')
    params = {
        'sysparm_count': True,
        'sysparm_group_by': 'u_drink_requester',
        'sysparm_order_by': 'COUNT^DESC'
    }
    aggregate_inc_resrc.parameters.add_custom(params)
    query = pysnow.QueryBuilder().field('u_drink').is_not_empty()
    response = aggregate_inc_resrc.get(query).all()
    payload = [{
        'name': requestor['groupby_fields'][0]['value'],
        'total': int(requestor['stats']['count'])
    } for requestor in response]
    return _add_rank(payload, 'total')

@app.get('/rank/drinks', dependencies=[Depends(authorize)])
async def get_top_drinks():
    aggregate_inc_resrc = snow_client.resource('/stats/incident')
    params = {
        'sysparm_count': True,
        'sysparm_group_by': 'u_drink',
        'sysparm_order_by': 'COUNT^DESC',
        'sysparm_display_value': True
    }
    aggregate_inc_resrc.parameters.add_custom(params)
    query = pysnow.QueryBuilder().field('u_drink').is_not_empty()
    response = aggregate_inc_resrc.get(query).all()
    payload = [{
        'name': requestor['groupby_fields'][0]['value'],
        'total': int(requestor['stats']['count'])
    } for requestor in response]
    return _add_rank(payload, 'total')

@app.get('/rank/holes', dependencies=[Depends(authorize)])
async def get_top_holes():
    aggregate_inc_resrc = snow_client.resource('/stats/incident')
    params = {
        'sysparm_count': True,
        'sysparm_group_by': 'location',
        'sysparm_order_by': 'COUNT^DESC',
        'sysparm_display_value': True
    }
    aggregate_inc_resrc.parameters.add_custom(params)
    query = pysnow.QueryBuilder().field('location').starts_with('Hole')
    response = aggregate_inc_resrc.get(query).all()
    payload = [{
        'name': requestor['groupby_fields'][0]['value'],
        'total': int(requestor['stats']['count'])
    } for requestor in response]
    return _add_rank(payload, 'total')
