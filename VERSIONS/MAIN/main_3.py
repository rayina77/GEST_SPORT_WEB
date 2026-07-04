from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database.db import get_connection

app = FastAPI(title="GEST SPORT")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "GEST SPORT"
        }
    )

@app.get("/athletes")
async def athletes(request: Request):

    conn = get_connection()

    athletes = conn.execute("""
        SELECT *
        FROM athletes
        ORDER BY nom
    """).fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="athletes.html",
        context={
            "title": "Athlètes",
            "athletes": athletes
        }
    )