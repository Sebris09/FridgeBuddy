import flet as ft
import flet_camera as fc

from datetime import datetime
import asyncio
import json
import os
import tempfile

from ai import analisi
from Database import inserisci_manuale, inserisci_scontrino


def carica_scontrino(page: ft.Page):
    page.title = "FridgeBuddy"

    data_selezionata = [datetime.now()]

    def mostra_messaggio(testo, colore):
        snackbar = ft.SnackBar(content=ft.Text(testo), bgcolor=colore)
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()

    loading_dialog = ft.AlertDialog(
        modal=True,
        content=ft.Container(
            width=280,
            padding=25,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                spacing=20,
                controls=[
                    ft.ProgressRing(width=50, height=50, stroke_width=4),
                    ft.Text("Immagine in elaborazione...", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ],
            ),
        ),
    )
    page.overlay.append(loading_dialog)

    camera = fc.Camera(expand=True, preview_enabled=True)
    camera_view = None
    camera_pronta = [False]

    camera_status = ft.Text(
        "Avvio fotocamera...", color=ft.Colors.WHITE, size=15,
        weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER,
    )

    async def elabora_immagine(percorso):
        try:
            risposta_json_str = await asyncio.to_thread(analisi, percorso)
            dati = json.loads(risposta_json_str)
            prodotti = dati.get("prodotti", [])
            prodotti_aggiunti = 0

            for prod in prodotti:
                nome = prod.get("nome")
                if not nome:
                    continue

                try:
                    qta = int(prod.get("qta", 1))
                except (ValueError, TypeError):
                    qta = 1

                try:
                    giorni_durata = int(prod.get("g_durata", 7))
                except (ValueError, TypeError):
                    giorni_durata = 7

                data_letta = prod.get("data_scadenza_letta", "")
                data_valida = None
                if data_letta:
                    try:
                        datetime.strptime(data_letta, "%Y-%m-%d")
                        data_valida = data_letta
                    except ValueError:
                        data_valida = None

                inserisci_scontrino(nome=nome, giorni_durata=giorni_durata, qta=qta, data_scadenza=data_valida)
                prodotti_aggiunti += 1

            return prodotti_aggiunti

        finally:
            try:
                if percorso and os.path.exists(percorso):
                    os.remove(percorso)
            except Exception:
                pass

    async def chiudi_camera(e=None):
        camera_pronta[0] = False

        try:
            await camera.pause_preview()
        except Exception:
            pass

        if page.views and page.views[-1] is camera_view:
            page.views.pop()

        page.update()

    async def inizializza_camera():
        try:
            camera_status.value = "Avvio fotocamera..."
            page.update()

            camere = await camera.get_available_cameras()

            if not camere:
                camera_status.value = "Nessuna fotocamera disponibile."
                page.update()
                return False

            camera_scelta = camere[0]

            for cam in camere:
                try:
                    if cam.lens_direction == fc.CameraLensDirection.BACK:
                        camera_scelta = cam
                        break
                except Exception:
                    pass

            await camera.initialize(
                description=camera_scelta,
                resolution_preset=fc.ResolutionPreset.HIGH,
                enable_audio=False,
                image_format_group=fc.ImageFormatGroup.JPEG,
            )

            camera_pronta[0] = True
            camera_status.value = "Inquadra lo scontrino o i prodotti"
            page.update()
            return True

        except Exception as ex:
            camera_pronta[0] = False
            camera_status.value = f"Errore fotocamera:\n{str(ex)}"
            page.update()
            return False

    async def scatta_foto(e=None):
        if not camera_pronta[0]:
            mostra_messaggio("⏳ Fotocamera non ancora pronta.", ft.Colors.ORANGE_700)
            return

        try:
            camera_status.value = "📸 Scatto..."
            page.update()

            foto = await camera.take_picture()

            if not foto:
                raise Exception("La fotocamera non ha restituito l'immagine.")

            fd, percorso = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)

            with open(percorso, "wb") as f:
                f.write(foto)

            camera_pronta[0] = False

            try:
                await camera.pause_preview()
            except Exception:
                pass

            if page.views and page.views[-1] is camera_view:
                page.views.pop()

            page.update()

            loading_dialog.open = True
            page.update()

            try:
                numero = await elabora_immagine(percorso)
            finally:
                loading_dialog.open = False
                page.update()

            mostra_messaggio(f"✅ Inseriti {numero} prodotti in dispensa!", ft.Colors.GREEN_700)

        except Exception as ex:
            loading_dialog.open = False
            camera_pronta[0] = False
            page.update()
            mostra_messaggio(f"❌ Errore fotocamera: {str(ex)}", ft.Colors.RED_700)

    pulsante_chiudi = ft.Container(
        width=48, height=48,
        bgcolor=ft.Colors.BLACK_54,
        border_radius=24,
        alignment=ft.Alignment.CENTER,
        content=ft.IconButton(icon=ft.Icons.CLOSE, icon_color=ft.Colors.WHITE, icon_size=27, on_click=chiudi_camera),
    )

    indicatore = ft.Container(
        padding=ft.Padding(left=18, right=18, top=8, bottom=8),
        bgcolor=ft.Colors.BLACK_54,
        border_radius=20,
        content=ft.Row(
            spacing=8, tight=True,
            controls=[ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.WHITE, size=18), camera_status],
        ),
    )

    preview_camera = ft.Container(expand=True, bgcolor=ft.Colors.BLACK, alignment=ft.Alignment.CENTER, content=camera)

    header_camera = ft.Container(
        height=75,
        bgcolor=ft.Colors.BLACK,
        padding=ft.Padding(left=15, right=15, top=10, bottom=10),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Scatta una foto", color=ft.Colors.WHITE, size=22, weight=ft.FontWeight.BOLD),
                pulsante_chiudi,
            ],
        ),
    )

    overlay_camera = ft.Container(expand=True, alignment=ft.Alignment.TOP_CENTER, padding=20, content=indicatore)

    area_camera = ft.Container(
        expand=True,
        bgcolor=ft.Colors.BLACK,
        content=ft.Stack(expand=True, controls=[preview_camera, overlay_camera]),
    )

    pulsante_scatto = ft.Container(
        width=82, height=82,
        bgcolor=ft.Colors.WHITE,
        border_radius=41,
        padding=5,
        content=ft.Container(
            bgcolor=ft.Colors.LIGHT_BLUE_600,
            border_radius=36,
            alignment=ft.Alignment.CENTER,
            content=ft.IconButton(icon=ft.Icons.PHOTO_CAMERA, icon_color=ft.Colors.WHITE, icon_size=32, on_click=scatta_foto),
        ),
    )

    footer_camera = ft.Container(height=125, bgcolor=ft.Colors.BLACK, alignment=ft.Alignment.CENTER, content=pulsante_scatto)

    camera_view = ft.View(
        route="/camera",
        padding=0,
        bgcolor=ft.Colors.BLACK,
        controls=[header_camera, area_camera, footer_camera],
    )

    async def apri_camera(e=None):
        if camera_pronta[0]:
            return

        page.views.append(camera_view)
        page.update()

        ok = await inizializza_camera()

        if not ok:
            if page.views and page.views[-1] is camera_view:
                page.views.pop()
            page.update()

    testo_data = ft.Text(
        f"Data scelta: {data_selezionata[0].strftime('%d/%m/%Y')}",
        weight=ft.FontWeight.W_600, color=ft.Colors.LIGHT_BLUE_200,
    )

    def data_cambiata(e):
        if date_picker.value:
            data_selezionata[0] = date_picker.value
            testo_data.value = f"Data scelta: {date_picker.value.strftime('%d/%m/%Y')}"
            page.update()

    date_picker = ft.DatePicker(first_date=datetime.now(), on_change=data_cambiata)
    page.overlay.append(date_picker)

    def apri_datepicker(e):
        date_picker.open = True
        page.update()

    tf_nome = ft.TextField(label="Nome prodotto", label_style=ft.TextStyle(color=ft.Colors.LIGHT_BLUE_200))

    tf_quantita = ft.TextField(
        label="Quantità (pezzi o grammi)",
        keyboard_type=ft.KeyboardType.NUMBER,
        label_style=ft.TextStyle(color=ft.Colors.LIGHT_BLUE_200),
    )

    def salva_manuale(e):
        nome = tf_nome.value.strip() if tf_nome.value else ""

        if not nome:
            mostra_messaggio("⚠️ Inserisci il nome del prodotto.", ft.Colors.ORANGE_700)
            return

        try:
            quantita = int(tf_quantita.value)
        except (ValueError, TypeError):
            quantita = 1

        scadenza = data_selezionata[0].strftime("%d/%m/%Y")

        try:
            inserisci_manuale(nome, scadenza, quantita)

            tf_nome.value = ""
            tf_quantita.value = ""
            manuale.open = False
            page.update()

            mostra_messaggio("✅ Prodotto aggiunto!", ft.Colors.GREEN_700)

        except Exception as ex:
            mostra_messaggio(f"❌ Errore: {str(ex)}", ft.Colors.RED_700)

    def apri_manuale(e):
        manuale.open = True
        page.update()

    manuale = ft.AlertDialog(
        title=ft.Text("Aggiungi manualmente", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=400,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                spacing=10,
                controls=[
                    ft.Text("Nome prodotto", weight=ft.FontWeight.BOLD),
                    tf_nome,
                    ft.Text("Quantità prodotto", weight=ft.FontWeight.BOLD),
                    ft.Text("Inserire il peso in grammi o la quantità di prodotti", size=12, weight=ft.FontWeight.W_300, text_align=ft.TextAlign.CENTER),
                    tf_quantita,
                    ft.Text("Scadenza prodotto", weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Seleziona data di scadenza", icon=ft.Icons.CALENDAR_MONTH, on_click=apri_datepicker),
                    testo_data,
                ],
            ),
        ),
        actions=[ft.TextButton("Salva", on_click=salva_manuale)],
    )
    page.overlay.append(manuale)

    bottone_scontrino = ft.Container(
        expand=True,
        border_radius=16,
        bgcolor=ft.Colors.LIGHT_BLUE_400,
        ink=True,
        on_click=apri_camera,
        padding=20,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Icon(ft.Icons.CAMERA_ALT, size=64, color=ft.Colors.WHITE),
                ft.Text("Scansiona Scontrino o Prodotti", size=23, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Apri la fotocamera e fotografa lo scontrino oppure direttamente i prodotti", size=14, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
            ],
        ),
    )

    bottone_manuale = ft.Container(
        expand=True,
        border_radius=16,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(2, ft.Colors.LIGHT_BLUE_200),
        ink=True,
        on_click=apri_manuale,
        padding=20,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Icon(ft.Icons.EDIT, size=64, color=ft.Colors.LIGHT_BLUE_400),
                ft.Text("Aggiungi manualmente", size=23, color=ft.Colors.LIGHT_BLUE_400, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Inserisci direttamente un prodotto nella dispensa", size=14, color=ft.Colors.LIGHT_BLUE_400, text_align=ft.TextAlign.CENTER),
            ],
        ),
    )

    return ft.SafeArea(
        expand=True,
        content=ft.Column(
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=15,
            controls=[bottone_scontrino, bottone_manuale],
        ),
    )