# FridgeBuddy

**FridgeBuddy** è un'app che ti aiuta a gestire la tua dispensa in modo intelligente, sfruttando l'intelligenza artificiale per tenere traccia dei prodotti, suggerire ricette e ridurre gli sprechi alimentari.

## Funzionalità

- **Gestione dispensa**: aggiungi, modifica e tieni traccia dei prodotti che hai in casa
- **Scansione scontrini**: fotografa lo scontrino della spesa e aggiungi automaticamente i prodotti acquistati alla dispensa
- **Ricette basate sull'IA**: genera ricette personalizzate a partire dagli ingredienti disponibili in dispensa
- **Ricette salvate**: salva le tue ricette preferite per ritrovarle facilmente
- **Impostazioni personalizzabili**: configura l'app secondo le tue preferenze

## Stack tecnologico

- **[Flet](https://flet.dev/)** (`0.86.5`) — framework Python per creare app multipiattaforma (Android, iOS, desktop) con un'unica codebase
- **flet-camera** — accesso alla fotocamera del dispositivo per fotografare scontrini e prodotti
- **[Google Gen AI](https://ai.google.dev/)** (`google-genai`) — motore IA per il riconoscimento degli scontrini/prodotti e la generazione delle ricette
- **Pydantic** — validazione e gestione dei dati
- **Pillow** — elaborazione delle immagini

## Requisiti

- Una chiave API di Google Gen AI (Gemini)

## Download

Per il download su Android, aprire la cartella build e scaricare il file: "FridgeBuddy.apk"

## Struttura del progetto

| File | Descrizione |
|---|---|
| `Home.py` | Entry point dell'applicazione |
| `Dispensa.py` | Gestione della dispensa (elenco prodotti) |
| `Carica_Scontrino.py` | Scansione e caricamento degli scontrini |
| `Ricetta.py` | Generazione ricette tramite IA |
| `Ricette_salvate.py` | Gestione delle ricette salvate |
| `Impostazioni.py` | Impostazioni dell'app |
| `Database.py` | Gestione della persistenza dei dati |
| `ai.py` | Logica di integrazione con l'IA (Google Gen AI) |
| `Theme.conf` | Configurazione del tema grafico |

## Licenza

Coperto da proprietà intellettuale.

---

Realizzato con usando [Flet](https://flet.dev/) e Google Gen AI.


# FridgeBuddy

**FridgeBuddy** is an app that helps you manage your pantry smartly, using artificial intelligence to track your products, suggest recipes, and reduce food waste.

## Features

- **Pantry management**: add, edit, and keep track of the products you have at home
- **Receipt scanning**: take a photo of your grocery receipt and automatically add purchased items to your pantry
- **AI-powered recipes**: generate personalized recipes based on the ingredients available in your pantry
- **Saved recipes**: save your favorite recipes for easy access later
- **Customizable settings**: configure the app to your preferences

## Tech stack

- **[Flet](https://flet.dev/)** (`0.86.5`) — Python framework for building cross-platform apps (Android, iOS, desktop) from a single codebase
- **flet-camera** — access to the device camera to photograph receipts and products
- **[Google Gen AI](https://ai.google.dev/)** (`google-genai`) — AI engine for receipt/product recognition and recipe generation
- **Pydantic** — data validation and management
- **Pillow** — image processing

## Requirements

- A Google Gen AI (Gemini) API key

## Download

For the Android download, open the build folder and download the file: “FridgeBuddy.apk”.

## Project structure

| File | Description |
|---|---|
| `Home.py` | Application entry point |
| `Dispensa.py` | Pantry management (product list) |
| `Carica_Scontrino.py` | Receipt scanning and upload |
| `Ricetta.py` | AI-powered recipe generation |
| `Ricette_salvate.py` | Saved recipes management |
| `Impostazioni.py` | App settings |
| `Database.py` | Data persistence management |
| `ai.py` | AI integration logic (Google Gen AI) |
| `Theme.conf` | Theme/graphic configuration |

## License

Copyright © 2026 FridgeBuddy. All rights reserved.

---

Built with using [Flet](https://flet.dev/) and Google Gen AI.
