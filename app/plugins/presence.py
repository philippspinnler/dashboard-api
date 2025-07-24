from homeassistant_api import Client
from app import config

URL = config.get_attribute(['home_assistant', 'url'])
TOKEN = config.get_attribute(['home_assistant', 'token'])

# List of person entities you want to check
person_entities = config.get_attribute(['home_assistant', 'person_entities'])

def get_data():
    persons = []
    away = []

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
            
            if state.state == "home":
                persons.append(person_entry)
            else:
                persons.append(person_entry)

    return persons