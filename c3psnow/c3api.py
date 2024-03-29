import os
import secrets
from copy import deepcopy
from enum import Enum
from operator import itemgetter
from pathlib import PurePath
import dotenv
import pysnow
import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# load secrets from .env
dotenv.load_dotenv(PurePath(__file__).with_name('.env'))

API_KEY = os.getenv('API_KEY')
SNOW_INST = os.getenv('SNOW_INST')
SNOW_USER = os.getenv('SNOW_USER')
SNOW_PASS = os.getenv('SNOW_PASS')
NOCO_KEY = os.getenv('NOCO_KEY')
NOCOBASEURL = os.getenv('NOCO_URL')
NOCOHEAD  = {
        'xc-token': NOCO_KEY,
        'Content-Type': 'application/json'
    }

snow_client = pysnow.Client(SNOW_INST, user=SNOW_USER, password=SNOW_PASS)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://c3psnow.quokka.rocks'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

class Order(BaseModel):
    name: str
    drinks: dict
    urgency: int
    spec_Instruct: str = None
    hole_Num: str
    #cart_Num: int = None

api_key = APIKeyHeader(name='X-API-Key')

def authorize(key: str = Depends(api_key)):
    if not secrets.compare_digest(key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token')

drink_map = {
    'Transfusion': 'u_drink_1',
    'Wild Arnold Palmer': 'u_drink_2',
    'Bloody Mary': 'u_drink_3',
    'Dark and Stormy': 'u_drink_4',
    'Apple Cider Bourbon': 'u_drink_5',
    'Coors Light': 'u_drink_6',
    'New Belgium Voodoo Ranger IPA': 'u_drink_7',
    'Sam Adams Seasonal': 'u_drink_8',
    'Unsweetened Iced Tea': 'u_soda_1',
    'Arnold Palmer': 'u_soda_2',
    'Water': 'u_water'
}

@app.post('/sendOrder', dependencies=[Depends(authorize)])
async def send_order(order: Order):
    incident_resource = snow_client.resource('/table/incident')
    #Set up service now payload from recieved order information
    inc = {'u_drink_requester':f"{order.name}",
        #'u_cart_number': f"{order.cart_Num}",
        'category' : 'drink',
        'location':f"{order.hole_Num}",
        'urgency':f"{order.urgency}",
        'u_special_instructions' : f"{order.spec_Instruct}"}
    
    description = f"{order.name} ordered "
    for drink, quant in order.drinks.items():
        drinksnowname = drink_map[drink]
        inc[drinksnowname] = quant
        if quant != 0:
            description = description + f"{drink} qty: {quant} "


    nocorul = f"{NOCOBASEURL}/find-one"

    query = {
        'where' : f"(Name,eq,{order.name})"
    }

    response = requests.get(nocorul, headers= NOCOHEAD, params = query)
    if response.content:
        phone= f"+1{response.json()['PhoneNumber']}"

        inc['u_phone_number']=phone
        inc['u_cart_number']=response.json()['CartID']    #Use pysnow to screate snow incident
        inc['short_description'] = description + f"from cart {inc['u_cart_number']} at {order.hole_Num}"
    else:
        inc['short_description'] = description + f"at {order.hole_Num} "
    try:
        result = incident_resource.create(payload=inc)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Order failed to submit to service now')
    
    return ("Order Successfully Submitted")

def _add_rank(payload: list[dict], key_name: str) -> list[dict]:
    '''Return new payload ranked based on key_name. Same values result
    in the same rank.

    Args:
        payload (list[dict]): payload to be ranked
        key_name (str): name of key to compare, value should be type int

    Returns:
        list[dict]: new payload with rank key-value
    '''
    sorted_payload = sorted(payload, key=itemgetter('total'), reverse=True)
    ranked_payload = []
    curr_max = 0
    curr_rank = 1
    for p in sorted_payload:
        curr = deepcopy(p)
        curr_rank = curr['rank'] = curr_rank+1 if curr[key_name] < curr_max else curr_rank
        curr_max = curr[key_name]
        ranked_payload.append(curr)
    return ranked_payload

@app.get('/rank/requestors', dependencies=[Depends(authorize)])
async def get_top_requestors():
    aggregate_inc_resrc = snow_client.resource('/stats/incident')
    params = {
        'sysparm_group_by': 'u_drink_requester',
        'sysparm_display_value': True,
        'sysparm_sum_fields': ','.join(drink_map.values()),
        'sysparm_query': 'u_drink_requesterISNOTEMPTY^sys_created_on>javascript:gs.endOfYesterday()'
    }
    aggregate_inc_resrc.parameters.add_custom(params)
    response = aggregate_inc_resrc.get().all()
    payload = []
    for requestor in response:
        total = sum([int(n) for n in requestor['stats']['sum'].values()])
        if total <= 0:
            continue
        payload.append({
            'name': requestor['groupby_fields'][0]['value'],
            'total': total
        })
    return _add_rank(payload, 'total')

@app.get('/rank/drinks', dependencies=[Depends(authorize)])
async def get_top_drinks():
    aggregate_inc_resrc = snow_client.resource('/stats/incident')
    params = {
        'sysparm_display_value': True,
        'sysparm_sum_fields': ','.join(drink_map.values()),
        'sysparm_query': 'sys_created_on>javascript:gs.endOfYesterday()'
    }
    aggregate_inc_resrc.parameters.add_custom(params)
    response = aggregate_inc_resrc.get().all()
    payload = []
    for drink_key, total in response[0]['stats']['sum'].items():
        if int(total):
            payload.append({
                'name': next((k for k, v in drink_map.items() if v == drink_key)),
                'total': int(total)
            })
    return _add_rank(payload, 'total')

@app.get('/rank/holes', dependencies=[Depends(authorize)])
async def get_top_holes():
    aggregate_inc_resrc = snow_client.resource('/stats/incident')
    params = {
        'sysparm_group_by': 'location',
        'sysparm_sum_fields': ','.join(drink_map.values()),
        'sysparm_display_value': True,
        'sysparm_query': 'locationSTARTSWITHHole^sys_created_on>javascript:gs.endOfYesterday()'
    }
    aggregate_inc_resrc.parameters.add_custom(params)
    response = aggregate_inc_resrc.get().all()
    payload = [{
        'name': location['groupby_fields'][0]['value'],
        'total': sum([int(n) for n in location['stats']['sum'].values()])
    } for location in response]
    return _add_rank(payload, 'total')

class State(Enum):
    NEW = 'New'
    ASSIGNED = 'Drink Delivery Assigned'
    PROCESS = 'Drink Being Made'
    DELIVER = 'Drink Being Delivered'
    CLOSED = 'Closed'
    CANCELED = 'Canceled'

fields = ['sys_created_on', 'u_drink_requester', 'urgency', 'state', 
          'u_drink_1', 'u_drink_2', 'u_drink_3', 'u_drink_4', 'u_drink_5', 
          'u_drink_6', 'u_drink_7', 'u_drink_8', 'u_soda_1', 'u_soda_2', 
          'u_water', 'assigned_to']

@app.get('/queue', dependencies=[Depends(authorize)])
async def get_queue(state: State = None, offset: int = 0, limit: int = 10):
    incident_resource = snow_client.resource('/table/incident')
    params = {
        'sysparm_limit': limit,
        'sysparm_offset': offset,
        'sysparm_fields': ','.join(fields),
        'sysparm_query': 'sys_created_on>javascript:gs.endOfYesterday()^u_drink_requesterISNOTEMPTY^ORDERBYurgency^ORDERBYsys_created_on'
    }
    # inconsistent results with pysnow, resorting to direct params
    if state:
        params['state'] = state.value
    incident_resource.parameters.add_custom(params)
    orders = incident_resource.get().all()
    retorder=[]
    for order in orders:
        order['total_drinks'] = (int(order['u_drink_1']) + int(order['u_drink_2']) 
            + int(order['u_drink_3']) + int(order['u_drink_4']) + int(order['u_drink_5']) 
            + int(order['u_drink_6']) + int(order['u_drink_7']) + int(order['u_drink_8']) 
            + int(order['u_soda_1']) + int(order['u_soda_2']) + int(order['u_water']))
        retorder.append(order)
    return retorder

alcoholic = ['u_drink_1', 'u_drink_2', 'u_drink_3', 'u_drink_4', 'u_drink_5', 
          'u_drink_6', 'u_drink_7', 'u_drink_8']

@app.get('/getBacStats', dependencies=[Depends(authorize)])
async def get_bac_stats(name: str):
    aggregate_drinks = snow_client.resource('/stats/incident')
    # inconsistent results with pysnow, resorting to direct params
    params = {
        'sysparm_display_value': True,
        'sysparm_sum_fields': ','.join(alcoholic),
        'sysparm_group_by': 'u_drink_requester',
        'sysparm_query': f'sys_created_on>javascript:gs.endOfYesterday()^u_drink_requester={name}'
    }
    aggregate_drinks.parameters.add_custom(params)
    response = aggregate_drinks.get().all()
    try:
        total = sum([int(n) for n in response[0]['stats']['sum'].values()])
    except IndexError:
        return {}

    aggregate_drinks_by_date = snow_client.resource('/stats/incident')
    # inconsistent results with pysnow, resorting to direct params
    params = {
        'sysparm_display_value': True,
        'sysparm_min_fields': 'sys_created_on',
        'sysparm_group_by': 'u_drink_requester',
        'sysparm_query': f'sys_created_on>javascript:gs.endOfYesterday()^u_drink_requester={name}^u_total_drinks>0'
    }
    aggregate_drinks_by_date.parameters.add_custom(params)
    response = aggregate_drinks_by_date.get().all()
    try:
        first_drink_time = response[0]['stats']['min']['sys_created_on']
    except IndexError:
        return {}
    return {'total': total, 'time': first_drink_time}

@app.get('/noco/getNames', dependencies=[Depends(authorize)])
async def get_names():

    url = f"{NOCOBASEURL}"

    query = {
        'column_name' : 'Name',
        'limit': 1000
    }


    res = requests.get(url, headers=NOCOHEAD, params=query)
    names = []
    for record in res.json()['list']:
        names.append(record['Name'])

    return names
