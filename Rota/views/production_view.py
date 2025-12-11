"""
EFES ROTA X - Uretim Takip Ekrani
"""

import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QProgressBar,
    QComboBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView,
    QLineEdit, QSpinBox, QSplitter, QApplication,
    QInputDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

try:
    from core.db_manager import db
except ImportError:
    db = None


# =============================================================================
# TEMA
# =============================================================================
class Colors:
    BG = "#FFFFFF"
    HEADER_BG = "#F3F3F3"
    BORDER = "#D4D4D4"
    GRID = "#E0E0E0"
    TEXT = "#1A1A1A"
    TEXT_SECONDARY = "#666666"
    TEXT_MUTED = "#999999"
    SELECTION = "#B4D7FF"
    ACCENT = "#217346"
    ROW_ALT = "#F9F9F9"
    
    CRITICAL = "#C00000"
    CRITICAL_BG = "#FDE8E8"
    WARNING = "#C65911"
    WARNING_BG = "#FFF3E0"
    SUCCESS = "#107C41"
    SUCCESS_BG = "#E6F4EA"
    INFO = "#0066CC"
    INFO_BG = "#E3F2FD"


# =============================================================================
# FABRIKA AYARLARI
# =============================================================================
class FactoryConfig:
    """Istasyon sirasi ve gruplar"""
    
    STATION_ORDER = [
        "INTERMAC", "LIVA KESIM", "LAMINE KESIM",
        "CNC RODAJ", "DOUBLEDGER", "ZIMPARA",
        "TESIR A1", "TESIR B1", "TESIR B1-1", "TESIR B1-2", "DELIK", "OYGU",
        "TEMPER A1", "TEMPER B1", "TEMPER BOMBE",
        "LAMINE A1", "ISICAM B1"
    ]
    
    HIDDEN_STATIONS = ["SEVKIYAT", "SEVKİYAT"]
    
    @classmethod
    def get_station_index(cls, station_name):
        try:
            return cls.STATION_ORDER.index(station_name)
        except ValueError:
            return 999
    
    @classmethod
    def should_show_station(cls, station_name):
        return station_name not in cls.HIDDEN_STATIONS


