from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI, File, Form, Query, UploadFile, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.plugins.ical import get_events
from app.plugins.netatmo import get_data as get_data_netatmo
from app.plugins.sonos import get_data as get_data_sonos, proxy
from app.plugins.speedtest import get_data as get_data_speedtest
# from app.plugins.album import album_uploade_page, upload_image, delete_image, get_data
from app.plugins.icloud_album import get_data as get_data_icloud
from app.plugins.immich import get_data as get_data_immich
from app.plugins.weather import get_data as get_data_weather
from app.plugins.publictransportation import get_data as get_data_publictransportation
from app.plugins.eoguide import get_data as get_data_eoguide
from app.plugins.presence import get_data as get_data_presence
from app.plugins.cars import get_data as get_data_cars
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi.middleware.cors import CORSMiddleware


class NoCacheMiddleware(BaseHTTPMiddleware):
    """Middleware to prevent browser caching by adding no-cache headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend())
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add no-cache middleware to prevent browser caching
app.add_middleware(NoCacheMiddleware)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/calendar")
@cache(expire=900)
async def calendar():
    return await get_events()


@app.get("/netatmo")
@cache(expire=300)
async def netatmo():
    return await get_data_netatmo()


@app.get("/sonos")
@cache(expire=10)
async def sonos():
    return get_data_sonos()


@app.get("/speedtest")
@cache(expire=1800)
async def speedtest():
    return await get_data_speedtest()


"""app.mount("/album/images", StaticFiles(directory="images"), name="images")


@app.get("/album")
@cache(expire=1800)
async def album():
    return get_data()


@app.get("/album/admin", response_class=HTMLResponse)
async def album_admin():
    return album_uploade_page()


@app.post("/album/upload-image/")
async def upload_file(file: UploadFile = File(...)):
    return upload_image(file)


@app.post("/album/delete-image/")
async def delete_file(filename: str = Form(...)):
    return delete_image(filename)
"""

@app.get("/album")
@cache(expire=21_600)
async def album():
    from app import config
    
    # Get the album provider from config, default to "immich"
    provider = config.get_attribute(["album_provider"]) or "immich"
    
    if provider == "immich":
        return await get_data_immich()
    elif provider == "icloud":
        return await get_data_icloud()
    else:
        raise ValueError(f"Invalid album provider: {provider}. Valid options are 'immich' or 'icloud'.")


@app.get("/weather")
@cache(expire=3600)
async def get_weather(
    lat: float = Query(47.4176969, description="Latitude"), lon: float = Query(7.7612123, description="Longitude")
):
    return await get_data_weather(lat=lat, lon=lon)


@app.get("/public-transportation")
@cache(expire=300)
async def get_departures(connections: str = '[["Hölstein, Süd", "Liestal, Bahnhof", "direct"]]'):
    return await get_data_publictransportation(connections)


@app.get("/eo-guide")
@cache(expire=21_600)
async def eo_guide():
    return await get_data_eoguide()


@app.get("/sonos/image-proxy")
async def proxy_image(url: str = Query(..., description="The full URL of the image to proxy")):
    return await proxy(url)


@app.get("/presence")
@cache(expire=120)
async def presence():
    return await get_data_presence()


@app.get("/cars")
@cache(expire=120)
async def cars():
    return await get_data_cars()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
