# C3PSNOW
## Front End

### Summary
The front end of c3psnow is a bootstrap html web app that is designed to take cocktail orders from golfers out on the course

### Workflow
Users start by scanning a QR code to get to the web app. From there, to order drinks they select the order drinks button. This takes them to a form to fill out for a drink order. The name field is populated with a pull from NoCo DB where we have stored all the users names. This form data is sent to a middle api where it is proccessed into a service now incident. The other options on the main page are for leaderboards and seeing the status of their orders. These utilize the same middle api to pull information from service now.

## Middle
The middle api is continuously running in a kubernetes cluster and kept up to date automatically from github though argoCD and Concourse. This api has several endpoints to send orders to snow, get data from snow, and get data from NoCo DB.

### Sample payload to create order:
```json
{
  "name": "John Smith",
  "drinks": {
    "Transfusion":                    0,
    "Wild Arnold Palmer":             0,
    "Bloody Mary":                    0,
    "Dark and Stormy":                0,
    "Coors Light":                    0,
    "New Belgium Voodoo Ranger IPA":  0,
    "Sam Adams Seasonal":             0,
    "Goose Island IPA":               0,
    "Unsweetended Ice Tea":           0,
    "Arnold Palmer":                  0,
    "Water":                          0
},
  "urgency": 1-3,
  "spec_Instruct": "Special instructions", #optional
  "hole_Num": "Hole 5"                     #important, must be formatted like this: "Hole #"
}
```
## Back End
The back end of c3psnow consists of a developer instance of service now designed specifically to hold drink orders as incidents. The other half of the back end is a NoCo DB that holds user information


## Architecture Diagram
![image](https://github.com/CC-Digital-Innovation/C3PSNOW/blob/main/c3psnow-frontend/images/c3arch.png?raw=true)
