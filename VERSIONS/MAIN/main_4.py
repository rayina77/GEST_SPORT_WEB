from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database.db import get_connection

app = FastAPI(title="GEST SPORT")

# =====================================
# DOSSIERS STATIQUES
# =====================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# =====================================
# TEMPLATES
# =====================================

templates = Jinja2Templates(directory="templates")

# =====================================
# PAGE ACCUEIL
# =====================================

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "GEST SPORT"
        }
    )

# =====================================
# ATHLETES
# =====================================

@app.get("/athletes")
async def athletes(
        request: Request,
        search: str = "",
        page: int = 1
):
    conn = get_connection()

    per_page = 10
    offset = (page - 1) * per_page

    query_count = """
        SELECT COUNT(*)
        FROM athletes a
        LEFT JOIN clubs c ON a.club_id = c.id
        WHERE
            a.nom LIKE ?
            OR a.prenom LIKE ?
            OR a.discipline LIKE ?
            OR a.province LIKE ?
    """

    search_param = f"%{search}%"

    total = conn.execute(
        query_count,
        (search_param, search_param, search_param, search_param)
    ).fetchone()[0]

    query = """
        SELECT
            a.*,
            c.nom AS club_nom
        FROM athletes a
        LEFT JOIN clubs c
            ON a.club_id = c.id
        WHERE
            a.nom LIKE ?
            OR a.prenom LIKE ?
            OR a.discipline LIKE ?
            OR a.province LIKE ?
        ORDER BY a.nom
        LIMIT ?
        OFFSET ?
    """

    athletes = conn.execute(
        query,
        (
            search_param,
            search_param,
            search_param,
            search_param,
            per_page,
            offset
        )
    ).fetchall()

    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        request=request,
        name="athletes.html",
        context={
            "title": "Athlètes",
            "athletes": athletes,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )