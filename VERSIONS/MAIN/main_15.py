import os
import shutil
import uuid

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database.db import get_connection
from fastapi import Form
from fastapi.responses import RedirectResponse
from fastapi import (
    Request,
    Form,
    UploadFile,
    File
)



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
        page: int = 1,
        success: str = ""
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
            "total_pages": total_pages,
            "success": success
        }
    )

@app.get("/clubs")
async def clubs(
        request: Request,
        search: str = "",
        page: int = 1
):
    conn = get_connection()

    per_page = 10
    offset = (page - 1) * per_page

    search_param = f"%{search}%"

    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM clubs
        WHERE
            nom LIKE ?
            OR discipline LIKE ?
            OR province LIKE ?
            OR ville LIKE ?
        """,
        (
            search_param,
            search_param,
            search_param,
            search_param
        )
    ).fetchone()[0]

    clubs = conn.execute(
        """
        SELECT
            c.*,
            COUNT(a.id) AS nb_athletes

        FROM clubs c

        LEFT JOIN athletes a
            ON a.club_id = c.id

        WHERE
            c.nom LIKE ?
            OR c.discipline LIKE ?
            OR c.province LIKE ?
            OR c.ville LIKE ?

        GROUP BY c.id

        ORDER BY c.nom

        LIMIT ?
        OFFSET ?
        """,
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
        name="clubs.html",
        context={
            "title": "Clubs",
            "clubs": clubs,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )

@app.get("/dashboard")
async def dashboard(request: Request):

    conn = get_connection()

    nb_athletes = conn.execute(
        "SELECT COUNT(*) FROM athletes"
    ).fetchone()[0]

    nb_clubs = conn.execute(
        "SELECT COUNT(*) FROM clubs"
    ).fetchone()[0]

    nb_ligues = conn.execute(
        "SELECT COUNT(*) FROM ligues"
    ).fetchone()[0]

    nb_federations = conn.execute(
        "SELECT COUNT(*) FROM federations"
    ).fetchone()[0]

    hommes = conn.execute(
        """
        SELECT COUNT(*)
        FROM athletes
        WHERE sexe='H'
        """
    ).fetchone()[0]

    femmes = conn.execute(
        """
        SELECT COUNT(*)
        FROM athletes
        WHERE sexe='F'
        """
    ).fetchone()[0]



    # ==========================
    # PROVINCES
    # ==========================

    provinces = conn.execute(
        """
        SELECT
            province,
            COUNT(*) as total
        FROM athletes
        GROUP BY province
        ORDER BY total DESC
        """
    ).fetchall()

    province_labels = [
        row["province"]
        for row in provinces
    ]

    province_values = [
        row["total"]
        for row in provinces
    ]

    # =====================================
    # ATHLETES PAR DISCIPLINE
    # =====================================

    disciplines = conn.execute(
        """
        SELECT
            discipline,
            COUNT(*) as total
        FROM athletes
        GROUP BY discipline
        ORDER BY total DESC
        """
    ).fetchall()

    discipline_labels = [
        row["discipline"]
        for row in disciplines
    ]

    discipline_values = [
        row["total"]
        for row in disciplines
    ]

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "Dashboard",
            "nb_athletes": nb_athletes,
            "nb_clubs": nb_clubs,
            "nb_ligues": nb_ligues,
            "nb_federations": nb_federations,
            "hommes": hommes,
            "femmes": femmes,
            "discipline_labels": discipline_labels,
            "discipline_values": discipline_values,
            "province_labels": province_labels,
            "province_values": province_values
        }
    )

@app.get("/ligues")
async def ligues(
        request: Request,
        search: str = "",
        page: int = 1
):

    conn = get_connection()

    per_page = 10
    offset = (page - 1) * per_page

    search_param = f"%{search}%"

    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM ligues
        WHERE
            nom LIKE ?
            OR discipline LIKE ?
            OR province LIKE ?
        """,
        (
            search_param,
            search_param,
            search_param
        )
    ).fetchone()[0]

    ligues = conn.execute(
        """
        SELECT
            l.*,
            COUNT(c.id) AS nb_clubs

        FROM ligues l

        LEFT JOIN clubs c
            ON c.ligue_id = l.id

        WHERE
            l.nom LIKE ?
            OR l.discipline LIKE ?
            OR l.province LIKE ?

        GROUP BY l.id

        ORDER BY l.nom

        LIMIT ?
        OFFSET ?
        """,
        (
            search_param,
            search_param,
            search_param,
            per_page,
            offset
        )
    ).fetchall()

    # =====================================
    # ATHLETES PAR PROVINCE
    # =====================================

    provinces = conn.execute(
        """
        SELECT
            province,
            COUNT(*) as total
        FROM athletes
        GROUP BY province
        ORDER BY total DESC
        """
    ).fetchall()

    province_labels = [
        row["province"]
        for row in provinces
    ]

    province_values = [
        row["total"]
        for row in provinces
    ]

    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        request=request,
        name="ligues.html",
        context={
            "title": "Ligues",
            "ligues": ligues,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )

