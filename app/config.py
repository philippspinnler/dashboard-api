import yaml

file_path = "config/config.yml"


def _load_config():
    """Load the configuration from the file."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def _save_config(config):
    """Save the updated configuration back to the file."""
    with open(file_path, "w") as file:
        yaml.safe_dump(config, file)


def get_attribute(keys):
    """
    Retrieve a specific attribute value from the config.
    Keys should be a list of nested keys. E.g., ['netatmo', 'access_token']
    """
    config = _load_config()
    attr = config
    for key in keys:
        if isinstance(attr, dict):
            attr = attr.get(key)
        else:
            return None  # Key path does not exist
    return attr


def update_attribute(keys, value):
    """
    Update a specific attribute value in the config.
    Keys should be a list of nested keys. E.g., ['netatmo', 'access_token']
    """
    config = _load_config()
    attr = config
    for key in keys[:-1]:
        attr = attr.setdefault(key, {})  # Ensure the path exists, create it if it doesn't
    attr[keys[-1]] = value

    # Save the updated configuration back to the file
    _save_config(config)
