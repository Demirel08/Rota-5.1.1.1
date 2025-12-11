from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime, timedelta

class DailySummaryDialog(QDialog):
    """Program açıldığında güncel özet bilgileri gösteren dialog"""

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Günlük Özet - REFLEKS 360 ROTA")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self.init_ui()
        self.load_summary_data()

    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Başlık
        title_label = QLabel("📊 GÜNCEL DURUM ÖZETİ")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Tarih
        date_label = QLabel(datetime.now().strftime("%d.%m.%Y - %A"))
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("color: #666; font-size: 11pt;")
        layout.addWidget(date_label)

        # Ayırıcı
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Scroll area için içerik
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setSpacing(10)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Kapat butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Kapat")
        btn_close.setMinimumWidth(120)
        btn_close.setMinimumHeight(35)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def create_info_card(self, title, value, color="#6B46C1", subtitle=""):
        """Bilgi kartı oluştur"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border-left: 4px solid {color};
                border-radius: 5px;
                padding: 10px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(5)

        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 10pt;")
        card_layout.addWidget(title_label)

        # Değer
        value_label = QLabel(str(value))
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        card_layout.addWidget(value_label)

        # Alt başlık (varsa)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #666; font-size: 9pt;")
            card_layout.addWidget(subtitle_label)

        return card

    def load_summary_data(self):
        """Özet verileri yükle ve göster"""
        try:
            # Aktif projeler
            projects = self.db.get_all_projects()
            active_projects = [p for p in projects if p.get('status') != 'Tamamlandı']

            card = self.create_info_card(
                "Aktif Projeler",
                len(active_projects),
                "#6B46C1",
                f"Toplam {len(projects)} proje"
            )
            self.content_layout.addWidget(card)

            # Siparişler
            orders = self.db.get_all_orders()
            pending_orders = [o for o in orders if o.get('status') not in ['Tamamlandı', 'Sevk Edildi']]

            card = self.create_info_card(
                "Devam Eden Siparişler",
                len(pending_orders),
                "#0066CC",
                f"Toplam {len(orders)} sipariş"
            )
            self.content_layout.addWidget(card)

            # Bugün teslim edilecek siparişler
            today = datetime.now().date()
            today_str = today.strftime("%Y-%m-%d")

            due_today = []
            for order in orders:
                delivery_date = order.get('delivery_date', '')
                if delivery_date and delivery_date.startswith(today_str):
                    if order.get('status') not in ['Tamamlandı', 'Sevk Edildi']:
                        due_today.append(order)

            if due_today:
                card = self.create_info_card(
                    "⚠️ Bugün Teslim",
                    len(due_today),
                    "#C65911",
                    "Acil takip gerekiyor!"
                )
                self.content_layout.addWidget(card)

            # Gecikmiş siparişler
            overdue = []
            for order in orders:
                delivery_date = order.get('delivery_date', '')
                if delivery_date:
                    try:
                        delivery_dt = datetime.strptime(delivery_date[:10], "%Y-%m-%d").date()
                        if delivery_dt < today and order.get('status') not in ['Tamamlandı', 'Sevk Edildi']:
                            overdue.append(order)
                    except:
                        pass

            if overdue:
                card = self.create_info_card(
                    "🚨 Gecikmiş Siparişler",
                    len(overdue),
                    "#C00000",
                    "Acil müdahale gerekiyor!"
                )
                self.content_layout.addWidget(card)

            # Kritik stok durumu
            try:
                stocks = self.db.get_all_plates()
                low_stock = [s for s in stocks if s.get('quantity', 0) <= 5]

                if low_stock:
                    card = self.create_info_card(
                        "⚠️ Düşük Stok",
                        len(low_stock),
                        "#FFC107",
                        "Plaka stoğu azalıyor"
                    )
                    self.content_layout.addWidget(card)
            except:
                pass

            # Üretim istasyonları
            try:
                stations = self.db.get_all_stations()
                active_stations = [s for s in stations if s.get('is_active', True)]

                card = self.create_info_card(
                    "Aktif İstasyonlar",
                    len(active_stations),
                    "#107C41",
                    f"{len(stations)} istasyon tanımlı"
                )
                self.content_layout.addWidget(card)
            except:
                pass

            # Boşluk ekle
            self.content_layout.addStretch()

            # Bilgi mesajı
            if not due_today and not overdue:
                success_frame = QFrame()
                success_frame.setStyleSheet("""
                    QFrame {
                        background-color: #10C41020;
                        border-left: 4px solid #107C41;
                        border-radius: 5px;
                        padding: 15px;
                    }
                """)
                success_layout = QVBoxLayout(success_frame)
                success_label = QLabel("✅ Tüm siparişler zamanında ilerliyor!")
                success_label.setStyleSheet("color: #107C41; font-weight: bold;")
                success_layout.addWidget(success_label)
                self.content_layout.addWidget(success_frame)

        except Exception as e:
            error_label = QLabel(f"Veriler yüklenirken hata oluştu:\n{str(e)}")
            error_label.setStyleSheet("color: #C00000;")
            self.content_layout.addWidget(error_label)