@app.get("/federations")
async def federations(
        request: Request,
        search: str = "",
        page: int = 1
):

    conn = get_connection()

    per_page = 10
    offset = (page - 1) * per_page

    search_param = f"%{search}%"

    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM federations
        WHERE
            nom LIKE ?
            OR discipline LIKE ?
            OR province LIKE ?
        """,
        (
            search_param,
            search_param,
            search_param
        )
    ).fetchone()[0]

    federations = conn.execute(
        """
        SELECT
            f.*,
            COUNT(DISTINCT c.id) AS nb_clubs,
            COUNT(DISTINCT a.id) AS nb_athletes

        FROM federations f

        LEFT JOIN clubs c
            ON c.federation_id = f.id

        LEFT JOIN athletes a
            ON a.club_id = c.id

        WHERE
            f.nom LIKE ?
            OR f.discipline LIKE ?
            OR f.province LIKE ?

        GROUP BY f.id

        ORDER BY f.nom

        LIMIT ?
        OFFSET ?
        """,
        (
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
        name="federations.html",
        context={
            "title": "Fédérations",
            "federations": federations,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )

@app.get("/athletes/new")
async def new_athlete(request: Request):

    conn = get_connection()

    clubs = conn.execute("""
        SELECT id, nom
        FROM clubs
        ORDER BY nom
    """).fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="athlete_form.html",
        context={
            "title": "Nouvel Athlète",
            "clubs": clubs,
            "athlete": None
        }
    )

@app.post("/athletes/new")
async def create_athlete(

        nom: str = Form(...),
        prenom: str = Form(...),
        sexe: str = Form(...),
        discipline: str = Form(...),
        categorie: str = Form(""),
        club_id: int = Form(...),
        province: str = Form(...),
        date_naissance: str = Form(""),
        niveau: str = Form(""),

        photo: UploadFile = File(None)

):

    photo_path = "photos/default.png"

    if photo and photo.filename:

        os.makedirs(
            "static/photos",
            exist_ok=True
        )

        extension = os.path.splitext(
            photo.filename
        )[1]

        filename = f"{uuid.uuid4()}{extension}"

        save_path = os.path.join(
            "static",
            "photos",
            filename
        )

        with open(save_path, "wb") as buffer:

            shutil.copyfileobj(
                photo.file,
                buffer
            )

        photo_path = f"photos/{filename}"

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO athletes
        (
            nom,
            prenom,
            sexe,
            discipline,
            categorie,
            club_id,
            province,
            photo,
            date_naissance,
            niveau
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            nom,
            prenom,
            sexe,
            discipline,
            categorie,
            club_id,
            province,
            photo_path,
            date_naissance,
            niveau
        )
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url="/athletes?success=added",
        status_code=303
    )

@app.get("/athletes/edit/{athlete_id}")
async def edit_athlete(
        request: Request,
        athlete_id: int
):

    conn = get_connection()

    athlete = conn.execute(
        """
        SELECT *
        FROM athletes
        WHERE id = ?
        """,
        (athlete_id,)
    ).fetchone()

    clubs = conn.execute(
        """
        SELECT id, nom
        FROM clubs
        ORDER BY nom
        """
    ).fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="athlete_form.html",
        context={
            "title": "Modifier Athlète",
            "athlete": athlete,
            "clubs": clubs
        }
    )

@app.post("/athletes/edit/{athlete_id}")
async def update_athlete(

        athlete_id: int,

        nom: str = Form(...),
        prenom: str = Form(...),
        sexe: str = Form(...),
        discipline: str = Form(...),
        categorie: str = Form(""),
        club_id: int = Form(...),
        province: str = Form(...),
        date_naissance: str = Form(""),
        niveau: str = Form(""),

        photo: UploadFile = File(None)

):

    conn = get_connection()

    athlete = conn.execute(
        """
        SELECT *
        FROM athletes
        WHERE id = ?
        """,
        (athlete_id,)
    ).fetchone()

    photo_path = athlete["photo"]

    if photo and photo.filename:

        os.makedirs(
            "static/photos",
            exist_ok=True
        )

        extension = os.path.splitext(
            photo.filename
        )[1]

        filename = f"{uuid.uuid4()}{extension}"

        save_path = os.path.join(
            "static",
            "photos",
            filename
        )

        old_photo = athlete["photo"]

        if (
            old_photo
            and old_photo != "photos/default.png"
        ):

            old_file = os.path.join(
                "static",
                old_photo.replace("\\", "/")
            )

            if os.path.exists(old_file):
                os.remove(old_file)

        with open(save_path, "wb") as buffer:

            shutil.copyfileobj(
                photo.file,
                buffer
            )

        photo_path = f"photos/{filename}"

    conn.execute(
        """
        UPDATE athletes

        SET
            nom=?,
            prenom=?,
            sexe=?,
            discipline=?,
            categorie=?,
            club_id=?,
            province=?,
            photo=?,
            date_naissance=?,
            niveau=?

        WHERE id=?
        """,
        (
            nom,
            prenom,
            sexe,
            discipline,
            categorie,
            club_id,
            province,
            photo_path,
            date_naissance,
            niveau,
            athlete_id
        )
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url="/athletes?success=updated",
        status_code=303
    )

@app.post("/athletes/delete/{athlete_id}")
async def delete_athlete(athlete_id: int):

    conn = get_connection()

    athlete = conn.execute(
        """
        SELECT photo
        FROM athletes
        WHERE id = ?
        """,
        (athlete_id,)
    ).fetchone()

    if athlete:

        photo = athlete["photo"]

        if (
            photo
            and photo != "photos/default.png"
        ):

            file_path = os.path.join(
                "static",
                photo.replace("\\", "/")
            )

            if os.path.exists(file_path):
                os.remove(file_path)

    conn.execute(
        """
        DELETE FROM athletes
        WHERE id = ?
        """,
        (athlete_id,)
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url="/athletes?success=deleted",
        status_code=303
    )