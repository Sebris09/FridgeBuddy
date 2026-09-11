import configparser
import json
import os
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field

def _ottieni_api_key() -> str:
    base_dir = os.getenv("FLET_APP_STORAGE_DATA", os.path.dirname(os.path.abspath(__file__)))
    api_conf_path = os.path.join(base_dir, "Api.conf")

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(api_conf_path)
    return config.get("Api", "Api", fallback="")


class Prodotto(BaseModel):
    nome: str
    qta: int
    g_durata: int = Field(
        description="Stima dei giorni mancanti alla scadenza. Usala SOLO se non hai trovato una data leggibile sulla confezione."
    )
    data_scadenza_letta: str = Field(
        default="",
        description="Se sulla confezione è stampata una data di scadenza leggibile, riportala QUI ESATTAMENTE nel formato AAAA-MM-GG (es. 2026-12-31). Se non è visibile o leggibile, lascia questo campo come stringa vuota."
    )


class Risultato(BaseModel):
    prodotti: list[Prodotto]


class IngredienteUsato(BaseModel):
    nome_dispensa: str = Field(
        description="Nome dell'ingrediente esattamente come appariva nella dispensa"
    )
    quantita_usata: float = Field(
        description="""
        Quantità consumata. 
        REGOLE FONDAMENTALI:
        - Se nel nome o valore del prodotto in dispensa si evince che la quantità è in grammi/ml (es. Pasta qta: 500), restituisci i GRAMMI usati per la ricetta (es. 80 o 100).
        - Se il prodotto è conteggiato a pezzi/unità (es. Uova qta: 6, Limone qta: 2, Scatoletta qta: 1), restituisci il NUMERO DI PEZZI usati (es. 1 o 2).
        """
    )


class RispostaRicetta(BaseModel):
    possibile: bool = Field(description="True se è stato possibile creare la ricetta, False se mancava l'alimento base richiesto")
    titolo: str
    testo_ricetta: str = Field(description="Testo completo della ricetta formattato oppure messaggio di errore")
    ingredienti_usati: list[IngredienteUsato] = Field(description="Lista dei soli ingredienti usati presi dalla dispensa")


def analisi(percorso: str):
    client = genai.Client(api_key=_ottieni_api_key())
    immagine = Image.open(percorso)

    oggi = datetime.now().strftime("%d/%m/%Y")

    istruzioni = f"""
    Oggi è il {oggi}. Usa questa data come riferimento per qualsiasi calcolo o deduzione temporale.

    Analizza la foto:

    SCONTRINO
    -Se è uno scontrino leggi tutti i prodotti alimentari, escludendo olio, burro, sale, pepe e acqua.
    -Rendi capibili i nomi non chiari (per esempio "LTT FRSC" diventa "Latte fresco", o "YOGURT FR" diventa "Yogurt Fragola")
    -Inserisci la quantità nel campo apposito 'qta'.
    -Sugli scontrini la data di scadenza quasi mai è stampata: lascia 'data_scadenza_letta' vuoto e stima i giorni in 'g_durata' secondo questi criteri:
        Carne/Pesce freschi: 3
        Latticini: 5/6
        Frutta o verdura: 7
        Cibo in scatola/Pasta/Riso/Surgelati: 180

    FOTO PRODOTTI:
    -Se nella foto si vedono direttamente i prodotti (non uno scontrino), osserva ciascun prodotto e dagli un nome capibile. Ignora olio, burro, sale, pepe e acqua.
    -Inserisci la quantità nel campo apposito 'qta'.
    -Cerca sulla confezione una scritta tipo "Scad." o "Da consumarsi entro" con una data leggibile:
        - Se la trovi ed è leggibile, trascrivila ESATTAMENTE, senza fare alcun calcolo, nel campo 'data_scadenza_letta' in formato AAAA-MM-GG. Se sulla confezione manca l'anno, usa il primo anno futuro compatibile con la data di oggi.
        - Se NON è leggibile o non è presente, lascia 'data_scadenza_letta' vuoto e stima i giorni mancanti in 'g_durata' secondo questi criteri:
            Carne/Pesce freschi: 3
            Latticini: 5/6
            Frutta o verdura: 7
            Cibo in scatola/Pasta/Riso/Surgelati: 180

    IMPORTANTE: non provare mai a calcolare tu quanti giorni mancano da una data letta, riporta solo la data così com'è scritta sulla confezione.
    """

    risposta = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[immagine, istruzioni],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Risultato,
        ),
    )
    return risposta.text


