from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse
from app.plugins.ical import get_events
from app.plugins.netatmo import get_data as get_data_netatmo
from app.plugins.sonos import get_data as get_data_sonos
from app.plugins.speedtest import get_data as get_data_speedtest
from app.plugins.album import album_uploade_page, upload_image, delete_image, get_data
from app.plugins.weather import get_data as get_data_weather
from app.plugins.publictransportation import get_data as get_data_publictransportation
from fastapi.staticfiles import StaticFiles

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/calendar")
async def calendar():
    return get_events()


@app.get("/netatmo")
async def netatmo():
    return get_data_netatmo()


@app.get("/sonos")
async def sonos():
    return get_data_sonos()


@app.get("/speedtest")
async def speedtest():
    return get_data_speedtest()


app.mount("/album/images", StaticFiles(directory="images"), name="images")


@app.get("/album")
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


@app.get("/weather")
async def get_weather(
    lat: float = Query(47.4176969, description="Latitude"), lon: float = Query(7.7612123, description="Longitude")
):
    return get_data_weather(lat=lat, lon=lon)


@app.get("/public-transportation")
async def get_departures(connections: str = '[["Hölstein, Süd", "Liestal, Bahnhof", "direct"]]'):
    return get_data_publictransportation(connections)
