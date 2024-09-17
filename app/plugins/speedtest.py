import httpx
from app import config


def get_data():
    speedtest_configs = config.get_attribute(["speedtests"])
    result = []
    for speedtest_config in speedtest_configs:
        response = httpx.get(f"http://{speedtest_config['host']}:{speedtest_config['port']}/api/speedtest/latest")

        response_json = response.json()

        upload = response_json["data"]["upload"]
        download = response_json["data"]["download"]
        upload_formatted = f"{int(round(float(upload)))} Mbps"
        download_formatted = f"{int(round(float(download)))} Mbps"

        result.append(
            {
                "provider": speedtest_config["provider"],
                "upload": upload_formatted,
                "download": download_formatted,
            }
        )
    return result
