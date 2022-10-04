# backend-C3PSNOW
## Summary
API to take orders from front end application and create incidents in a service now instance

### Sample payload:
```json
{
  "name": "John Smith",
  "drinks": {
    "Transfusion":                    0,
    "Wild Arnold Palmer":            0,
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
