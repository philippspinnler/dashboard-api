from homeassistant_api import Client
import asyncio
from app import config

URL = config.get_attribute(['home_assistant', 'url'])
TOKEN = config.get_attribute(['home_assistant', 'token'])

# Get entity IDs from config
GRID_CONSUMPTION_ENTITY = config.get_attribute(['inverter', 'grid_consumption_entity'])
GRID_FEEDIN_ENTITY = config.get_attribute(['inverter', 'grid_feedin_entity'])
POWER_CONSUMPTION_ENTITY = config.get_attribute(['inverter', 'power_consumption_entity'])
PV_POWER_ENTITY = config.get_attribute(['inverter', 'pv_power_entity'])
BATTERY_STATE_OF_CHARGE_ENTITY = config.get_attribute(['inverter', 'battery_state_of_charge_entity'])


async def get_data():
    def _get_inverter_data():
        with Client(f"{URL}/api", TOKEN) as client:
            # Fetch all entity states
            grid_consumption = client.get_entity(entity_id=GRID_CONSUMPTION_ENTITY).get_state().state
            grid_feedin = client.get_entity(entity_id=GRID_FEEDIN_ENTITY).get_state().state
            power_consumption = client.get_entity(entity_id=POWER_CONSUMPTION_ENTITY).get_state().state
            pv_power = client.get_entity(entity_id=PV_POWER_ENTITY).get_state().state
            battery_state_of_charge = client.get_entity(entity_id=BATTERY_STATE_OF_CHARGE_ENTITY).get_state().state

            return {
                "grid_consumption": grid_consumption,
                "grid_feedin": grid_feedin,
                "power_consumption": power_consumption,
                "pv_power": pv_power,
                "battery_state_of_charge": battery_state_of_charge,
            }
    
    return await asyncio.to_thread(_get_inverter_data)
