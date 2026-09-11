import flet as ft
from datetime import datetime
from Database import ottieni_prodotti, inizializza_db, elimina, aggiorna_qta

ACCENT = ft.Colors.LIGHT_BLUE_200


def dispensa(page: ft.Page):
    page.title = "FridgeBuddy"

    inizializza_db()
    prodotti = ottieni_prodotti()

    def formatta_scadenza(scadenza_iso):
        try:
            dt = datetime.strptime(scadenza_iso, "%Y-%m-%d")
            giorni = (dt.date() - datetime.now().date()).days

            if giorni < 0:
                return "Scaduto", ft.Colors.RED_700
            if giorni == 0:
                return "Scade oggi", ft.Colors.RED_700
            if giorni <= 3:
                return f"Scade il {dt.strftime('%d/%m/%Y')}", ft.Colors.RED_400
            if giorni <= 7:
                return f"Scade il {dt.strftime('%d/%m/%Y')}", ft.Colors.ORANGE_700
            return f"Scade il {dt.strftime('%d/%m/%Y')}", ft.Colors.GREY_600

        except Exception:
            return scadenza_iso, ft.Colors.GREY_600

    def stato_vuoto():
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.KITCHEN_OUTLINED, size=50, color=ft.Colors.LIGHT_BLUE_700),
                    ft.Text(
                        "La tua dispensa è vuota, scansiona uno scontrino",
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def ricarica_lista():
        prodotti_agg = ottieni_prodotti()
        colonna_prodotti.controls = (
            [crea_card(p) for p in prodotti_agg]
            if prodotti_agg
            else [stato_vuoto()]
        )
        page.update()

    def elimina_prodotto(e, id_prodotto):
        elimina(id_prodotto)
        ricarica_lista()

    def crea_card(prodotto):
        id_prod = prodotto["id"]
        testo_scadenza, colore_scadenza = formatta_scadenza(prodotto["scadenza"])

        bottone_qta = ft.ElevatedButton(
            content=ft.Text(str(prodotto["qta"])),
            width=44, height=32,
            style=ft.ButtonStyle(padding=0, shape=ft.RoundedRectangleBorder(radius=10)),
        )

        def apri_dialog_qta(e):
            tf_qta = ft.TextField(
                value=bottone_qta.content.value,
                keyboard_type=ft.KeyboardType.NUMBER,
                autofocus=True, width=80, text_align=ft.TextAlign.CENTER,
            )

            def salva_qta(e_salva):
                try:
                    nuova_qta = int(tf_qta.value)
                    aggiorna_qta(id_prod, nuova_qta)
                    dlg.open = False
                    page.update()
                    ricarica_lista()
                except ValueError:
                    pass

            def chiudi_dialog(e_chiudi):
                dlg.open = False
                page.update()

            dlg = ft.AlertDialog(
                title=ft.Text(f"Modifica quantità: {prodotto['nome']}"),
                content=ft.Container(content=tf_qta, alignment=ft.Alignment.CENTER, height=60),
                actions=[
                    ft.TextButton("Annulla", on_click=chiudi_dialog),
                    ft.ElevatedButton("Salva", on_click=salva_qta),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        bottone_qta.on_click = apri_dialog_qta

        def diminuisci(e):
            valore_attuale = int(bottone_qta.content.value)
            if valore_attuale >= 1:
                aggiorna_qta(id_prod, valore_attuale - 1)
                ricarica_lista()

        def aumenta(e):
            valore_attuale = int(bottone_qta.content.value)
            nuovo_valore = valore_attuale + 1
            aggiorna_qta(id_prod, nuovo_valore)
            bottone_qta.content.value = str(nuovo_valore)
            page.update()

        counter = ft.Row(
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=ft.Colors.LIGHT_BLUE_700,
                              icon_size=20, style=ft.ButtonStyle(padding=0), on_click=diminuisci),
                bottone_qta,
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ft.Colors.LIGHT_BLUE_700,
                              icon_size=20, style=ft.ButtonStyle(padding=0), on_click=aumenta),
            ],
        )

        return ft.Card(
            elevation=1,
            shape=ft.RoundedRectangleBorder(radius=14),
            content=ft.Container(
                padding=ft.Padding.symmetric(vertical=12, horizontal=14),
                content=ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(prodotto["nome"], weight=ft.FontWeight.W_600, size=15),
                                ft.Text(testo_scadenza, size=12, weight=ft.FontWeight.W_500, color=colore_scadenza),
                            ],
                        ),
                        counter,
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color=ft.Colors.RED_400,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_100, shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=lambda e: elimina_prodotto(e, prodotto["id"]),
                        ),
                    ],
                ),
            ),
        )

    colonna_prodotti = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        scroll=ft.ScrollMode.AUTO,
        spacing=8,
        controls=[crea_card(p) for p in prodotti] if prodotti else [stato_vuoto()],
    )

    header = ft.Container(
        padding=ft.Padding.only(top=15, bottom=5),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.KITCHEN_OUTLINED, size=24, color=ft.Colors.LIGHT_BLUE_700),
                ft.Text("La tua dispensa", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, size=24, text_align=ft.TextAlign.CENTER),
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
                    expand=True,
                    margin=10,
                    padding=10,
                    bgcolor=ACCENT,
                    border_radius=16,
                    content=colonna_prodotti,
                ),
            ],
        ),
    )