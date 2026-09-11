import flet as ft
from Database import ottieni_ricette, elimina_ricetta, db_ricette, aggiorna_qta, ottieni_prodotti

ACCENT = ft.Colors.LIGHT_BLUE_200


def ricette_salvate(page: ft.Page):
    page.title = "FridgeBuddy"

    db_ricette()

    contenitore_ricetta = ft.Markdown(selectable=True)
    report_scarico_corrente = []

    def scarica(e):
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
        page.update()
        ricarica_lista()

    bottone_scarica = ft.ElevatedButton(
        "Conferma e togli dalla dispensa", icon=ft.Icons.CHECK,
        bgcolor=ft.Colors.LIGHT_BLUE_600, color=ft.Colors.WHITE,
        on_click=scarica, visible=False,
    )

    def chiudi_dialog(e):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Row(controls=[
            ft.Icon(ft.Icons.RESTAURANT_MENU, color=ft.Colors.LIGHT_BLUE_700),
            ft.Text("Dettaglio ricetta", weight=ft.FontWeight.BOLD),
        ]),
        content=ft.Container(
            content=ft.Column(
                controls=[contenitore_ricetta, ft.Text("L'IA può commettere errori", weight=ft.FontWeight.W_200)],
                scroll=ft.ScrollMode.AUTO,
            ),
            width=450, height=350,
        ),
        actions=[bottone_scarica, ft.TextButton("Chiudi", on_click=chiudi_dialog)],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def controlla_disponibilita(report_scarico: list, prodotti_dispensa: list) -> bool:
        if not report_scarico:
            return True

        for ing in report_scarico:
            nome_ing = ing.get("nome")
            qta_necessaria = ing.get("qta_usata", 0)

            if not nome_ing:
                continue

            prodotto = next(
                (p for p in prodotti_dispensa if p["nome"].lower().strip() == nome_ing.lower().strip()),
                None,
            )

            if not prodotto or prodotto["qta"] < qta_necessaria:
                return False

        return True

    def ricarica_lista():
        ricette_agg = ottieni_ricette()
        prodotti_dispensa = ottieni_prodotti()

        colonna_ricette.controls = (
            [crea_card(r, prodotti_dispensa) for r in ricette_agg]
            if ricette_agg
            else [
                ft.Container(
                    expand=True, alignment=ft.Alignment.CENTER,
                    content=ft.Text(
                        "Non hai ancora salvato nessuna ricetta",
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            ]
        )
        page.update()

    def elimina(e, id_ricetta):
        elimina_ricetta(id_ricetta)
        ricarica_lista()

    def apri_ricetta(e, testo_ricetta, report_scarico):
        nonlocal report_scarico_corrente
        contenitore_ricetta.value = testo_ricetta
        report_scarico_corrente = report_scarico or []

        prodotti_dispensa = ottieni_prodotti()
        disponibile = controlla_disponibilita(report_scarico_corrente, prodotti_dispensa)

        bottone_scarica.visible = bool(report_scarico_corrente)
        bottone_scarica.disabled = not disponibile
        bottone_scarica.text = (
            "Conferma e togli dalla dispensa" if disponibile else "Prodotti insufficienti in dispensa"
        )

        if dialog not in page.overlay:
            page.overlay.append(dialog)

        dialog.open = True
        page.update()

    def crea_card(ricetta, prodotti_dispensa):
        id_ricetta = ricetta["id"]
        report_scarico = ricetta.get("report_scarico", [])

        is_disponibile = controlla_disponibilita(report_scarico, prodotti_dispensa)
        colore_sfondo = ft.Colors.WHITE if is_disponibile else ft.Colors.GREY_300

        return ft.Card(
            elevation=1,
            bgcolor=colore_sfondo,
            shape=ft.RoundedRectangleBorder(radius=14),
            content=ft.Container(
                padding=ft.Padding.symmetric(vertical=12, horizontal=14),
                content=ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.MENU_BOOK_ROUNDED,
                            icon_color=ft.Colors.LIGHT_BLUE_700,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.LIGHT_BLUE_100, shape=ft.RoundedRectangleBorder(radius=10)),
                            tooltip="Leggi ricetta",
                            on_click=lambda e, r=ricetta: apri_ricetta(e, r["testo_ricetta"], r.get("report_scarico")),
                        ),
                        ft.Text(ricetta["titolo"], expand=True, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color=ft.Colors.RED_700,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_200, shape=ft.RoundedRectangleBorder(radius=10)),
                            tooltip="Elimina ricetta",
                            on_click=lambda e: elimina(e, id_ricetta),
                        ),
                    ],
                ),
            ),
        )

    ricette_iniziali = ottieni_ricette()
    prodotti_iniziali = ottieni_prodotti()

    colonna_ricette = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        scroll=ft.ScrollMode.AUTO,
        spacing=8,
        controls=[crea_card(r, prodotti_iniziali) for r in ricette_iniziali]
        if ricette_iniziali
        else [
            ft.Container(
                expand=True, alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    "Non hai ancora salvato nessuna ricetta",
                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                    text_align=ft.TextAlign.CENTER,
                ),
            )
        ],
    )

    ricarica_lista()

    header = ft.Container(
        padding=ft.Padding.only(top=15, bottom=5),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=24, color=ft.Colors.LIGHT_BLUE_700),
                ft.Text("Le tue ricette salvate", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, size=24, text_align=ft.TextAlign.CENTER),
            ],
        ),
    )

    return ft.SafeArea(
        expand=True,
        content=ft.Column(
            expand=True,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                header,
                ft.Container(
                    expand=True, margin=10, padding=10,
                    bgcolor=ACCENT, border_radius=16,
                    content=colonna_ricette,
                ),
            ],
        ),
    )