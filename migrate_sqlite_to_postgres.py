import os
import sqlite3
import psycopg2
from dotenv import load_dotenv

# Charge le fichier .env
load_dotenv()

SQLITE_DB = "database/sport.db"

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception(
        "La variable DATABASE_URL n'est pas définie dans le fichier .env"
    )

# =====================================================
# CONNEXIONS
# =====================================================

sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row

sqlite_cursor = sqlite_conn.cursor()

pg_conn = psycopg2.connect(DATABASE_URL)
pg_conn.autocommit = False
pg_cursor = pg_conn.cursor()

# =====================================================
# TYPES SQLITE -> POSTGRES
# =====================================================

def convert_type(t):

    if t is None:
        return "TEXT"

    t = t.upper()

    if "INT" in t:
        return "INTEGER"

    if "REAL" in t:
        return "DOUBLE PRECISION"

    if "FLOA" in t:
        return "DOUBLE PRECISION"

    if "DOUB" in t:
        return "DOUBLE PRECISION"

    if "NUMERIC" in t:
        return "NUMERIC"

    if "BOOL" in t:
        return "BOOLEAN"

    if "BLOB" in t:
        return "BYTEA"

    if "DATE" in t:
        return "DATE"

    if "TIME" in t:
        return "TIMESTAMP"

    return "TEXT"

# =====================================================
# TABLES SQLITE
# =====================================================

sqlite_cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
AND name NOT LIKE 'sqlite_%'
ORDER BY name
""")

tables = [r[0] for r in sqlite_cursor.fetchall()]

print()
print("=" * 60)
print("Tables détectées :")
print("=" * 60)

for t in tables:
    print("-", t)

print()

# =====================================================
# MIGRATION
# =====================================================

for table in tables:

    print("=" * 60)
    print("Migration :", table)
    print("=" * 60)

    # -----------------------------
    # Colonnes
    # -----------------------------

    sqlite_cursor.execute(f'PRAGMA table_info("{table}")')

    columns = sqlite_cursor.fetchall()

    defs = []

    pk = []

    for col in columns:

        cid = col[0]
        name = col[1]
        ctype = convert_type(col[2])
        notnull = col[3]
        default = col[4]
        primary = col[5]

        txt = f'"{name}" {ctype}'

        if notnull:
            txt += " NOT NULL"

        if default is not None:
            txt += f" DEFAULT {default}"

        defs.append(txt)

        if primary:
            pk.append(name)

    if pk:
        defs.append(
            "PRIMARY KEY ({})".format(
                ",".join(f'"{x}"' for x in pk)
            )
        )

    pg_cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')

    create_sql = f'''
    CREATE TABLE "{table}"(
        {",".join(defs)}
    )
    '''

    pg_cursor.execute(create_sql)

    # -----------------------------
    # Données
    # -----------------------------

    sqlite_cursor.execute(f'SELECT * FROM "{table}"')

    rows = sqlite_cursor.fetchall()

    if len(rows) == 0:
        print("0 ligne")
        continue

    colnames = rows[0].keys()

    cols = ",".join(
        f'"{c}"'
        for c in colnames
    )

    placeholders = ",".join(
        ["%s"] * len(colnames)
    )

    insert_sql = f'''
    INSERT INTO "{table}"
    ({cols})
    VALUES
    ({placeholders})
    '''

    for row in rows:

        values = []

        for c in colnames:

            value = row[c]

            # -----------------------------
            # Nettoyage des données
            # -----------------------------

            if isinstance(value, str):

                value = value.strip()

                # chaîne vide -> NULL
                if value == "":
                    value = None

            values.append(value)

        try:
            pg_cursor.execute(insert_sql, values)

        except Exception as e:

            print()
            print("Erreur dans la table :", table)
            print("Colonnes :", list(colnames))
            print("Valeurs  :", values)
            print("Erreur   :", e)
            print()

            raise

    print(len(rows), "lignes copiées")

# =====================================================
# REMISE A ZERO DES SEQUENCES
# =====================================================

print()
print("=" * 60)
print("Mise à jour des séquences")
print("=" * 60)

for table in tables:

    sqlite_cursor.execute(f'PRAGMA table_info("{table}")')

    cols = sqlite_cursor.fetchall()

    for c in cols:

        if c[5]:

            column = c[1]

            pg_cursor.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('"{table}"','{column}'),
                COALESCE(MAX("{column}"),1),
                TRUE
            )
            FROM "{table}"
            """)

pg_conn.commit()

sqlite_conn.close()
pg_conn.close()

print()
print("=" * 60)
print("MIGRATION TERMINÉE")
print("=" * 60)