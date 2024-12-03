from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse
from app.plugins.ical import get_events
from app.plugins.netatmo import get_data as get_data_netatmo
from app.plugins.sonos import get_data as get_data_sonos, proxy
from app.plugins.speedtest import get_data as get_data_speedtest
# from app.plugins.album import album_uploade_page, upload_image, delete_image, get_data
from app.plugins.icloud_album import get_data as get_data_album
from app.plugins.weather import get_data as get_data_weather
from app.plugins.publictransportation import get_data as get_data_publictransportation
from app.plugins.eoguide import get_data as get_data_eoguide
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi.middleware.cors import CORSMiddleware


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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/calendar")
@cache(expire=900)
async def calendar():
    return get_events()


@app.get("/netatmo")
@cache(expire=900)
async def netatmo():
    return get_data_netatmo()


@app.get("/sonos")
@cache(expire=10)
async def sonos():
    return get_data_sonos()


@app.get("/speedtest")
@cache(expire=1800)
async def speedtest():
    return get_data_speedtest()


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
@cache(expire=1800)
async def album():
    return get_data_album()


@app.get("/weather")
@cache(expire=3600)
async def get_weather(
    lat: float = Query(47.4176969, description="Latitude"), lon: float = Query(7.7612123, description="Longitude")
):
    return get_data_weather(lat=lat, lon=lon)


@app.get("/public-transportation")
@cache(expire=300)
async def get_departures(connections: str = '[["Hölstein, Süd", "Liestal, Bahnhof", "direct"]]'):
    return get_data_publictransportation(connections)


@app.get("/eo-guide")
@cache(expire=21_600)
async def eo_guide():
    return get_data_eoguide()


@app.get("/sonos/image-proxy")
async def proxy_image(url: str = Query(..., description="The full URL of the image to proxy")):
    return proxy(url)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
