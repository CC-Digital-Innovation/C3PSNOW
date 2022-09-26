import os
import secrets
from copy import deepcopy

import dotenv
import pysnow
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.params import Form
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# load secrets from .env
dotenv.load_dotenv()

API_KEY = os.getenv('API_KEY')
SNOW_INST = os.getenv('SNOW_INST')
SNOW_USER = os.getenv('SNOW_USER')
SNOW_PASS = os.getenv('SNOW_PASS')

snow_client = pysnow.Client(SNOW_INST, user=SNOW_USER, password=SNOW_PASS)

app = FastAPI(root_path='/c3psnow')

class Order(BaseModel):
    name: str
    drinks: dict
    urgency: int
    spec_Instruct: str = None
    hole_Num: str
    cart_Num: int = None

api_key = APIKeyHeader(name='X-API-Key')

def authorize(key: str = Depends(api_key)):
    if not secrets.compare_digest(key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token')

@app.post('/sendOrder', dependencies=[Depends(authorize)])
async def send_order(order: Order):

    drink_map = {
        'Drink 1': 'u_drink_1',
        'Drink 2': 'u_drink_2',
        'Drink 3': 'u_drink_3',
        'Drink 4': 'u_drink_4',
        'Drink 5': 'u_drink_5',
        'Drink 6': 'u_drink_6',
        'Drink 7': 'u_drink_7',
        'Drink 8': 'u_drink_8',
        'Soda 1': 'u_soda_1',
        'Soda 2': 'u_soda_2',
        'Water': 'u_water'
    }
    
    #Set up service now payload from recieved order information
    inc = {'u_drink_requester':f"{order.name}",
        'u_cart_number': f"{order.cart_Num}",
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
    inc['short_description'] = description + f"at {order.hole_Num} "

    #Use pysnow to screate snow incident
    incident_resource = snow_client.resource('/table/incident')
    result = incident_resource.create(payload=inc)
    #Return status ie order failed/created

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
