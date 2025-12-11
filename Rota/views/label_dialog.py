import sys
import qrcode
from io import BytesIO
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen

try:
    from ui.theme import Theme
except ImportError:
    pass

class LabelDialog(QDialog):
    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.data = order_data
        self.setWindowTitle(f"Etiket Önizleme: {order_data['code']}")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #2C3E50;") # Koyu arka plan (Etiket parlasın diye)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Başlık
        lbl_info = QLabel("YAZDIRILACAK ETİKET ÖNİZLEMESİ")
        lbl_info.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)
        
        # --- ETİKET ALANI (BEYAZ KART) ---
        self.label_frame = QLabel()
        self.label_frame.setFixedSize(400, 250) # Standart etiket boyutu oranı
        self.label_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        self.label_frame.setAlignment(Qt.AlignCenter)
        
        # Etiketi Çiz
        self.render_label()
        
        # Gölge Efekti (Hava katsın)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.label_frame.setGraphicsEffect(shadow)
        
        # Ortala
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(self.label_frame)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        # --- BUTONLAR ---
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("KAPAT")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("""
            QPushButton { background-color: transparent; color: #BDC3C7; border: 1px solid #BDC3C7; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { color: white; border-color: white; }
        """)
        
        btn_print = QPushButton("🖨️ YAZDIR / PDF KAYDET")
        btn_print.setCursor(Qt.PointingHandCursor)
        btn_print.clicked.connect(self.print_label)
        btn_print.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_print)
        
        layout.addLayout(btn_layout)

    def generate_qr(self, data_str):
        """Python qrcode kütüphanesi ile QR oluşturur"""
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(data_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # PIL Image -> QPixmap dönüşümü
        im_data = img.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(im_data, img.size[0], img.size[1], QImage.Format_RGBA8888)
        return QPixmap.fromImage(qim)

    def render_label(self):
        """Etiketi kodla çizer (Resim olarak)"""
        # Boş bir resim oluştur (Tuval)
        canvas = QPixmap(400, 250)
        canvas.fill(Qt.white)
        
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Siyah Üst Bant (Firma Adı İçin)
        painter.fillRect(0, 0, 400, 50, QColor("black"))
        
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(15, 32, "EFES CAM FABRİKASI")
        
        painter.setFont(QFont("Arial", 10))
        painter.drawText(280, 32, self.data['date']) # Tarih sağda
        
        # 2. QR Kod (Solda)
        # Sipariş kodunu QR'a gömüyoruz
        qr_pixmap = self.generate_qr(self.data['code'])
        qr_pixmap = qr_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(15, 65, qr_pixmap)
        
        # 3. Ana Bilgiler (Ortada)
        painter.setPen(Qt.black)
        
        # Müşteri
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QColor("#7F8C8D"))
        painter.drawText(130, 80, "MÜŞTERİ:")
        
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.setPen(Qt.black)
        painter.drawText(130, 100, self.data['customer'][:20]) # Sığmazsa kes
        
        # Ürün
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QColor("#7F8C8D"))
        painter.drawText(130, 130, "ÜRÜN TİPİ:")
        
        painter.setFont(QFont("Arial", 11))
        painter.setPen(Qt.black)
        painter.drawText(130, 150, f"{self.data['thickness']}mm {self.data['product']}")
        
        # 4. DEV ÖLÇÜLER (Usta uzaktan görsün diye)
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 28, QFont.Bold))
        # Kutu içine alalım
        rect_pen = QPen(Qt.black, 2)
        painter.setPen(rect_pen)
        painter.drawRect(130, 170, 250, 60)
        
        painter.drawText(130, 170, 250, 60, Qt.AlignCenter, f"{self.data['width']} x {self.data['height']}")
        
        # 5. Alt Bilgi (Rota)
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QColor("#333"))
        # Rota bilgisini al (Eğer varsa)
        route = self.data.get('route', 'STANDART')
        painter.drawText(15, 240, f"ROTA: {route}")
        
        painter.end()
        
        # Ekrana bas
        self.label_frame.setPixmap(canvas)
        self.current_label_pixmap = canvas

    def print_label(self):
        """Yazıcıya gönderir veya kaydeder"""
        # Gerçek yazıcı entegrasyonu karmaşıktır, burada resmi kaydedelim
        filename = f"ETIKET_{self.data['code']}.png"
        self.current_label_pixmap.save(filename)
        
        # Kullanıcıya bilgi ver
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Yazdırıldı", f"Etiket başarıyla oluşturuldu:\n{filename}\n\n(Gerçek sistemde bu dosya barkod yazıcısına gönderilir.)")
        self.accept()