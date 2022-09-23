# backend-C3PSNOW
## Summary
API to take orders from front end application and create incidents in a service now instance

### Sample payload:
```json
{
  "name": "John Smith",
  "drinks": {"Drink 1": 0,
             "Drink 2": 0,
             "Drink 3": 0,
             "Drink 4": 0,
             "Drink 5": 0,
             "Drink 6": 0,
             "Drink 7": 0,
             "Drink 8": 0,
             "Soda 1": 0,
             "Soda 2": 0,
             "Water": 0},
  "urgency": 1-3,
  "spec_Instruct": "Special instructions", #optional
  "hole_Num": "Hole 5"                     #important, must be formatted like this: "Hole #"
  "cart_Num" : 4                           #Optional
}
```