# =============================================================================
# URETIM GIRIS DIALOGU
# =============================================================================
class ProductionEntryDialog(QDialog):
    def __init__(self, order_data, station_name, station_info, parent=None):
        super().__init__(parent)
        self.order = order_data
        self.station = station_name
        self.info = station_info
        self.result_qty = 0
        self.selected_plate_id = None

        self.setWindowTitle("Uretim Girisi")
        self.setFixedSize(450, 450)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.BG}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel(f"Uretim Girisi - {self.station}")
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Colors.ACCENT};")
        layout.addWidget(title)
        
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.BORDER};")
        layout.addWidget(sep)
        
        info_style = f"font-size: 11px; color: {Colors.TEXT_SECONDARY};"
        
        order_code = self.order.get('code', self.order.get('order_code', ''))
        customer = self.order.get('customer', self.order.get('customer_name', ''))
        
        lbl_order = QLabel(f"Siparis: {order_code}")
        lbl_order.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(lbl_order)
        
        lbl_customer = QLabel(f"Musteri: {customer}")
        lbl_customer.setStyleSheet(info_style)
        layout.addWidget(lbl_customer)
        
        layout.addSpacing(8)
        
        done = int(self.info.get('done', 0))
        total = int(self.info.get('total', 0))
        remaining = max(0, total - done)
        
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 10, 12, 10)
        
        for label, value, color in [
            ("Toplam", total, Colors.TEXT),
            ("Biten", done, Colors.SUCCESS),
            ("Kalan", remaining, Colors.WARNING if remaining > 0 else Colors.SUCCESS)
        ]:
            item = QVBoxLayout()
            item.setSpacing(2)
            
            lbl_t = QLabel(label)
            lbl_t.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_MUTED};")
            lbl_t.setAlignment(Qt.AlignCenter)
            item.addWidget(lbl_t)
            
            lbl_v = QLabel(str(value))
            lbl_v.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
            lbl_v.setAlignment(Qt.AlignCenter)
            item.addWidget(lbl_v)
            
            status_layout.addLayout(item)
        
        layout.addWidget(status_frame)
        
        layout.addSpacing(8)

        # Plaka Seçimi (KESIM istasyonları için)
        if self.station in ["INTERMAC", "LIVA KESIM", "LAMINE KESIM"]:
            plate_label = QLabel("📦 Kullanılan Plaka:")
            plate_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT};")
            layout.addWidget(plate_label)

            self.combo_plate = QComboBox()
            self.combo_plate.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {Colors.BORDER};
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 12px;
                    background-color: white;
                }}
                QComboBox:focus {{
                    border-color: {Colors.ACCENT};
                }}
            """)

            # Sipariş bilgilerinden cam tipi ve kalınlığı al
            thickness = self.order.get('thickness', 0)
            product_type = self.order.get('product_type', '')

            # Uygun plakaları getir
            if db:
                plates = db.get_plates_by_thickness_type(thickness, product_type)
                self.combo_plate.addItem("-- Plaka Seçiniz --", None)

                for plate in plates:
                    if plate.get('quantity', 0) > 0:
                        display_text = (
                            f"{plate['width']}x{plate['height']} cm - "
                            f"{plate['quantity']} adet - "
                            f"{plate.get('location', 'Konum yok')}"
                        )
                        self.combo_plate.addItem(display_text, plate['id'])

                if self.combo_plate.count() == 1:
                    # Uygun plaka yok
                    self.combo_plate.addItem("⚠️ Uygun plaka bulunamadı", None)
                    self.combo_plate.setCurrentIndex(1)

            layout.addWidget(self.combo_plate)
            layout.addSpacing(8)

        else:
            self.combo_plate = None

        qty_layout = QHBoxLayout()

        lbl_qty = QLabel("Tamamlanan Adet:")
        lbl_qty.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT};")
        qty_layout.addWidget(lbl_qty)

        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, max(1, remaining))
        self.spin_qty.setValue(remaining if remaining > 0 else 1)
        self.spin_qty.setFixedWidth(100)
        self.spin_qty.setStyleSheet(f"""
            QSpinBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QSpinBox:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        qty_layout.addWidget(self.spin_qty)
        qty_layout.addStretch()

        layout.addLayout(qty_layout)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Iptal")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.HEADER_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 0 20px;
                color: {Colors.TEXT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BORDER};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_layout.addStretch()
        
        btn_save = QPushButton("Kaydet")
        btn_save.setFixedHeight(34)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 4px;
                padding: 0 30px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_save.clicked.connect(self.save_production)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
    
    def save_production(self):
        self.result_qty = self.spin_qty.value()

        # Plaka seçimi kontrolü (kesim istasyonları için)
        if self.combo_plate is not None:
            selected_idx = self.combo_plate.currentIndex()
            self.selected_plate_id = self.combo_plate.itemData(selected_idx)

            if self.selected_plate_id is None and self.combo_plate.count() > 1:
                reply = QMessageBox.question(
                    self,
                    "Plaka Seçmediniz",
                    "Plaka seçmediniz! Stok ekranınızdan bu üretim düşmeyecektir.\n\n"
                    "Yine de devam etmek istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

        self.accept()


# =============================================================================
# SIPARIS SATIRI
# =============================================================================
class OrderRowWidget(QFrame):
    clicked = Signal(dict)
    
    def __init__(self, order_data):
        super().__init__()
        self.order = order_data
        self.setup_ui()
        self.setCursor(Qt.PointingHandCursor)
    
    def setup_ui(self):
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border-bottom: 1px solid {Colors.GRID};
            }}
            QFrame:hover {{
                background-color: {Colors.SELECTION};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 12, 6)
        layout.setSpacing(8)
        
        queue_pos = self.order.get('queue_position', 0)
        if queue_pos and queue_pos < 9999:
            lbl_pos = QLabel(f"{queue_pos}")
            lbl_pos.setFixedWidth(24)
            lbl_pos.setAlignment(Qt.AlignCenter)
            lbl_pos.setStyleSheet(f"""
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT_SECONDARY};
                font-size: 10px;
                font-weight: bold;
                border-radius: 3px;
                padding: 2px;
            """)
            layout.addWidget(lbl_pos)
        
        priority = self.order.get('priority', 'Normal')
        priority_colors = {
            'Kritik': Colors.CRITICAL,
            'Acil': Colors.WARNING,
            'Cok Acil': Colors.WARNING,
            'Normal': Colors.BORDER
        }
        
        indicator = QFrame()
        indicator.setFixedSize(4, 40)
        indicator.setStyleSheet(f"background-color: {priority_colors.get(priority, Colors.BORDER)}; border-radius: 2px;")
        layout.addWidget(indicator)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        
        code = self.order.get('code', self.order.get('order_code', ''))
        lbl_code = QLabel(code)
        lbl_code.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT};")
        top_layout.addWidget(lbl_code)
        
        if priority in ['Kritik', 'Acil', 'Cok Acil']:
            lbl_priority = QLabel(priority)
            lbl_priority.setStyleSheet(f"""
                background-color: {Colors.CRITICAL_BG if priority == 'Kritik' else Colors.WARNING_BG};
                color: {Colors.CRITICAL if priority == 'Kritik' else Colors.WARNING};
                padding: 1px 6px;
                border-radius: 2px;
                font-size: 9px;
                font-weight: bold;
            """)
            top_layout.addWidget(lbl_priority)

        # Not ikonu
        notes = self.order.get('notes', '').strip()
        if notes:
            lbl_note = QLabel("📝")
            lbl_note.setToolTip(notes)
            lbl_note.setCursor(Qt.PointingHandCursor)
            lbl_note.setStyleSheet(f"""
                color: {Colors.ACCENT};
                font-size: 14px;
                padding: 0 4px;
            """)
            # Tıklanabilir yapmak için mouse event ekle
            def on_note_click(event, n=notes):
                event.accept()  # Event'i durdur
                self.show_note_popup(n)
            lbl_note.mousePressEvent = on_note_click
            top_layout.addWidget(lbl_note)

        top_layout.addStretch()
        info_layout.addLayout(top_layout)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)
        
        customer = self.order.get('customer', self.order.get('customer_name', ''))
        lbl_customer = QLabel(customer)
        lbl_customer.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_SECONDARY};")
        bottom_layout.addWidget(lbl_customer)
        
        delivery = self.order.get('delivery_date', '')
        if delivery:
            try:
                delivery_date = datetime.strptime(delivery, '%Y-%m-%d')
                days_left = (delivery_date - datetime.now()).days
                
                if days_left < 0:
                    delivery_text = f"Gecikti ({abs(days_left)}g)"
                    delivery_color = Colors.CRITICAL
                elif days_left == 0:
                    delivery_text = "Bugun!"
                    delivery_color = Colors.WARNING
                elif days_left <= 3:
                    delivery_text = f"{days_left} gun"
                    delivery_color = Colors.WARNING
                else:
                    delivery_text = f"{days_left} gun"
                    delivery_color = Colors.TEXT_MUTED
                
                lbl_delivery = QLabel(delivery_text)
                lbl_delivery.setStyleSheet(f"font-size: 10px; color: {delivery_color}; font-weight: bold;")
                bottom_layout.addWidget(lbl_delivery)
            except:
                pass
        
        bottom_layout.addStretch()
        info_layout.addLayout(bottom_layout)
        
        layout.addLayout(info_layout, 1)
        
        status_map = self.order.get('status_map', {})
        total_stations = sum(1 for s, v in status_map.items() 
                           if v.get('status') != 'Yok' and FactoryConfig.should_show_station(s))
        completed_stations = sum(1 for s, v in status_map.items() 
                                if v.get('status') == 'Bitti' and FactoryConfig.should_show_station(s))
        progress = int((completed_stations / total_stations * 100)) if total_stations > 0 else 0
        
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(2)
        
        lbl_progress = QLabel(f"{completed_stations}/{total_stations}")
        lbl_progress.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_MUTED};")
        lbl_progress.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(lbl_progress)
        
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(progress)
        bar.setTextVisible(False)
        bar.setFixedSize(70, 6)
        
        bar_color = Colors.SUCCESS if progress >= 100 else Colors.ACCENT
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BORDER};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 3px;
            }}
        """)
        progress_layout.addWidget(bar)
        
        layout.addLayout(progress_layout)
        
        has_partial = any(s.get('status') == 'Kismi' for s in status_map.values())
        all_done = all(s.get('status') in ['Bitti', 'Yok'] for s in status_map.values()) and total_stations > 0
        
        if all_done:
            status_text = "Bitti"
            status_bg = Colors.SUCCESS_BG
            status_fg = Colors.SUCCESS
        elif has_partial:
            status_text = "Uretimde"
            status_bg = Colors.INFO_BG
            status_fg = Colors.INFO
        else:
            status_text = "Bekliyor"
            status_bg = Colors.HEADER_BG
            status_fg = Colors.TEXT_SECONDARY
        
        lbl_status = QLabel(status_text)
        lbl_status.setFixedWidth(70)
        lbl_status.setAlignment(Qt.AlignCenter)
        lbl_status.setStyleSheet(f"""
            background-color: {status_bg};
            color: {status_fg};
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
        """)
        layout.addWidget(lbl_status)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.order)
        super().mousePressEvent(event)

    def show_note_popup(self, note_text):
        """Not popup penceresi göster"""
        QMessageBox.information(
            self,
            "Sipariş Notu",
            note_text,
            QMessageBox.Ok
        )


# =============================================================================
# ANA WIDGET
# =============================================================================
class ProductionView(QWidget):
    """Uretim Takip Ekrani"""
    
    def __init__(self):
        super().__init__()
        self.current_filter = "Tumu"
        self.selected_order = None
        self.all_orders = []
        self.setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(10000)
        
        self.refresh_data()
    
    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {Colors.BORDER}; width: 1px; }}")
        
        left_panel = self._create_list_panel()
        splitter.addWidget(left_panel)
        
        self.detail_panel = self._create_detail_panel()
        splitter.addWidget(self.detail_panel)
        
        splitter.setSizes([380, 620])
        
        layout.addWidget(splitter, 1)
        
        statusbar = self._create_statusbar()
        layout.addWidget(statusbar)
    
    def _create_toolbar(self):
        toolbar = QFrame()
        toolbar.setFixedHeight(32)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)
        
        lbl_title = QLabel("Uretim Takip")
        lbl_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(lbl_title)
        
        self._add_separator(layout)
        
        lbl_filter = QLabel("Filtre:")
        lbl_filter.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(lbl_filter)
        
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["Tumu", "Beklemede", "Uretimde", "Tamamlanan"])
        self.combo_filter.setFixedWidth(100)
        self.combo_filter.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
                background-color: {Colors.BG};
            }}
        """)
        self.combo_filter.currentTextChanged.connect(self.apply_filter)
        layout.addWidget(self.combo_filter)
        
        self._add_separator(layout)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Ara...")
        self.search_box.setFixedWidth(150)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }}
        """)
        self.search_box.textChanged.connect(self.apply_search)
        layout.addWidget(self.search_box)
        
        layout.addStretch()
        
        self.lbl_total = QLabel("Toplam: 0")
        self.lbl_total.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(self.lbl_total)
        
        layout.addSpacing(12)
        
        self.lbl_urgent = QLabel("Kritik: 0")
        self.lbl_urgent.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.CRITICAL};")
        layout.addWidget(self.lbl_urgent)
        
        layout.addSpacing(12)
        
        self.lbl_production = QLabel("Uretimde: 0")
        self.lbl_production.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.INFO};")
        layout.addWidget(self.lbl_production)
        
        self._add_separator(layout)
        
        btn_refresh = QPushButton("Yenile")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 2px;
                padding: 4px 10px;
                color: {Colors.TEXT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #E5E5E5;
                border: 1px solid {Colors.BORDER};
            }}
        """)
        btn_refresh.clicked.connect(self.refresh_data)
        layout.addWidget(btn_refresh)
        
        return toolbar
    
    def _create_list_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"background-color: {Colors.BG};")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QFrame()
        header.setFixedHeight(28)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        lbl = QLabel("Siparisler (Karar Destek Sirasina Gore)")
        lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.TEXT};")
        header_layout.addWidget(lbl)
        
        layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {Colors.BG};")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch()
        
        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)
        
        return panel
    
    def _create_detail_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border-left: 1px solid {Colors.BORDER};
            }}
        """)
        
        self.detail_layout = QVBoxLayout(panel)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(0)
        
        self._show_empty_detail()
        
        return panel
    
    def _create_statusbar(self):
        statusbar = QFrame()
        statusbar.setFixedHeight(22)
        statusbar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-top: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(statusbar)
        layout.setContentsMargins(8, 0, 8, 0)
        
        self.status_label = QLabel("Hazir")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return statusbar
    
    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(20)
        sep.setStyleSheet(f"background-color: {Colors.BORDER};")
        layout.addWidget(sep)
    
    def _show_empty_detail(self):
        self._clear_detail()
        
        empty = QLabel("Bir siparis secin")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px; padding: 60px;")
        self.detail_layout.addWidget(empty)
    
    def _clear_detail(self):
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def refresh_data(self):
        try:
            if db:
                matrix_data = db.get_production_matrix_advanced()
                
                orders_info = {}
                try:
                    with db.get_connection() as conn:
                        try:
                            conn.execute("ALTER TABLE orders ADD COLUMN queue_position INTEGER DEFAULT 9999")
                        except:
                            pass
                        
                        rows = conn.execute("""
                            SELECT id, priority, delivery_date,
                                   COALESCE(queue_position, 9999) as queue_position,
                                   COALESCE(notes, '') as notes
                            FROM orders
                            WHERE status NOT IN ('Sevk Edildi', 'Tamamlandı')
                            ORDER BY queue_position ASC, delivery_date ASC
                        """).fetchall()

                        for row in rows:
                            orders_info[row['id']] = {
                                'priority': row['priority'],
                                'delivery_date': row['delivery_date'],
                                'queue_position': row['queue_position'],
                                'notes': row['notes']
                            }
                except Exception as e:
                    print(f"Orders info error: {e}")
                
                for order in matrix_data:
                    order_id = order.get('id')
                    if order_id in orders_info:
                        order['priority'] = orders_info[order_id]['priority']
                        order['delivery_date'] = orders_info[order_id]['delivery_date']
                        order['queue_position'] = orders_info[order_id]['queue_position']
                        order['notes'] = orders_info[order_id]['notes']
                    else:
                        order['priority'] = 'Normal'
                        order['queue_position'] = 9999
                        order['notes'] = ''
                
                matrix_data.sort(key=lambda x: (x.get('queue_position', 9999), x.get('delivery_date', '9999-12-31')))
                
                self.all_orders = matrix_data
            else:
                self.all_orders = []
            
            self.update_list()
            self.update_stats()
            self.status_label.setText(f"{len(self.all_orders)} siparis | {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.status_label.setText(f"Hata: {str(e)}")
    
    def update_list(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        filtered = self._filter_orders(self.all_orders)
        
        if not filtered:
            empty = QLabel("Siparis bulunamadi")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {Colors.TEXT_MUTED}; padding: 40px;")
            self.list_layout.insertWidget(0, empty)
            return
        
        for order in filtered:
            row = OrderRowWidget(order)
            row.clicked.connect(self.show_detail)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)
    
    def update_stats(self):
        if not self.all_orders:
            self.lbl_total.setText("Toplam: 0")
            self.lbl_urgent.setText("Kritik: 0")
            self.lbl_production.setText("Uretimde: 0")
            return
        
        total = len(self.all_orders)
        urgent = sum(1 for o in self.all_orders if o.get('priority') in ['Kritik', 'Acil'])
        production = 0
        
        for order in self.all_orders:
            status_map = order.get('status_map', {})
            has_partial = any(s.get('status') == 'Kismi' for s in status_map.values())
            if has_partial:
                production += 1
        
        self.lbl_total.setText(f"Toplam: {total}")
        self.lbl_urgent.setText(f"Kritik: {urgent}")
        self.lbl_production.setText(f"Uretimde: {production}")
    
    def _filter_orders(self, orders):
        search_text = self.search_box.text().lower()
        if search_text:
            orders = [o for o in orders 
                     if search_text in o.get('code', '').lower() 
                     or search_text in o.get('customer', '').lower()]
        
        if self.current_filter == "Tumu":
            return orders
        
        filtered = []
        for order in orders:
            status_map = order.get('status_map', {})
            
            has_work = any(s.get('status') != 'Yok' and FactoryConfig.should_show_station(st) 
                          for st, s in status_map.items())
            if not has_work:
                continue
            
            has_partial = any(s.get('status') == 'Kismi' for s in status_map.values())
            all_done = all(s.get('status') in ['Bitti', 'Yok'] for s in status_map.values())
            not_started = all(s.get('status') in ['Bekliyor', 'Yok'] for s in status_map.values())
            
            if self.current_filter == "Beklemede" and not_started:
                filtered.append(order)
            elif self.current_filter == "Uretimde" and has_partial:
                filtered.append(order)
            elif self.current_filter == "Tamamlanan" and all_done:
                filtered.append(order)
        
        return filtered
    
    def apply_filter(self, text):
        self.current_filter = text
        self.update_list()
    
    def apply_search(self, text):
        self.update_list()
    
    def show_detail(self, order_data):
        self.selected_order = order_data
        self._clear_detail()
        
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(4)
        
        top_row = QHBoxLayout()
        
        code = order_data.get('code', order_data.get('order_code', ''))
        lbl_code = QLabel(code)
        lbl_code.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.TEXT};")
        top_row.addWidget(lbl_code)
        
        priority = order_data.get('priority', 'Normal')
        if priority in ['Kritik', 'Acil', 'Cok Acil']:
            lbl_priority = QLabel(priority)
            lbl_priority.setStyleSheet(f"""
                background-color: {Colors.CRITICAL_BG if priority == 'Kritik' else Colors.WARNING_BG};
                color: {Colors.CRITICAL if priority == 'Kritik' else Colors.WARNING};
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            """)
            top_row.addWidget(lbl_priority)
        
        top_row.addStretch()
        header_layout.addLayout(top_row)
        
        bottom_row = QHBoxLayout()
        
        customer = order_data.get('customer', order_data.get('customer_name', ''))
        lbl_customer = QLabel(customer)
        lbl_customer.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
        bottom_row.addWidget(lbl_customer)
        
        delivery = order_data.get('delivery_date', '')
        if delivery:
            try:
                delivery_date = datetime.strptime(delivery, '%Y-%m-%d')
                days_left = (delivery_date - datetime.now()).days
                
                if days_left < 0:
                    delivery_text = f"GECIKTI! ({abs(days_left)} gun)"
                    delivery_color = Colors.CRITICAL
                elif days_left == 0:
                    delivery_text = "BUGUN TESLIM!"
                    delivery_color = Colors.WARNING
                elif days_left <= 3:
                    delivery_text = f"Teslim: {days_left} gun kaldi"
                    delivery_color = Colors.WARNING
                else:
                    delivery_text = f"Teslim: {delivery} ({days_left} gun)"
                    delivery_color = Colors.TEXT_SECONDARY
                
                lbl_delivery = QLabel(delivery_text)
                lbl_delivery.setStyleSheet(f"font-size: 11px; color: {delivery_color}; font-weight: bold;")
                bottom_row.addWidget(lbl_delivery)
            except:
                pass
        
        bottom_row.addStretch()
        header_layout.addLayout(bottom_row)
        
        self.detail_layout.addWidget(header)
        
        station_header = QFrame()
        station_header.setFixedHeight(28)
        station_header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border-bottom: 1px solid {Colors.GRID};
            }}
        """)
        sh_layout = QHBoxLayout(station_header)
        sh_layout.setContentsMargins(16, 0, 16, 0)
        
        lbl_sh = QLabel("Istasyonlar (Rota Sirasina Gore)")
        lbl_sh.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.TEXT_SECONDARY};")
        sh_layout.addWidget(lbl_sh)
        
        self.detail_layout.addWidget(station_header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {Colors.BG};")
        
        stations_widget = QWidget()
        stations_layout = QVBoxLayout(stations_widget)
        stations_layout.setContentsMargins(16, 12, 16, 12)
        stations_layout.setSpacing(6)
        
        status_map = order_data.get('status_map', {})
        
        sorted_stations = self._sort_stations_by_route(status_map, order_data.get('route', ''))
        
        for station, info in sorted_stations:
            if not FactoryConfig.should_show_station(station):
                continue
            
            if info.get('status') == 'Yok':
                continue
            
            station_widget = self._create_station_row(station, info)
            stations_layout.addWidget(station_widget)
        
        stations_layout.addStretch()
        
        scroll.setWidget(stations_widget)
        self.detail_layout.addWidget(scroll, 1)
        
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(50)
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-top: 1px solid {Colors.BORDER};
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(16, 8, 16, 8)
        
        btn_fire = QPushButton("Fire Bildir")
        btn_fire.setFixedHeight(34)
        btn_fire.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.CRITICAL};
                border-radius: 4px;
                padding: 0 16px;
                color: {Colors.CRITICAL};
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.CRITICAL};
                color: white;
            }}
        """)
        btn_fire.clicked.connect(self.report_fire)
        bottom_layout.addWidget(btn_fire)
        
        bottom_layout.addStretch()
        
        self.detail_layout.addWidget(bottom_bar)
    
    def _sort_stations_by_route(self, status_map, route_str):
        if route_str:
            route_order = [s.strip() for s in route_str.split(',')]
            
            def get_order(item):
                station = item[0]
                try:
                    return route_order.index(station)
                except ValueError:
                    return 999
            
            return sorted(status_map.items(), key=get_order)
        else:
            return sorted(status_map.items(), key=lambda x: FactoryConfig.get_station_index(x[0]))
    
    def _create_station_row(self, station_name, info):
        row = QFrame()
        row.setFixedHeight(44)
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.ROW_ALT};
                border: 1px solid {Colors.GRID};
                border-radius: 4px;
            }}
        """)
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        
        status = info.get('status', 'Bekliyor')
        if status == 'Bitti':
            icon_text = "●"
            icon_color = Colors.SUCCESS
        elif status == 'Kısmi':
            icon_text = "◐"
            icon_color = Colors.WARNING
        else:
            icon_text = "○"
            icon_color = Colors.TEXT_MUTED
        
        lbl_icon = QLabel(icon_text)
        lbl_icon.setFixedWidth(16)
        lbl_icon.setStyleSheet(f"font-size: 14px; color: {icon_color};")
        layout.addWidget(lbl_icon)
        
        lbl_name = QLabel(station_name)
        lbl_name.setFixedWidth(110)
        lbl_name.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(lbl_name)
        
        done = int(info.get('done', 0))
        total = int(info.get('total', 0))
        
        lbl_qty = QLabel(f"{done}/{total}")
        lbl_qty.setFixedWidth(60)
        lbl_qty.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(lbl_qty)
        
        progress = int((done / total * 100)) if total > 0 else 0
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(progress)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BORDER};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {icon_color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(bar, 1)
        
        layout.addStretch()
        
        if status in ['Bekliyor', 'Kısmi']:
            btn_entry = QPushButton("Uretim Gir")
            btn_entry.setFixedSize(85, 28)
            btn_entry.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.ACCENT};
                    border: none;
                    border-radius: 3px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #1D6640;
                }}
            """)
            btn_entry.clicked.connect(lambda checked, s=station_name, i=info: self.open_production_dialog(s, i))
            layout.addWidget(btn_entry)
        else:
            lbl_done = QLabel("Tamamlandi")
            lbl_done.setStyleSheet(f"font-size: 10px; color: {Colors.SUCCESS}; font-weight: bold;")
            layout.addWidget(lbl_done)
        
        return row
    
    def open_production_dialog(self, station_name, station_info):
        if not self.selected_order:
            return
        
        remaining = int(station_info.get('total', 0)) - int(station_info.get('done', 0))
        if remaining <= 0:
            QMessageBox.information(self, "Bilgi", "Bu istasyonda kalan adet yok.")
            return
        
        dialog = ProductionEntryDialog(
            self.selected_order, 
            station_name, 
            station_info, 
            self
        )
        
        if dialog.exec() == QDialog.Accepted and dialog.result_qty > 0:
            try:
                order_id = self.selected_order.get('id')
                if db and order_id:
                    # Üretim kaydı
                    db.register_production(order_id, station_name, dialog.result_qty)

                    # Plaka stok azaltma (kesim istasyonları için)
                    if dialog.selected_plate_id:
                        db.decrease_plate_stock(dialog.selected_plate_id, amount=1)
                        self.status_label.setText(
                            f"{dialog.result_qty} adet {station_name} kaydedildi (1 plaka kullanıldı)"
                        )
                    else:
                        self.status_label.setText(f"{dialog.result_qty} adet {station_name} kaydedildi")

                    self.refresh_data()

                    for order in self.all_orders:
                        if order.get('id') == order_id:
                            self.show_detail(order)
                            break
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayit hatasi:\n{str(e)}")
    
    def report_fire(self):
        """Fire bildirimi - DÜZELTİLDİ: İstasyon sorar"""
        if not self.selected_order:
            return
        
        # 1. İstasyon Seçimi
        route_str = self.selected_order.get('route', '')
        if route_str:
            stations = [s.strip() for s in route_str.split(',')]
        else:
            stations = FactoryConfig.STATION_ORDER
            
        station, ok_st = QInputDialog.getItem(self, "İstasyon Seç", "Hangi istasyonda fire oldu?", stations, 0, False)
        if not ok_st: return

        # 2. Adet Girişi
        qty, ok = QInputDialog.getInt(
            self,
            "Fire Bildirimi",
            f"Siparis: {self.selected_order.get('code', '')}\nİstasyon: {station}\n\nKac adet fire?",
            1, 1, 1000
        )
        
        if ok and db:
            try:
                # Yönetici ekranından girildiği için operatör adı 'Yönetici' olarak kaydedilir
                db.report_fire(self.selected_order.get('id'), qty, station, "Yönetici")
                self.status_label.setText(f"{qty} adet fire kaydedildi ve Rework açıldı")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Hata:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 9))
    
    window = ProductionView()
    window.setWindowTitle("EFES ROTA X - Uretim Takip")
    window.resize(1200, 700)
    window.show()
    
    sys.exit(app.exec())