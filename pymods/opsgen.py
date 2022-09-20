import opsgenie_sdk

class OpsInstance:
    def __init__(self, key):
        config = opsgenie_sdk.Configuration()
        config.api_key['Authorization'] = key
        api_client = opsgenie_sdk.ApiClient(configuration = config)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=api_client)

    def createAlert(self, payload):
        body = opsgenie_sdk.CreateAlertPayload(**payload)
        try:
            response = self.alert_api.create_alert(create_alert_payload=body)
            return response
        except opsgenie_sdk.ApiException as e:
            print(f"Exception when creating alert: {e}")
