import asyncio
import flet as ft
from ai import ricetta
from Database import ottieni_prodotti, aggiorna_qta, salva_ricetta, db_ricette

ACCENT = ft.Colors.LIGHT_BLUE_200


def pagina_ricetta(page: ft.Page):
    page.title = "FridgeBuddy"

    def sezione(titolo: str, contenuto: ft.Control):
        return ft.Container(
            margin=ft.Margin.only(bottom=15),
            padding=16,
            bgcolor=ACCENT,
            border_radius=16,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(titolo, theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD),
                    contenuto,
                ],
            ),
        )

    testo_tipo_piatto = ft.TextField(
        adaptive=True,
        label="Es. Pasta, Riso, Secondo...",
        label_style=ft.TextStyle(color=ft.Colors.LIGHT_BLUE_700),
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
    )

    testo_allergie = ft.TextField(
        adaptive=True,
        label="Es. Lattosio, Frutta a guscio...",
        label_style=ft.TextStyle(color=ft.Colors.LIGHT_BLUE_700),
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
    )

    testo_persone = ft.Text("1", size=22, weight=ft.FontWeight.BOLD)

    def diminuisci(e):
        valore_attuale = int(testo_persone.value)
        if valore_attuale > 1:
            testo_persone.value = str(valore_attuale - 1)
            page.update()

    def aumenta(e):
        testo_persone.value = str(int(testo_persone.value) + 1)
        page.update()

    counter = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=ft.Colors.LIGHT_BLUE_700, on_click=diminuisci),
            testo_persone,
            ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ft.Colors.LIGHT_BLUE_700, on_click=aumenta),
        ],
    )

    testo_tempo = ft.Text("Tempo massimo: 30 minuti", size=14, weight=ft.FontWeight.W_500)

    def aggiorna_tempo(e):
        testo_tempo.value = f"Tempo massimo: {int(slider_tempo.value)} minuti"
        page.update()

    slider_tempo = ft.Slider(
        min=5, max=120, divisions=23, value=30,
        label="{value} min",
        active_color=ft.Colors.LIGHT_BLUE_700,
        on_change=aggiorna_tempo,
    )

    tipi_diete = ["Vegana", "Vegetariana", "Celiaca", "Senza Lattosio", "Chetogenica"]
    checkbox_diete = [
        ft.Checkbox(label=dieta, value=False, active_color=ft.Colors.LIGHT_BLUE_700)
        for dieta in tipi_diete
    ]

    contenitore_ricetta = ft.Markdown(selectable=True)
    contenitore_dialog = ft.Container()

    report_scarico_corrente = []
    dati_ricetta_corrente = {"titolo": None, "testo": None}

    def scarica_prodotti(e):
        prodotti_attuali = ottieni_prodotti()

        for elemento in report_scarico_corrente:
            nome_elem = elemento.get("nome")
            qta_usata = elemento.get("qta_usata", 0)

            prod_trovato = next(
                (p for p in prodotti_attuali if p["nome"].lower().strip() == (nome_elem or "").lower().strip()),
                None,
            )

            if prod_trovato:
                nuova_qta = prod_trovato["qta"] - qta_usata
                if isinstance(prod_trovato["qta"], int):
                    nuova_qta = int(round(nuova_qta))
                aggiorna_qta(id_prodotto=prod_trovato["id"], nuova_qta=max(0, nuova_qta))

        bottone_scarica.disabled = True
        bottone_scarica.text = "Dispensa aggiornata"
        page.update()

    bottone_scarica = ft.ElevatedButton(
        "Conferma e togli dalla dispensa", icon=ft.Icons.CHECK,
        bgcolor=ft.Colors.LIGHT_BLUE_600, color=ft.Colors.WHITE,
        on_click=scarica_prodotti, visible=False,
    )

    def salvataggio(e):
        db_ricette()
        titolo = dati_ricetta_corrente["titolo"]
        testo = dati_ricetta_corrente["testo"]

        if titolo and testo:
            salva_ricetta(titolo, testo, report_scarico_corrente)
            bottone_salva.disabled = True
            page.update()

    bottone_salva = ft.ElevatedButton(
        "Salva ricetta", icon=ft.Icons.BOOKMARK_BORDER,
        bgcolor=ft.Colors.LIGHT_BLUE_600, color=ft.Colors.WHITE,
        on_click=salvataggio, disabled=True,
    )

    def chiudi_dialog(e):
        dialog_ricetta.open = False
        page.update()

    dialog_ricetta = ft.AlertDialog(
        title=ft.Row(controls=[
            ft.Icon(ft.Icons.RESTAURANT_MENU, color=ft.Colors.LIGHT_BLUE_700),
            ft.Text("La tua ricetta", weight=ft.FontWeight.BOLD),
        ]),
        content=contenitore_dialog,
        actions=[ft.TextButton("Chiudi", on_click=chiudi_dialog)],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    async def genera(e):
        nonlocal report_scarico_corrente
        report_scarico_corrente = []
        dati_ricetta_corrente["titolo"] = None
        dati_ricetta_corrente["testo"] = None

        bottone_scarica.visible = False
        bottone_scarica.disabled = False
        bottone_salva.disabled = True

        larghezza_schermo = page.width if page.width else 400
        altezza_schermo = page.height if page.height else 600

        contenitore_dialog.width = min(larghezza_schermo * 0.85, 550)
        contenitore_dialog.height = altezza_schermo * 0.65

        contenitore_dialog.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[ft.ProgressRing(), ft.Text("Generazione ricetta in corso...", size=16)],
        )

        if dialog_ricetta not in page.overlay:
            page.overlay.append(dialog_ricetta)

        dialog_ricetta.open = True
        bottone_genera.disabled = True

        page.update()
        await asyncio.sleep(0.1)

        try:
            diete = [cb.label for cb in checkbox_diete if cb.value]
            stringa_dieta = ", ".join(diete)

            tipo_piatto = testo_tipo_piatto.value or "Qualsiasi"
            allergie = testo_allergie.value or ""

            numero_persone = int(testo_persone.value)
            tempo = int(slider_tempo.value)

            prodotti = ottieni_prodotti()

            lista_cibi_dispensa = [
                f"{p['nome']} (Qtà: {p['qta']}, Scadenza: {p['scadenza']})" for p in prodotti
            ]

            titolo_risposta, risposta_testo, report_scarico = await asyncio.to_thread(
                ricetta,
                lista_cibi=lista_cibi_dispensa,
                persone=numero_persone,
                tempo=tempo,
                dieta=stringa_dieta,
                tipo=tipo_piatto,
                allergie=allergie,
                prodotti_dispensa=prodotti,
            )

            contenitore_ricetta.value = risposta_testo
            report_scarico_corrente = report_scarico

            if titolo_risposta and "Non è possibile creare" not in risposta_testo:
                dati_ricetta_corrente["titolo"] = titolo_risposta or "Ricetta Personalizzata"
                dati_ricetta_corrente["testo"] = risposta_testo
                bottone_salva.disabled = False
            else:
                bottone_salva.disabled = True

            azioni_dialog = []
            if report_scarico_corrente:
                bottone_scarica.visible = True
                azioni_dialog.append(bottone_scarica)

            azioni_dialog.append(bottone_salva)
            azioni_dialog.append(ft.TextButton("Chiudi", on_click=chiudi_dialog))

            dialog_ricetta.actions = azioni_dialog

        except Exception as err:
            contenitore_ricetta.value = f"Errore durante la generazione della ricetta:\n{err}"
            bottone_salva.disabled = True
            dialog_ricetta.actions = [ft.TextButton("Chiudi", on_click=chiudi_dialog)]

        finally:
            contenitore_dialog.content = ft.Column(
                controls=[
                    contenitore_ricetta,
                    ft.Text("L'IA può commettere errori", weight=ft.FontWeight.W_200),
                ],
                scroll=ft.ScrollMode.AUTO,
            )
            bottone_genera.disabled = False
            page.update()

    bottone_genera = ft.ElevatedButton(
        content=ft.Text("Genera ricetta", size=17, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.LIGHT_BLUE_600,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14), padding=18),
        on_click=genera,
    )

    header = ft.Container(
        padding=ft.Padding.only(top=15, bottom=5),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.RESTAURANT_MENU_OUTLINED, size=24, color=ft.Colors.LIGHT_BLUE_700),
                ft.Text("Imposta la tua ricetta", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, size=24, text_align=ft.TextAlign.CENTER),
            ],
        ),
    )

    return ft.SafeArea(
        expand=True,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                header,

                sezione("Tipo di piatto", testo_tipo_piatto),
                sezione("Numero di persone", counter),
                sezione("Tempo di preparazione", ft.Column(spacing=5, controls=[testo_tempo, slider_tempo])),
                sezione("Dieta", ft.Column(spacing=2, controls=checkbox_diete)),
                sezione("Allergie", testo_allergie),

                bottone_genera,
            ],
        ),
    )