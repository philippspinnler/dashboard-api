# Dashboard API

API service for DakBoard integration with various data providers.

## Configuration

The application uses a YAML configuration file located at `config/config.yml`.

### Album Provider Configuration

You can choose between two album providers: **Immich** (default) or **iCloud**.

Set the `album_provider` configuration key:

```yaml
album_provider: immich  # Options: "immich" (default) or "icloud"
```

#### Immich Configuration
When using Immich as the album provider, configure the following:

```yaml
immich:
  url: https://your-immich-instance.com
  api_key: your-api-key
  album_name: Dashboard
  share_key: your-share-key
  c: your-c-parameter
```

#### iCloud Configuration
When using iCloud as the album provider, configure the following:

```yaml
icloud_album_id: your-album-id
```

The `/album` endpoint will automatically use the configured provider to fetch images.

## Running the Application

```bash
# Install dependencies
uv sync

# Run the application
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /album` - Get album images from configured provider (Immich or iCloud)
- `GET /calendar` - Get calendar events
- `GET /netatmo` - Get Netatmo data
- `GET /sonos` - Get Sonos data
- `GET /speedtest` - Get speedtest results
- `GET /weather` - Get weather data
- `GET /public-transportation` - Get public transportation data
- `GET /eo-guide` - Get EO Guide data
- `GET /presence` - Get presence data
