import flet as ft
from datetime import datetime

if not hasattr(ft, "run"):
    raise RuntimeError(
        f"Versione Flet caricata: {getattr(ft, '__version__', 'sconosciuta')} "
        f"- percorso: {getattr(ft, '__file__', 'sconosciuto')}"
    )

from Database import inizializza_db, ottieni_3_prodotti, ottieni_prodotti
from Impostazioni import schermata_impostazioni, leggi_tema
from Dispensa import dispensa
from Ricetta import pagina_ricetta
from Carica_Scontrino import carica_scontrino
from Ricette_salvate import ricette_salvate



ACCENT = ft.Colors.LIGHT_BLUE_200


def main(page: ft.Page):

    inizializza_db()

    page.title = "FridgeBuddy"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ft.Colors.SURFACE

    tema = leggi_tema()

    if tema == "LIGHT":
        page.theme_mode = ft.ThemeMode.LIGHT
    else:
        page.theme_mode = ft.ThemeMode.DARK

    area_contenuto = ft.Container(expand=True)
    scheda_attiva = "home"

    def mostra_home():

        prodotti = ottieni_3_prodotti()

        prodotti_tutti = ottieni_prodotti()
        totale_prodotti = len(prodotti_tutti)

        oggi = datetime.now().date()
        prodotti_in_scadenza = 0
        for p in prodotti_tutti:
            try:
                data_scad = datetime.strptime(p["scadenza"], "%Y-%m-%d").date()
                if (data_scad - oggi).days <= 3:
                    prodotti_in_scadenza += 1
            except Exception:
                pass

        def crea_statistica(icona, valore, etichetta, bgcolor, colore):
            return ft.Container(
                expand=True,
                bgcolor=bgcolor,
                border_radius=16,
                padding=ft.Padding.symmetric(vertical=14, horizontal=8),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[
                        ft.Icon(icona, size=24, color=colore),
                        ft.Text(str(valore), size=24, weight=ft.FontWeight.BOLD, color=colore),
                        ft.Text(
                            etichetta,
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=colore,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
            )

        allarme = prodotti_in_scadenza > 0

        riga_statistiche = ft.Container(
            margin=ft.Margin.only(left=10, right=10, top=8),
            content=ft.Row(
                spacing=10,
                controls=[
                    crea_statistica(
                        ft.Icons.KITCHEN_OUTLINED,
                        totale_prodotti,
                        "Prodotti in dispensa",
                        ft.Colors.LIGHT_BLUE_100,
                        ft.Colors.LIGHT_BLUE_700,
                    ),
                    crea_statistica(
                        ft.Icons.WARNING_AMBER_ROUNDED if allarme else ft.Icons.CHECK_CIRCLE_OUTLINE,
                        prodotti_in_scadenza,
                        "In scadenza (≤3 gg)",
                        ft.Colors.RED_100 if allarme else ft.Colors.GREEN_100,
                        ft.Colors.RED_700 if allarme else ft.Colors.GREEN_700,
                    ),
                ],
            ),
        )

        logo = (
            "/Logo.png"
            if page.theme_mode == ft.ThemeMode.LIGHT
            else "/LogoW.png"
        )

        header = ft.Container(
            height=70,
            padding=10,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        content=ft.Image(src=logo, fit=ft.BoxFit.CONTAIN),
                    ),
                    ft.Container(
                        alignment=ft.Alignment.CENTER_RIGHT,
                        content=ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            icon_size=28,
                            tooltip="Impostazioni",
                            on_click=lambda e: naviga("impostazioni"),
                        ),
                    ),
                ],
            ),
        )

        if prodotti:
            cards = [
                ft.Card(
                    height=75,
                    elevation=1,
                    content=ft.Container(
                        alignment=ft.Alignment.CENTER,
                        padding=10,
                        border_radius=12,
                        content=ft.Text(
                            prodotto["nome"],
                            size=17,
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ),
                )
                for prodotto in prodotti
            ]

            lista_prodotti = ft.Column(expand=True, spacing=8, controls=cards)

        else:
            lista_prodotti = ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    controls=[
                        ft.Icon(ft.Icons.KITCHEN_OUTLINED, size=50, color=ft.Colors.LIGHT_BLUE_700),
                        ft.Text("La tua dispensa è vuota", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text("Scansiona uno scontrino per aggiungere prodotti.", size=14, text_align=ft.TextAlign.CENTER),
                    ],
                ),
            )

        box_scadenze = ft.Container(
            expand=True,
            margin=10,
            padding=15,
            bgcolor=ACCENT,
            border_radius=16,
            content=ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    ft.Text("Prodotti in scadenza", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    lista_prodotti,
                ],
            ),
        )

        return ft.SafeArea(
            expand=True,
            content=ft.Column(expand=True, spacing=0, controls=[header, riga_statistiche, box_scadenze]),
        )

    def naviga(nome_scheda):
        nonlocal scheda_attiva
        scheda_attiva = nome_scheda

        page.overlay.clear()

        if nome_scheda == "home":
            area_contenuto.content = mostra_home()
        elif nome_scheda == "dispensa":
            area_contenuto.content = dispensa(page)
        elif nome_scheda == "scontrino":
            area_contenuto.content = carica_scontrino(page)
        elif nome_scheda == "ricetta":
            area_contenuto.content = pagina_ricetta(page)
        elif nome_scheda == "ricette_salvate":
            area_contenuto.content = ricette_salvate(page)
        elif nome_scheda == "impostazioni":
            area_contenuto.content = schermata_impostazioni(page)

        page.update()

    area_contenuto.content = mostra_home()

    btn_dispensa = ft.IconButton(
        icon=ft.Icons.KITCHEN_OUTLINED, icon_size=27, tooltip="Dispensa",
        on_click=lambda e: naviga("dispensa"),
    )

    btn_scontrino = ft.IconButton(
        icon=ft.Icons.RECEIPT_LONG_OUTLINED, icon_size=27, tooltip="Scansiona scontrino",
        on_click=lambda e: naviga("scontrino"),
    )

    btn_home = ft.Container(
        width=62, height=62,
        bgcolor=ft.Colors.LIGHT_BLUE_600,
        shape=ft.BoxShape.CIRCLE,
        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.BLACK_26),
        content=ft.IconButton(
            icon=ft.Icons.HOME_ROUNDED, icon_color=ft.Colors.WHITE, icon_size=34,
            on_click=lambda e: naviga("home"),
        ),
    )

    btn_ricetta = ft.IconButton(
        icon=ft.Icons.RESTAURANT_MENU_OUTLINED, icon_size=27, tooltip="Ricetta",
        on_click=lambda e: naviga("ricetta"),
    )

    btn_salvate = ft.IconButton(
        icon=ft.Icons.MENU_BOOK_OUTLINED, icon_size=27, tooltip="Ricette salvate",
        on_click=lambda e: naviga("ricette_salvate"),
    )

    barra_navigazione = ft.Container(
        height=75,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        padding=5,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK_12),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[btn_dispensa, btn_scontrino, btn_home, btn_ricetta, btn_salvate],
        ),
    )

    page.add(
        ft.SafeArea(
            expand=True,
            avoid_intrusions_top=False,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[area_contenuto, barra_navigazione],
            ),
        )
    )

    page.update()

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")