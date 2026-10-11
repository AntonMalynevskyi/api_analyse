import requests

from api_analyse.config import config


def download_road_data():
    api_key = config.api.opentransport_key

    headers = {
        'Authorization': f'Bearer {api_key}',
        'SOAPAction': 'http://opentransportdata.swiss/TDP/Soap_Datex2/Pull/v1/pullTrafficMessages',
        'If-Modified-Since': '2025-05-27T10:00:00',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    with open(config.paths.data_raw / "traffic" / 'VM_request_body.xml', 'rb') as f:
        data = f.read()

    response = requests.post(
        'https://api.opentransportdata.swiss/TDP/Soap_Datex2/TrafficSituations/Pull',
        headers=headers,
        data=data,
    )

    with open(config.paths.data_raw / "traffic" / "traffic_situations.xml", 'wb') as f:
        f.write(response.content)


if __name__ == "__main__":
    print("loaded downloader function")