def ricetta(lista_cibi: list[str], persone: int, tempo: int, dieta: str, tipo: str, allergie: str, prodotti_dispensa: list[dict]):

    client = genai.Client(api_key=_ottieni_api_key())
    ingredienti = ", ".join(lista_cibi)

    prompt = f"""
    Sei uno chef. Hai questi ingredienti a disposizione: {ingredienti}.

    Devi rispettare queste regole TASSATIVAMENTE:

    1.  Tipo di piatto ("{tipo}"):
        -se è specificato un tipo (es Pasta, Riso, Secondo) e hai in dispensa l'ingrediente base (es hai la pasta e l'utente richiede Pasta), devi OBBLIGATORIAMENTE creare una ricetta, anche se semplice (es pasta in bianco).
        -SOLO se manca del tutto l'alimento base (es l'utente chiede il riso ma in dispensa NON c'è il riso), rispondi UNICAMENTE con la frase:
         "Non è possibile creare la ricetta selezionata con i prodotti nella dispensa"
        -Se il tipo è "Qualsiasi", proponi la miglior ricetta con quello che hai.

    2.  Ingredienti base di casa:
        -Puoi dare SEMPRE per scontato l'uso di: olio d'oliva, sale, pepe, acqua e burro.

    3.  Scadenze e dosi:
        -Usa prima i prodotti che scadono prima.
        -Calcola le dosi per {persone} persone.
        -La preparazione deve richiedere massimo {tempo} minuti.
    
    4.  Restrizioni alimentari
        -Dieta richiesta: "{dieta if dieta else 'Nessuna'}".
        -Allergie da EVITARE ASSOLUTAMENTE: "{allergie if allergie else 'Nessuna'}".
        -ATTENZIONE AGLI INGREDIENTI NASCOSTI: Devi analizzare anche la composizione dei prodotti pronti o derivati!
         (Esempi: se l'utente è allergico ai PINOLI, NON puoi usare il pesto...)

    5. Gestione Smart delle Quantità da scaricare:
       - Analizza il valore di 'qta' e il nome del prodotto per capire come è salvato nel DB:
         a) Prodotti a PESO/VOLUME (es. Pasta, Riso, Farina, Latte con qta grandi come 200, 500, 1000): 
            Nel campo 'quantita_usata' indica i GRAMMI/ML effettivi usati (es. 80 per 80g di pasta).
         b) Prodotti a PEZZI/UNITÀ (es. Uova, Mele, Mozzarella, Scatolette con qta piccole come 1, 2, 6): 
            Nel campo 'quantita_usata' indica il NUMERO DI PEZZI usati (es. 1 per 1 uovo).
         
    Struttura della risposta:
    -Nome del piatto (es. "Pasta al pomodoro per {persone} persone", se {persone}=1 allora "Pasta al pomodoro per 1 persona"), non dare nomi particolari ai piatti.
    -Lista degli ingredienti con le dosi corrette.
    -Preparazione dettagliata passo dopo passo, tutti i passi devono essere divisi e numerati.
    -Non aggiungere frasi oltre al nome del piatto, alla lista degli ingredienti e alla preparazione.
    Queste sezioni devono essere divise tra di loro per rendere il tutto il più leggibile possibili.
    Le sezioni devono essere: Nome del piatto, Lista degli ingredienti, Preparazione passo passo.
    I titoli delle sezioni mettili in grassetto

    Struttura del campo testo_ricetta:
    Utilizza la sintassi Markdown con a capo formattati correttamente (usa due a capo tra i blocchi):

    **Nome del piatto**
    [Nome del piatto per X persone]

    **Ingredienti:**
    - Ingrediente 1: dose
    - Ingrediente 2: dose

    **Preparazione:**
    1. Primo passaggio...
    2. Secondo passaggio...

    DIVIETO ASSOLUTO: Non usare tag HTML come <b> o <br>. Usa solo sintassi Markdown.
    """

    risposta = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RispostaRicetta,
        ),
    )

    if hasattr(risposta, "parsed") and risposta.parsed:
        dati = risposta.parsed
    else:
        dati = RispostaRicetta.model_validate_json(risposta.text)

    if not dati.possibile:
        return None, dati.testo_ricetta, []

    report_scarico = []
    for ing in dati.ingredienti_usati:
        for prod in prodotti_dispensa:
            if prod["nome"].lower() in ing.nome_dispensa.lower() or ing.nome_dispensa.lower() in prod["nome"].lower():
                report_scarico.append({
                    "id": prod["id"],
                    "nome": prod["nome"],
                    "qta_usata": ing.quantita_usata
                })
                break

    return dati.titolo, dati.testo_ricetta, report_scarico
