import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QColorDialog,
    QFileDialog, QComboBox, QVBoxLayout, QGridLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import Image, ImageDraw
import qrcode
import qrcode.image.svg


def pil2qimage(pil_img):
    """PIL Image objesini QImage’e çevirir (RGBA bekleniyor)."""
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    return QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)


class MetroDarkQR(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metro Dark QR Kod Üretici")
        self.setFixedSize(600, 720)
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            }
            QPushButton {
                background-color: #1f1f1f;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2e2e2e;
            }
            QLineEdit, QComboBox {
                background-color: #1f1f1f;
                border: 1px solid #3a3a3a;
                padding: 5px;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QLabel {
                font-weight: bold;
            }
        """)
        self.init_ui()
        self.onizleme_goster = False

    def init_ui(self):
        layout = QVBoxLayout()
        grid = QGridLayout()

        # URL
        grid.addWidget(QLabel("URL:"), 0, 0)
        self.url_input = QLineEdit("https://beykozunsesi.com.tr")
        grid.addWidget(self.url_input, 0, 1)

        # Boyut (editable combo)
        grid.addWidget(QLabel("Boyut (px):"), 1, 0)
        self.boyut_combo = QComboBox()
        self.boyut_combo.setEditable(True)
        self.boyut_combo.addItems(["300", "600", "1080", "3840", "4096"])
        self.boyut_combo.setCurrentText("3840")
        grid.addWidget(self.boyut_combo, 1, 1)

        # Ön plan renk
        self.onrenk_btn = QPushButton("Ön Plan Renk Seç")
        self.onrenk_btn.clicked.connect(lambda: self.renk_sec(self.onrenk_btn))
        self.onrenk_btn.setStyleSheet("background-color: black; color: white;")
        grid.addWidget(QLabel("Ön Plan Renk:"), 2, 0)
        grid.addWidget(self.onrenk_btn, 2, 1)

        # Gradient başlangıç rengi
        self.renk1_btn = QPushButton("Gradient Başlangıç Rengi Seç")
        self.renk1_btn.clicked.connect(lambda: self.renk_sec(self.renk1_btn))
        self.renk1_btn.setStyleSheet("background-color: #2196F3; color: white;")
        grid.addWidget(QLabel("Gradient Başlangıç Rengi:"), 3, 0)
        grid.addWidget(self.renk1_btn, 3, 1)

        # Gradient bitiş rengi
        self.renk2_btn = QPushButton("Gradient Bitiş Rengi Seç")
        self.renk2_btn.clicked.connect(lambda: self.renk_sec(self.renk2_btn))
        self.renk2_btn.setStyleSheet("background-color: #21CBF3; color: white;")
        grid.addWidget(QLabel("Gradient Bitiş Rengi:"), 4, 0)
        grid.addWidget(self.renk2_btn, 4, 1)

        # Gradient tipi
        grid.addWidget(QLabel("Gradient Tipi:"), 5, 0)
        self.gradient_tipi = QComboBox()
        self.gradient_tipi.addItems(["Dikey", "Yatay", "Çapraz", "Dairesel"])
        grid.addWidget(self.gradient_tipi, 5, 1)

        # Format
        grid.addWidget(QLabel("Format:"), 6, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "SVG", "PDF", "WebP", "GIF (Animasyon)"])
        grid.addWidget(self.format_combo, 6, 1)

        layout.addLayout(grid)

        # Önizleme label
        self.onizleme_label = QLabel()
        self.onizleme_label.setAlignment(Qt.AlignCenter)
        self.onizleme_label.setFixedSize(320, 320)
        self.onizleme_label.hide()
        layout.addWidget(QLabel("Önizleme:", alignment=Qt.AlignCenter))
        layout.addWidget(self.onizleme_label)

        # Üret butonu
        self.uret_btn = QPushButton("QR Kod Üret ve Kaydet")
        self.uret_btn.clicked.connect(self.qr_uret)
        self.uret_btn.setStyleSheet(
            "background-color: #2979ff; color: white; font-weight: bold; padding: 10px; border-radius: 6px;"
        )
        layout.addWidget(self.uret_btn)

        self.setLayout(layout)

        # Varsayılan renkler
        self.onrenk_btn.setProperty("renk", "#000000")
        self.renk1_btn.setProperty("renk", "#2196F3")
        self.renk2_btn.setProperty("renk", "#21CBF3")

        # Değişikliklerde önizlemeyi güncelle
        for btn in [self.onrenk_btn, self.renk1_btn, self.renk2_btn]:
            btn.clicked.connect(self.guncelle_onizleme)

        self.url_input.textChanged.connect(self.guncelle_onizleme)
        self.boyut_combo.currentTextChanged.connect(self.guncelle_onizleme)
        self.gradient_tipi.currentIndexChanged.connect(self.guncelle_onizleme)
        self.format_combo.currentIndexChanged.connect(self.guncelle_onizleme)

    def renk_sec(self, btn):
        renk = QColorDialog.getColor()
        if renk.isValid():
            btn.setStyleSheet(f"background-color: {renk.name()}; color: white;")
            btn.setProperty("renk", renk.name())
            self.guncelle_onizleme()

    def gradient_arka_plan(self, boyut, renk1, renk2, tipi):
        img = Image.new("RGB", (boyut, boyut), renk1)
        draw = ImageDraw.Draw(img)
        for y in range(boyut):
            for x in range(boyut):
                oran_x = x / boyut
                oran_y = y / boyut
                if tipi == "Dikey":
                    oran = oran_y
                elif tipi == "Yatay":
                    oran = oran_x
                elif tipi == "Çapraz":
                    oran = (oran_x + oran_y) / 2
                elif tipi == "Dairesel":
                    merkez = boyut / 2
                    dist = ((x - merkez) ** 2 + (y - merkez) ** 2) ** 0.5 / merkez
                    oran = min(dist, 1)
                r = int(renk1[0] + (renk2[0] - renk1[0]) * oran)
                g = int(renk1[1] + (renk2[1] - renk1[1]) * oran)
                b = int(renk1[2] + (renk2[2] - renk1[2]) * oran)
                draw.point((x, y), (r, g, b))
        return img

    def guncelle_onizleme(self):
        try:
            img = self.qr_uret(only_preview=True)
            if img:
                pil_img = img.resize((300, 300), Image.LANCZOS)
                qimg = pil2qimage(pil_img)  # Güncellenmiş dönüşüm fonksiyonu
                pix = QPixmap.fromImage(qimg)
                self.onizleme_label.setPixmap(pix)
                self.onizleme_label.show()
                self.onizleme_goster = True
            else:
                self.onizleme_label.hide()
        except Exception as e:
            print(f"Önizleme hata: {e}")
            self.onizleme_label.hide()

    def qr_uret(self, only_preview=False):
        url = self.url_input.text().strip()
        if not url:
            if not only_preview:
                QMessageBox.warning(self, "Hata", "Lütfen URL giriniz!")
            return None

        boyut_text = self.boyut_combo.currentText()
        try:
            boyut = int(boyut_text)
            if boyut < 100 or boyut > 10000:
                raise ValueError()
        except Exception:
            if not only_preview:
                QMessageBox.warning(self, "Hata", "Geçersiz boyut değeri! 100-10000 arasında sayı girin.")
            return None

        onrenk = self.onrenk_btn.property("renk") or "#000000"
        renk1 = self.renk1_btn.property("renk") or "#2196F3"
        renk2 = self.renk2_btn.property("renk") or "#21CBF3"
        tipi = self.gradient_tipi.currentText()
        format_sec = self.format_combo.currentText().lower()

        def hex2rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        onrenk_rgb = onrenk
        renk1_rgb = hex2rgb(renk1)
        renk2_rgb = hex2rgb(renk2)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color=onrenk_rgb, back_color="white").convert("RGBA")
        qr_img = qr_img.resize((boyut, boyut), Image.LANCZOS)

        bg = self.gradient_arka_plan(boyut, renk1_rgb, renk2_rgb, tipi).convert("RGBA")

        datas = qr_img.getdata()
        yeni_data = []
        for item in datas:
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                yeni_data.append((0, 0, 0, 0))
            else:
                yeni_data.append(item)
        qr_img.putdata(yeni_data)

        sonuc = bg.copy()
        sonuc.paste(qr_img, (0, 0), qr_img)

        if only_preview:
            return sonuc

        dosya, _ = QFileDialog.getSaveFileName(self, "Kaydet", "qr_kod", f"*.{format_sec}")
        if not dosya:
            return

        if format_sec == "svg":
            img_svg = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
            with open(dosya, "w") as f:
                f.write(img_svg.to_string())
        elif format_sec == "pdf":
            sonuc.save(dosya, "PDF")
        elif format_sec == "gif (animasyon)":
            frames = []
            for i in range(10):
                r = int(renk1_rgb[0] + (renk2_rgb[0] - renk1_rgb[0]) * i / 9)
                g = int(renk1_rgb[1] + (renk2_rgb[1] - renk1_rgb[1]) * i / 9)
                b = int(renk1_rgb[2] + (renk2_rgb[2] - renk1_rgb[2]) * i / 9)
                frame_bg = self.gradient_arka_plan(boyut, (r, g, b), renk2_rgb, tipi).convert("RGBA")
                frame_bg.paste(qr_img, (0, 0), qr_img)
                frames.append(frame_bg)
            frames[0].save(dosya, save_all=True, append_images=frames[1:], duration=100, loop=0)
        else:
            sonuc.save(dosya)

        QMessageBox.information(self, "Başarılı", f"QR kod kaydedildi:\n{dosya}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = MetroDarkQR()
    pencere.show()
    sys.exit(app.exec_())
