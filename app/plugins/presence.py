from homeassistant_api import Client
import asyncio
from app import config

URL = config.get_attribute(['home_assistant', 'url'])
TOKEN = config.get_attribute(['home_assistant', 'token'])

# List of person entities you want to check
person_entities = config.get_attribute(['home_assistant', 'person_entities'])

async def get_data():
    def _get_presence_data():
        persons = []

        with Client(f"{URL}/api", TOKEN) as client:
            for entity_id in person_entities:
                person = client.get_entity(entity_id=entity_id)
                state = person.get_state()
                avatar_url = state.attributes.get('entity_picture', None)
                
                # If avatar_url exists and is relative, add full URL
                if avatar_url and avatar_url.startswith('/'):
                    avatar_url = f"{URL}{avatar_url}"
                
                friendly_name = state.attributes.get('friendly_name', entity_id)
                
                person_entry = {
                    "name": friendly_name,
                    "avatar_url": avatar_url,
                    "state": state.state,
                }
                
                persons.append(person_entry)
        
        # Sort persons alphabetically by name (case-insensitive)
        persons.sort(key=lambda x: x['name'].lower())

        return {
            "persons": persons
        }
    
    return await asyncio.to_thread(_get_presence_data)
