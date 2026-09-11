import sqlite3
import json
import os
from datetime import datetime, timedelta


def _percorso_db() -> str:
    base_dir = os.getenv("FLET_APP_STORAGE_DATA", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "dispensa.db")





def inizializza_db():
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prodotti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            qta INTEGER DEFAULT 1,
            data_inserimento TEXT NOT NULL,
            data_scadenza TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ricette_salvate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo TEXT NOT NULL,
            testo_ricetta TEXT NOT NULL,
            report_scarico TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE ricette_salvate ADD COLUMN report_scarico TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def inserisci_manuale(nome, data_scadenza, qta):
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()

    data_oggi = datetime.now().strftime("%Y-%m-%d")

    try:
        if "/" in data_scadenza:
            dt = datetime.strptime(data_scadenza, "%d/%m/%Y")
        elif "-" in data_scadenza and len(data_scadenza.split("-")[0]) == 2:
            dt = datetime.strptime(data_scadenza, "%d-%m-%Y")
        else:
            dt = datetime.strptime(data_scadenza, "%Y-%m-%d")

        scadenza_iso = dt.strftime("%Y-%m-%d")
    except ValueError:
        scadenza_iso = data_scadenza

    cursor.execute("""
        INSERT INTO prodotti (nome, qta, data_inserimento, data_scadenza)
        VALUES (?, ?, ?, ?)
    """, (nome, qta, data_oggi, scadenza_iso))

    conn.commit()
    conn.close()


def inserisci_scontrino(nome, giorni_durata, qta=1, data_scadenza=None):
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()

    oggi = datetime.now()
    data_inserimento = oggi.strftime("%Y-%m-%d")

    if data_scadenza:
        data_scadenza_finale = data_scadenza
    else:
        data_scadenza_finale = (oggi + timedelta(days=giorni_durata)).strftime("%Y-%m-%d")

    cursor.execute("""
        INSERT INTO prodotti (nome, qta, data_inserimento, data_scadenza)
        VALUES (?, ?, ?, ?)
    """, (nome, qta, data_inserimento, data_scadenza_finale))

    conn.commit()
    conn.close()


def ottieni_prodotti():
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, qta, data_scadenza FROM prodotti ORDER BY data_scadenza ASC")
    righe = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "nome": r[1], "qta": r[2], "scadenza": r[3]} for r in righe]


def ottieni_3_prodotti():
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, qta, data_scadenza FROM prodotti ORDER BY data_scadenza ASC LIMIT 3")
    righe_3Prod = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "nome": r[1], "qta": r[2], "scadenza": r[3]} for r in righe_3Prod]


def elimina(id_prodotto):
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()

    cursor.execute("DELETE FROM prodotti WHERE id=?", (id_prodotto,))

    conn.commit()
    conn.close()


def aggiorna_qta(id_prodotto, nuova_qta):
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()

    if nuova_qta <= 0:
        cursor.execute("DELETE FROM prodotti WHERE id=?", (id_prodotto,))
    else:
        cursor.execute(
            "UPDATE prodotti SET qta=? WHERE id=?", (nuova_qta, id_prodotto)
        )

    conn.commit()
    conn.close()


def db_ricette():
    inizializza_db()


def salva_ricetta(titolo: str, testo_ricetta: str, report_scarico: list = None):
    inizializza_db()

    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()

    report_json = json.dumps(report_scarico) if report_scarico else None

    cursor.execute(
        "INSERT INTO ricette_salvate (titolo, testo_ricetta, report_scarico) VALUES (?, ?, ?)",
        (titolo, testo_ricetta, report_json)
    )
    conn.commit()
    conn.close()


def ottieni_ricette():
    inizializza_db()

    conn = sqlite3.connect(_percorso_db())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ricette_salvate ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    ricette = []
    for row in rows:
        r = dict(row)
        if r.get("report_scarico"):
            try:
                r["report_scarico"] = json.loads(r["report_scarico"])
            except Exception:
                r["report_scarico"] = []
        else:
            r["report_scarico"] = []
        ricette.append(r)

    return ricette


def elimina_ricetta(id_ricetta: int):
    conn = sqlite3.connect(_percorso_db())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ricette_salvate WHERE id=?", (id_ricetta,))
    conn.commit()
    conn.close()


def ricetta_realizzabile(report_scarico: list) -> bool:
    if not report_scarico:
        return True

    prodotti_db = ottieni_prodotti()

    for item in report_scarico:
        nome_ricercato = item.get("nome")
        qta_necessaria = item.get("qta_usata", 0)

        if not nome_ricercato:
            continue

        prod_trovato = next(
            (p for p in prodotti_db if p["nome"].lower().strip() == nome_ricercato.lower().strip()),
            None
        )

        if not prod_trovato or prod_trovato["qta"] < qta_necessaria:
            return False
    return True