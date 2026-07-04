import os
import shutil
import uuid
import folium

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
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    FileResponse
)
import matplotlib.pyplot as plt
from reportlab.platypus import Image
from folium.plugins import MarkerCluster



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

    # ==========================
    # EVOLUTION PAR ANNEE
    # ==========================

    evolution = conn.execute(
        """
        SELECT
            SUBSTR(date_creation,1,4) AS annee,
            COUNT(*) AS total
        FROM athletes
        WHERE date_creation IS NOT NULL
          AND date_creation != ''
        GROUP BY annee
        ORDER BY annee
        """
    ).fetchall()

    evolution_labels = [
        row["annee"]
        for row in evolution
    ]

    evolution_values = [
        row["total"]
        for row in evolution
    ]

    # ==========================
    # EVOLUTION CUMULATIVE
    # ==========================

    evolution_cumulative = []

    cumul = 0

    for row in evolution:
        cumul += row["total"]

        evolution_cumulative.append(cumul)

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
            "province_values": province_values,
            "evolution_labels": evolution_labels,
            "evolution_values": evolution_values
        }
    )

@app.get("/dashboard/pdf")
async def export_dashboard_pdf():

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
    # DISCIPLINES
    # ==========================

    disciplines = conn.execute(
        """
        SELECT discipline,
               COUNT(*) AS total
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

    # ==========================
    # PROVINCES
    # ==========================

    provinces = conn.execute(
        """
        SELECT province,
               COUNT(*) AS total
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

    # ==========================
    # EVOLUTION PAR ANNEE
    # ==========================

    evolution = conn.execute(
        """
        SELECT
            SUBSTR(date_creation,1,4) AS annee,
            COUNT(*) AS total
        FROM athletes
        WHERE date_creation IS NOT NULL
          AND date_creation != ''
        GROUP BY annee
        ORDER BY annee
        """
    ).fetchall()

    evolution_labels = [
        row["annee"]
        for row in evolution
    ]

    evolution_values = [
        row["total"]
        for row in evolution
    ]



    # =====================================
    # EFFECTIF CUMULATIF
    # =====================================

    evolution_cumulative = []

    cumul = 0

    for valeur in evolution_values:
        cumul += valeur

        evolution_cumulative.append(cumul)

    conn.close()

    # ==========================
    # CAMEMBERT HOMMES/FEMMES
    # ==========================

    plt.figure(figsize=(5, 5))

    plt.pie(
        [hommes, femmes],
        labels=["Hommes", "Femmes"],
        autopct="%1.1f%%"
    )

    plt.title("Répartition Hommes / Femmes")

    plt.savefig(
        "gender_chart.png",
        bbox_inches="tight"
    )

    plt.close()

    # ==========================
    # DISCIPLINES
    # ==========================

    if discipline_labels:

        plt.figure(figsize=(8, 4))

        plt.bar(
            discipline_labels,
            discipline_values
        )

        plt.title(
            "Athlètes par Discipline"
        )

        plt.xticks(rotation=45)

        plt.tight_layout()

        plt.savefig(
            "discipline_chart.png",
            bbox_inches="tight"
        )

        plt.close()

    # ==========================
    # PROVINCES
    # ==========================

    if province_labels:

        plt.figure(figsize=(8, 5))

        plt.barh(
            province_labels,
            province_values
        )

        plt.title(
            "Athlètes par Province"
        )

        plt.tight_layout()

        plt.savefig(
            "province_chart.png",
            bbox_inches="tight"
        )

        plt.close()

    # ==========================
    # NOUVEAUX ATHLETES / ANNEE
    # ==========================

    if evolution_labels:
        plt.figure(figsize=(8, 4))

        plt.plot(
            evolution_labels,
            evolution_values,
            marker="o",
            linewidth=3
        )

        plt.title(
            "Evolution annuelle des nouveaux athlètes"
        )

        plt.xlabel("Année")

        plt.ylabel("Nouveaux athlètes")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(
            "evolution_yearly_chart.png",
            bbox_inches="tight"
        )

        plt.close()

    # ==========================
    # EFFECTIF CUMULATIF
    # ==========================

    if evolution_labels:
        plt.figure(figsize=(8, 4))

        plt.plot(
            evolution_labels,
            evolution_cumulative,
            marker="o",
            linewidth=3
        )

        plt.title(
            "Evolution cumulative des effectifs"
        )

        plt.xlabel("Année")

        plt.ylabel("Effectif total")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(
            "evolution_cumulative_chart.png",
            bbox_inches="tight"
        )

        plt.close()

    # ==========================
    # PDF
    # ==========================

    pdf_file = "dashboard_report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "GEST SPORT - Rapport Dashboard",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            f"Nombre d'athlètes : <b>{nb_athletes}</b>",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Nombre de clubs : <b>{nb_clubs}</b>",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Nombre de ligues : <b>{nb_ligues}</b>",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Nombre de fédérations : <b>{nb_federations}</b>",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            f"Hommes : <b>{hommes}</b>",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Femmes : <b>{femmes}</b>",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # Camembert

    elements.append(
        Paragraph(
            "Répartition Hommes / Femmes",
            styles["Heading2"]
        )
    )

    elements.append(
        Image(
            "gender_chart.png",
            width=250,
            height=250
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # Discipline

    if discipline_labels:

        elements.append(
            Paragraph(
                "Athlètes par Discipline",
                styles["Heading2"]
            )
        )

        elements.append(
            Image(
                "discipline_chart.png",
                width=450,
                height=250
            )
        )

        elements.append(
            Spacer(1, 20)
        )

    # Province

    if province_labels:

        elements.append(
            Paragraph(
                "Athlètes par Province",
                styles["Heading2"]
            )
        )

        elements.append(
            Image(
                "province_chart.png",
                width=450,
                height=300
            )
        )

        # =====================================
        # EVOLUTION ANNUELLE
        # =====================================

        if evolution_labels:
            elements.append(
                Spacer(1, 20)
            )

            elements.append(
                Paragraph(
                    "Evolution annuelle des nouveaux athlètes",
                    styles["Heading2"]
                )
            )

            elements.append(
                Image(
                    "evolution_yearly_chart.png",
                    width=450,
                    height=250
                )
            )

        # =====================================
        # EVOLUTION CUMULATIVE
        # =====================================

        if evolution_labels:
            elements.append(
                Spacer(1, 20)
            )

            elements.append(
                Paragraph(
                    "Evolution cumulative des effectifs",
                    styles["Heading2"]
                )
            )

            elements.append(
                Image(
                    "evolution_cumulative_chart.png",
                    width=450,
                    height=250
                )
            )

    doc.build(elements)

    return FileResponse(
        pdf_file,
        filename="Dashboard_GEST_SPORT.pdf",
        media_type="application/pdf"
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
        date_creation: str = Form(""),

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

    # ==========================
    # DATE DE CREATION
    # ==========================

    date_creation = datetime.now().strftime(
        "%Y-%m-%d"
    )

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
            niveau,
            date_creation
        )

        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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
            niveau,
            date_creation
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
        date_creation: str = Form(""),

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
            niveau=?,
            date_creation=?

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
            date_creation,
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

@app.get("/carte")
async def carte_gabon():

    conn = get_connection()

    athletes = conn.execute(
        """
        SELECT
            nom,
            prenom,
            discipline,
            province,
            latitude,
            longitude
        FROM athletes
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        """
    ).fetchall()

    conn.close()

    import folium
    from folium.plugins import MarkerCluster

    gabon_map = folium.Map(
        location=[-0.7, 11.6],
        zoom_start=6
    )

    marker_cluster = MarkerCluster().add_to(
        gabon_map
    )

    for athlete in athletes:

        popup = f"""
        <b>{athlete['nom']} {athlete['prenom']}</b><br>
        Discipline : {athlete['discipline']}<br>
        Province : {athlete['province']}
        """

        folium.Marker(
            [
                athlete["latitude"],
                athlete["longitude"]
            ],
            popup=popup
        ).add_to(marker_cluster)

    map_file = "static/gabon_map.html"

    gabon_map.save(map_file)

    return FileResponse(map_file)