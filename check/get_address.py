import logging, aiohttp, requests

from settings import settings


API_KEY = settings.bots.api_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AddressValidator:
    def __init__(self, api_key=API_KEY):
        self.base_url = 'https://content-addressvalidation.googleapis.com/v1:validateAddress'
        self.api_key = api_key
        self.headers = {
            "authority": "content-addressvalidation.googleapis.com",
            "method": "POST",
            "path": f"/v1:validateAddress?alt=json&key={API_KEY}",
            "accept-encoding": "gzip, deflate, br",
            "Sec-Fetch-Site": "same-origin",
            "X-Goog-Encode-Response-If-Executable": "base64",
            "X-Origin": "https://developers-dot-devsite-v2-prod.appspot.com",
        }
        self.endpoint = f"{self.base_url}?alt=json&key={self.api_key}"

    async def validate_address(self, address_line):
        logging.info("Starting address validation")
        payload = f'{{"address": {{"regionCode": "AR", "addressLines": ["{address_line}"]}}}}'
        try:
            async with aiohttp.ClientSession() as session:
                logging.info(f"Sending request to {self.endpoint}")
                logging.info(f"Sending payload: {payload}")
                async with session.post(self.endpoint, data=payload, headers=self.headers) as response:
                    logging.info("Received response from the server")
                    response_json = await response.json() 
                    data = response_json['result']['address']['formattedAddress']
                    return data
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            raise

    async def get_validation_granularity(self, address_line):
        logging.info("Starting validation granularity")
        payload = f'{{"address": {{"regionCode": "AR", "addressLines": ["{address_line}"]}}}}'
        try:
            async with aiohttp.ClientSession() as session:
                logging.info(f"Sending request to {self.endpoint}")
                logging.info(f"Sending payload: {payload}")
                async with session.post(self.endpoint, data=payload, headers=self.headers) as response:
                    logging.info("Received response from the server")
                    response_json = await response.json() 
                    data = response_json['result']['verdict']['validationGranularity'] 
                    return data
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            raise