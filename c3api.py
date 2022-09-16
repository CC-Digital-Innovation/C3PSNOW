import json
import configparser
from fastapi.params import Form
from fastapi import FastAPI
import requests



app = FastAPI()

config = configparser.ConfigParser()
config.read('config.ini')

@app.post("/sendOrder/")
async def sendOrder(Token: str = Form(...),
                     name: str = Form(...),
                     cocktail: str = Form(...),
                     severity: str = Form(...),
                     quantity: int = Form(...),
                     spec_Instruct: str = Form(None),
                     hole_Num: str = Form(...)):

        if Token == config.get('creds', 'token'):
            #USe SNOW API to screate snow incident: Done

            location_Map = {
                "1"  : "Hole 1",
                "2"  : "Hole 2",
                "3"  : "Hole 3",
                "4"  : "Hole 4",
                "5"  : "Hole 5",
                "6"  : "Hole 6",
                "7"  : "Hole 7",
                "8"  : "Hole 8",
                "9"  : "Hole 9",
                "10" : "Hole 10",
                "11" : "Hole 11",
                "12" : "Hole 12",
                "13" : "Hole 13",
                "14" : "Hole 14",
                "15" : "Hole 15",
                "16" : "Hole 16",
                "17" : "Hole 17",
                "18" : "Hole 18"
            }

            inc = {"u_drink_requester":f"{name}",
                "u_drink":f"{cocktail}",
                "location":f"{location_Map[hole_Num]}",
                "u_quantity":f"{quantity}",
                "urgency":f"{severity}",
                "description" : f"{spec_Instruct}",
                "short_description":f"{name} ordered {quantity} {cocktail}(s) at {location_Map[hole_Num]}"}

            url = config.get('endpoints', 'incurl')
            user = config.get('creds', 'user')
            passw = config.get('creds', 'pass')
            headers = {"Content-Type":"application/json","Accept":"application/json"}
            resp = requests.post(url, auth=(user,passw), headers = headers, data = json.dumps(inc))
            #Return status ie order failed/created
            #Use OpsGenie API to create OPsGenie alert
        else:
            print("You are not authorized to use this service")

    
    