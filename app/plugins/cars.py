from homeassistant_api import Client
import asyncio
from app import config

URL = config.get_attribute(['home_assistant', 'url'])
TOKEN = config.get_attribute(['home_assistant', 'token'])

# List of car configurations
cars_config = config.get_attribute(['cars']) or []


async def get_data():
    def _get_cars_data():
        cars_data = []

        with Client(f"{URL}/api", TOKEN) as client:
            for car_config in cars_config:
                car_name = car_config.get('name', 'Unknown Car')
                range_entity = car_config.get('range_entity')
                charging_active = car_config.get('charging_active_entity')
                charging_power = car_config.get('charging_power_entity')
                end_of_charge_entity = car_config.get('end_of_charge_entity')
                state_of_charge_entity = car_config.get('state_of_charge_entity')

                range = client.get_entity(entity_id=range_entity)

                # Initialize car entry
                car_entry = {
                    "name": car_name,
                    "range": client.get_entity(entity_id=range_entity).get_state().state,
                    "charge_procentage": client.get_entity(entity_id=state_of_charge_entity).get_state().state,
                    "charging": True if client.get_entity(entity_id=charging_active).get_state().state == "on" else False,
                    "charging_power": client.get_entity(entity_id=charging_power).get_state().state,
                    "end_of_charge": client.get_entity(entity_id=end_of_charge_entity).get_state().state,
                }
                
                cars_data.append(car_entry)

        return cars_data
    
    return await asyncio.to_thread(_get_cars_data)
