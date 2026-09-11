import configparser
import os
import flet as ft


def _percorsi_config():
    base_dir = os.getenv("FLET_APP_STORAGE_DATA", os.path.dirname(os.path.abspath(__file__)))
    return (
        os.path.join(base_dir, "Api.conf"),
        os.path.join(base_dir, "Theme.conf"),
    )


def _assicura_file_default():
    api_conf_path, theme_conf_path = _percorsi_config()

    if not os.path.exists(theme_conf_path):
        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg["Theme"] = {"Theme": "LIGHT"}
        with open(theme_conf_path, "w") as f:
            cfg.write(f)

    if not os.path.exists(api_conf_path):
        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg["Api"] = {"Api": ""}
        with open(api_conf_path, "w") as f:
            cfg.write(f)

    return api_conf_path, theme_conf_path


def leggi_api() -> str:
    api_conf_path, _ = _assicura_file_default()
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(api_conf_path)
    return cfg.get("Api", "Api", fallback="")


def leggi_tema() -> str:
    _, theme_conf_path = _assicura_file_default()
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(theme_conf_path)
    return cfg.get("Theme", "Theme", fallback="LIGHT")


ACCENT = ft.Colors.LIGHT_BLUE_200


def schermata_impostazioni(page: ft.Page):
    page.title = "FridgeBuddy"
    page.padding = 20

    api_conf_path, theme_conf_path = _assicura_file_default()

    tema_corrente = leggi_tema()
    api_corrente = leggi_api()
    indice_iniziale = 0 if tema_corrente == "LIGHT" else 1

    def cambio_tema(e: ft.Event[ft.CupertinoSlidingSegmentedButton]):
        nuovo_tema = "LIGHT" if e.control.selected_index == 0 else "DARK"
        page.theme_mode = ft.ThemeMode.LIGHT if nuovo_tema == "LIGHT" else ft.ThemeMode.DARK

        try:
            cfg = configparser.ConfigParser()
            cfg.optionxform = str
            cfg["Theme"] = {"Theme": nuovo_tema}
            with open(theme_conf_path, "w") as f:
                cfg.write(f)
        except Exception as ex:
            snack = ft.SnackBar(content=ft.Text(f"❌ Tema non salvato: {ex}"), bgcolor=ft.Colors.RED_700)
            page.overlay.append(snack)
            snack.open = True

        page.update()

    tf_api = ft.TextField(
        adaptive=True,
        expand=True,
        value=api_corrente,
        password=True,
        can_reveal_password=True,
        label="Inserisci qui la tua chiave API",
        label_style=ft.TextStyle(color=ft.Colors.LIGHT_BLUE_700),
    )

    def salva_API(e):
        chiave = tf_api.value

        try:
            cfg = configparser.ConfigParser()
            cfg.optionxform = str
            cfg["Api"] = {"Api": chiave if chiave else ""}

            with open(api_conf_path, "w") as f:
                cfg.write(f)

            snack = ft.SnackBar(content=ft.Text("✅ Chiave API salvata"), bgcolor=ft.Colors.GREEN_700)
        except Exception as ex:
            snack = ft.SnackBar(content=ft.Text(f"❌ Errore salvataggio: {ex}"), bgcolor=ft.Colors.RED_700)

        page.overlay.append(snack)
        snack.open = True
        page.update()

    testo = ft.Text(
        """
Accedi a Google AI Studio
Vai sul sito di Google AI Studio ed effettua l'accesso con il tuo account Google.

Apri la sezione Chiavi API
Nel menu laterale a sinistra, clicca sulla voce Chiavi API.

Crea la chiave
Clicca sul pulsante Create chiave API. Scegli se associarla a un progetto esistente o a un nuovo progetto predefinito.

Copia e salva
Copia la stringa generata e salvala dentro FridgeBuddy.

Sicurezza
Tratta la chiave API come una password. Non condividerla pubblicamente.
La tua chiave API viene salvata solamente in locale sul tuo dispositivo.
        """
    )

    def chiudi_dialog(e):
        info.open = False
        page.update()

    info = ft.AlertDialog(
        title=ft.Row(controls=[
            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=ft.Colors.LIGHT_BLUE_700),
            ft.Text("Come creare la tua API", weight=ft.FontWeight.BOLD),
        ]),
        content=testo,
        actions=[ft.TextButton("Chiudi", on_click=chiudi_dialog)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(info)

    def apri(e):
        info.open = True
        page.update()

    def sezione(titolo: str, contenuto: ft.Control):
        return ft.Container(
            margin=ft.Margin.only(bottom=15),
            padding=16,
            bgcolor=ACCENT,
            border_radius=16,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text(titolo, theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD),
                    contenuto,
                ],
            ),
        )

    header = ft.Container(
        padding=ft.Padding.only(bottom=10),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=24, color=ft.Colors.LIGHT_BLUE_700),
                ft.Text("Impostazioni", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, size=24, text_align=ft.TextAlign.CENTER),
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

                sezione(
                    "Tema",
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.CupertinoSlidingSegmentedButton(
                                selected_index=indice_iniziale,
                                thumb_color=ft.Colors.WHITE,
                                on_change=cambio_tema,
                                controls=[ft.Text("Light"), ft.Text("Dark")],
                            ),
                        ],
                    ),
                ),

                sezione(
                    "Chiave API",
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.IconButton(ft.Icons.INFO_OUTLINE_ROUNDED, on_click=apri),
                            tf_api,
                            ft.IconButton(
                                icon=ft.Icons.SAVE_ROUNDED,
                                icon_color=ft.Colors.LIGHT_BLUE_700,
                                tooltip="Salva",
                                on_click=salva_API,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
