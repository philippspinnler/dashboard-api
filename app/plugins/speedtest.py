import httpx
from app import config


def format_speed(speed_mbps: float) -> str:
    """Format speed with appropriate unit (Kbps, Mbps, Gbps, Tbps)"""
    speed = float(speed_mbps)
    
    if speed < 1:
        # Convert to Kbps
        value = speed * 1000
        if value < 10:
            return f"{value:.2f} Kbps"
        elif value < 100:
            return f"{value:.1f} Kbps"
        else:
            return f"{int(round(value))} Kbps"
    elif speed < 1000:
        # Keep as Mbps
        if speed < 10:
            return f"{speed:.2f} Mbps"
        elif speed < 100:
            return f"{speed:.1f} Mbps"
        else:
            return f"{int(round(speed))} Mbps"
    elif speed < 1000000:
        # Convert to Gbps
        value = speed / 1000
        if value < 10:
            return f"{value:.2f} Gbps"
        elif value < 100:
            return f"{value:.1f} Gbps"
        else:
            return f"{int(round(value))} Gbps"
    else:
        # Convert to Tbps
        value = speed / 1000000
        if value < 10:
            return f"{value:.2f} Tbps"
        elif value < 100:
            return f"{value:.1f} Tbps"
        else:
            return f"{int(round(value))} Tbps"


async def get_data():
    speedtest_configs = config.get_attribute(["speedtests"])
    result = []
    async with httpx.AsyncClient() as client:
        for speedtest_config in speedtest_configs:
            response = await client.get(f"http://{speedtest_config['host']}:{speedtest_config['port']}/api/speedtest/latest")

            response_json = response.json()

            upload = response_json["data"]["upload"]
            download = response_json["data"]["download"]
            upload_formatted = format_speed(upload)
            download_formatted = format_speed(download)

            result.append(
                {
                    "provider": speedtest_config["provider"],
                    "upload": upload_formatted,
                    "download": download_formatted,
                }
            )
    return result
