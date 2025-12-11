"""
EFES ROTA X - Stok Yönetimi ve Depo (Standartlaştırılmış)
- Stok girişi artık manuel değil, seçmeli yapılıyor.
- Kalınlık ve Cam Tipi seçilerek standart isimlendirme sağlanıyor.
"""

import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QProgressBar, QComboBox,
    QLineEdit, QAbstractItemView, QDialog,
    QMessageBox, QDoubleSpinBox, QApplication, QFormLayout,
    QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon

try:
    from core.db_manager import db
except ImportError:
    db = None


# =============================================================================
# TEMA VE RENKLER
# =============================================================================
class Colors:
    BG = "#FFFFFF"
    HEADER_BG = "#F8F9FA"
    BORDER = "#D4D4D4"
    GRID = "#E0E0E0"
    TEXT = "#212529"
    TEXT_SECONDARY = "#6C757D"
    
    STOCK_GOOD = "#2E7D32"
    STOCK_LOW = "#F57C00"
    STOCK_CRIT = "#D32F2F"
    
    ACCENT = "#0F6CBD"
    SELECTION = "#C6E2FF"


# =============================================================================
# PLAKA GİRİŞ PENCERESİ (YENİ)
# =============================================================================
class PlateEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plaka Stok Girişi")
        self.setFixedSize(450, 450)
        self.result_data = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG}; font-family: 'Segoe UI', Arial;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Başlık
        title = QLabel("📦 Depoya Plaka Ekle")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.ACCENT};")
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # 1. Kalınlık
        self.combo_thickness = QComboBox()
        thicknesses = ["4", "6", "8", "10", "12", "15", "19"]
        self.combo_thickness.addItems(thicknesses)
        self.combo_thickness.setCurrentText("6")
        form_layout.addRow("Kalınlık (mm):", self.combo_thickness)

        # 2. Cam Tipi
        self.combo_type = QComboBox()
        glass_types = ["Düz Cam", "Temperli", "Lamine", "Satina", "Ayna", "Renkli"]
        self.combo_type.addItems(glass_types)
        form_layout.addRow("Cam Tipi:", self.combo_type)

        # 3. Plaka Boyutu - Hazır seçimli
        self.combo_size = QComboBox()
        standard_sizes = [
            "321x244",
            "321x600",
            "244x170",
            "244x321",
            "600x321",
            "Özel Ebat"
        ]
        self.combo_size.addItems(standard_sizes)
        self.combo_size.currentTextChanged.connect(self.on_size_changed)
        form_layout.addRow("Plaka Boyutu (cm):", self.combo_size)

        # 4. Özel Ebat İçin Girişler (Başlangıçta gizli)
        custom_frame = QFrame()
        custom_layout = QHBoxLayout(custom_frame)
        custom_layout.setContentsMargins(0, 0, 0, 0)

        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(10, 1000)
        self.spin_width.setValue(321)
        self.spin_width.setSuffix(" cm")
        custom_layout.addWidget(QLabel("En:"))
        custom_layout.addWidget(self.spin_width)

        self.spin_height = QDoubleSpinBox()
        self.spin_height.setRange(10, 1000)
        self.spin_height.setValue(244)
        self.spin_height.setSuffix(" cm")
        custom_layout.addWidget(QLabel("Boy:"))
        custom_layout.addWidget(self.spin_height)

        self.custom_frame = custom_frame
        self.custom_frame.setVisible(False)
        form_layout.addRow("", self.custom_frame)

        # 5. Adet
        self.spin_quantity = QDoubleSpinBox()
        self.spin_quantity.setRange(1, 10000)
        self.spin_quantity.setValue(10)
        self.spin_quantity.setDecimals(0)
        self.spin_quantity.setSuffix(" adet")
        form_layout.addRow("Adet:", self.spin_quantity)

        # 6. Konum (Opsiyonel)
        self.inp_location = QLineEdit()
        self.inp_location.setPlaceholderText("Örn: Depo A-1, Raf 3")
        form_layout.addRow("Konum (Opsiyonel):", self.inp_location)

        layout.addLayout(form_layout)

        # Önizleme
        self.lbl_preview = QLabel()
        self.lbl_preview.setStyleSheet(f"""
            background-color: {Colors.HEADER_BG};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 12px;
            color: {Colors.TEXT};
            font-weight: bold;
        """)
        self.update_preview()
        layout.addWidget(self.lbl_preview)

        # Sinyaller
        self.combo_thickness.currentTextChanged.connect(self.update_preview)
        self.combo_type.currentTextChanged.connect(self.update_preview)
        self.combo_size.currentTextChanged.connect(self.update_preview)
        self.spin_width.valueChanged.connect(self.update_preview)
        self.spin_height.valueChanged.connect(self.update_preview)
        self.spin_quantity.valueChanged.connect(self.update_preview)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()

        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_layout.addStretch()

        btn_save = QPushButton("💾 Plaka Ekle")
        btn_save.clicked.connect(self.save)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #0B5EA8; }}
        """)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def on_size_changed(self, size_text):
        """Boyut seçimi değişince özel ebat alanını göster/gizle"""
        if size_text == "Özel Ebat":
            self.custom_frame.setVisible(True)
        else:
            self.custom_frame.setVisible(False)
            if "x" in size_text:
                parts = size_text.split("x")
                self.spin_width.setValue(int(parts[0]))
                self.spin_height.setValue(int(parts[1]))

    def update_preview(self):
        """Önizleme metnini güncelle"""
        thickness = self.combo_thickness.currentText()
        glass_type = self.combo_type.currentText()
        width = int(self.spin_width.value())
        height = int(self.spin_height.value())
        qty = int(self.spin_quantity.value())

        preview = f"{thickness}mm {glass_type}\n{width}x{height} cm\n{qty} adet"
        self.lbl_preview.setText(preview)

    def save(self):
        """Plakayı kaydet"""
        thickness = int(self.combo_thickness.currentText())
        glass_type = self.combo_type.currentText()
        width = int(self.spin_width.value())
        height = int(self.spin_height.value())
        quantity = int(self.spin_quantity.value())
        location = self.inp_location.text().strip()

        self.result_data = {
            'thickness': thickness,
            'glass_type': glass_type,
            'width': width,
            'height': height,
            'quantity': quantity,
            'location': location
        }
        self.accept()


# =============================================================================
# STANDART STOK GİRİŞ PENCERESİ (SEÇMELİ)
# =============================================================================
class StockEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stok Girişi")
        self.setFixedSize(400, 300)
        self.result_data = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG}; font-family: 'Segoe UI', Arial;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("Depoya Ürün Ekle")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.ACCENT};")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # 1. Kalınlık Seçimi
        self.combo_thickness = QComboBox()
        # Fabrika standart kalınlıkları
        thicknesses = ["4", "6", "8", "10", "12", "19"]
        self.combo_thickness.addItems(thicknesses)
        self.combo_thickness.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        form_layout.addRow("Cam Kalınlığı (mm):", self.combo_thickness)
        
        # 2. Cam Tipi Seçimi
        self.combo_type = QComboBox()
        # Fabrika standart cam tipleri
        glass_types = ["Düz Cam", "Temperli", "Lamine", "Satina", "Ayna", "Renkli", "Buzlu", "Reflekte"]
        self.combo_type.addItems(glass_types)
        self.combo_type.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        form_layout.addRow("Cam Tipi:", self.combo_type)
        
        # 3. Miktar
        self.spin_qty = QDoubleSpinBox()
        self.spin_qty.setRange(0.1, 100000)
        self.spin_qty.setValue(100)
        self.spin_qty.setSuffix(" m²")
        self.spin_qty.setStyleSheet(f"""
            QDoubleSpinBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        form_layout.addRow("Eklenecek Miktar:", self.spin_qty)
        
        # Önizleme
        self.lbl_preview = QLabel("4mm Düz Cam")
        self.lbl_preview.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-style: italic; margin-top: 5px;")
        form_layout.addRow("Ürün Kodu:", self.lbl_preview)
        
        # Sinyaller (Önizleme güncelleme)
        self.combo_thickness.currentTextChanged.connect(self.update_preview)
        self.combo_type.currentTextChanged.connect(self.update_preview)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.HEADER_BG};
                border: 1px solid {Colors.BORDER};
                color: {Colors.TEXT};
                padding: 8px 16px;
                border-radius: 4px;
            }}
        """)
        
        btn_save = QPushButton("Kaydet")
        btn_save.clicked.connect(self.save)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                color: white;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #0B5EA8; }}
        """)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def update_preview(self):
        thick = self.combo_thickness.currentText()
        gtype = self.combo_type.currentText()
        self.lbl_preview.setText(f"{thick}mm {gtype}")

    def save(self):
        thick = self.combo_thickness.currentText()
        gtype = self.combo_type.currentText()
        
        # Standart isimlendirme: "4mm Düz Cam"
        product_name = f"{thick}mm {gtype}"
        
        self.result_data = {
            "name": product_name,
            "qty": self.spin_qty.value()
        }
        self.accept()


# =============================================================================
# ANA STOK EKRANI
# =============================================================================
class StockView(QWidget):
    def __init__(self):
        super().__init__()
        self.all_stocks = []
        self.setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(10000)
        
        self.refresh_data()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG}; font-family: 'Segoe UI', Calibri, Arial;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # İstatistik
        stats_bar = self._create_stats_bar()
        layout.addWidget(stats_bar)

        # Tab Widget (Genel Stok ve Plaka Stoku)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER};
                background-color: {Colors.BG};
            }}
            QTabBar::tab {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT};
                padding: 8px 20px;
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                font-weight: bold;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.BG};
                color: {Colors.ACCENT};
                border-bottom: 2px solid {Colors.ACCENT};
            }}
            QTabBar::tab:hover {{
                background-color: {Colors.SELECTION};
            }}
        """)

        # Tab 1: Genel Stok (m² bazlı)
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(0, 0, 0, 0)
        self.table = self._create_table()
        general_layout.addWidget(self.table)
        self.tab_widget.addTab(general_tab, "📊 Genel Stok (m²)")

        # Tab 2: Plaka Stoku
        plate_tab = QWidget()
        plate_layout = QVBoxLayout(plate_tab)
        plate_layout.setContentsMargins(0, 0, 0, 0)
        self.plate_table = self._create_plate_table()
        plate_layout.addWidget(self.plate_table)
        self.tab_widget.addTab(plate_tab, "📦 Plaka Stoku")

        layout.addWidget(self.tab_widget)

        # Status Bar
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet(f"background-color: {Colors.HEADER_BG}; border-top: 1px solid {Colors.BORDER};")
        sb_layout = QHBoxLayout(self.status_bar)
        sb_layout.setContentsMargins(10, 0, 10, 0)

        self.lbl_status = QLabel("Hazır")
        self.lbl_status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        sb_layout.addWidget(self.lbl_status)

        layout.addWidget(self.status_bar)

    def _create_toolbar(self):
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(12)
        
        title = QLabel("Stok Yönetimi")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Ürün Ara...")
        self.search_box.setFixedWidth(200)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                background-color: {Colors.BG};
            }}
            QLineEdit:focus {{ border-color: {Colors.ACCENT}; }}
        """)
        self.search_box.textChanged.connect(self.filter_table)
        layout.addWidget(self.search_box)
        
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["Tümü", "Kritik Stoklar", "Yeterli Stoklar"])
        self.combo_filter.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                background-color: {Colors.BG};
            }}
        """)
        self.combo_filter.currentTextChanged.connect(self.filter_table)
        layout.addWidget(self.combo_filter)
        
        btn_refresh = QPushButton("Yenile")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_data)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {Colors.HEADER_BG}; }}
        """)
        layout.addWidget(btn_refresh)
        
        btn_add = QPushButton("+ Stok Girişi")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self.add_stock_dialog)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #0B5EA8; }}
        """)
        layout.addWidget(btn_add)
        
        return toolbar

    def _create_stats_bar(self):
        bar = QFrame()
        bar.setStyleSheet(f"background-color: {Colors.BG}; border-bottom: 1px solid {Colors.BORDER};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        self.lbl_total_items = QLabel("Çeşit: 0")
        self.lbl_total_m2 = QLabel("Toplam Stok: 0 m²")
        self.lbl_low_stock = QLabel("Kritik Ürün: 0")
        
        base_style = f"""
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            border: 1px solid {Colors.BORDER};
        """
        
        self.lbl_total_items.setStyleSheet(f"{base_style} background-color: {Colors.HEADER_BG}; color: {Colors.TEXT};")
        self.lbl_total_m2.setStyleSheet(f"{base_style} background-color: {Colors.HEADER_BG}; color: {Colors.ACCENT};")
        self.lbl_low_stock.setStyleSheet(f"{base_style} background-color: #FDEDED; color: {Colors.STOCK_CRIT}; border-color: {Colors.STOCK_CRIT};")
        
        layout.addWidget(self.lbl_total_items)
        layout.addWidget(self.lbl_total_m2)
        layout.addWidget(self.lbl_low_stock)
            
        layout.addStretch()
        return bar

    def _create_table(self):
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Ürün Adı", "Mevcut (m²)", "Min. Limit", "Doluluk Durumu", "Durum", "Son İşlem"])
        
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setGridStyle(Qt.SolidLine)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.setColumnWidth(0, 250)
        table.setColumnWidth(3, 150)
        
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {Colors.BORDER};
                border-right: 1px solid {Colors.BORDER};
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG};
                gridline-color: {Colors.GRID};
                border: 1px solid {Colors.BORDER};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {Colors.BORDER};
                color: {Colors.TEXT};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.SELECTION};
                color: #000000;
            }}
        """)
        
        return table

    def _create_plate_table(self):
        """Plaka stok tablosu"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Kalınlık", "Cam Tipi", "Boyut (cm)", "Adet", "Toplam m²", "Konum", "Eklenme", "İşlem"
        ])

        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setGridStyle(Qt.SolidLine)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {Colors.BORDER};
                border-right: 1px solid {Colors.BORDER};
                font-weight: bold;
                font-size: 11px;
            }}
        """)

        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG};
                gridline-color: {Colors.GRID};
                border: 1px solid {Colors.BORDER};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {Colors.BORDER};
                color: {Colors.TEXT};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.SELECTION};
                color: #000000;
            }}
        """)

        return table

    def refresh_data(self):
        if not db: return

        try:
            # Genel stok verisi
            self.all_stocks = db.get_all_stocks()
            self.filter_table()
            self.update_stats()

            # Plaka stok verisi
            self.all_plates = db.get_all_plates()
            self.populate_plate_table()

            self.lbl_status.setText(f"Veriler güncellendi: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.lbl_status.setText(f"Hata: {e}")

    def update_stats(self):
        total_items = len(self.all_stocks)
        total_m2 = sum(s.get('quantity_m2', 0) for s in self.all_stocks)
        low_stock = sum(1 for s in self.all_stocks if s.get('quantity_m2', 0) < s.get('min_limit', 0))
        
        self.lbl_total_items.setText(f"Çeşit: {total_items}")
        self.lbl_total_m2.setText(f"Toplam Stok: {total_m2:,.0f} m²".replace(",", "."))
        self.lbl_low_stock.setText(f"Kritik Ürün: {low_stock}")

    def filter_table(self):
        search_txt = self.search_box.text().lower()
        filter_type = self.combo_filter.currentText()
        
        filtered_data = []
        for item in self.all_stocks:
            if search_txt and search_txt not in item['product_name'].lower():
                continue
                
            qty = item.get('quantity_m2', 0)
            limit = item.get('min_limit', 0)
            
            if filter_type == "Kritik Stoklar" and qty >= limit: continue
            if filter_type == "Yeterli Stoklar" and qty < limit: continue
                
            filtered_data.append(item)
            
        self.populate_table(filtered_data)

    def populate_table(self, data):
        self.table.setRowCount(0)
        self.table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            qty = item.get('quantity_m2', 0)
            limit = item.get('min_limit', 100)
            name = item.get('product_name', '-')
            last_updated = item.get('last_updated', '-')
            
            name_item = QTableWidgetItem(name)
            name_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row, 0, name_item)
            
            qty_item = QTableWidgetItem(f"{qty:.1f} m²")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if qty < limit:
                qty_item.setForeground(QColor(Colors.STOCK_CRIT))
                qty_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row, 1, qty_item)
            
            limit_item = QTableWidgetItem(f"{limit:.0f} m²")
            limit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            limit_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.table.setItem(row, 2, limit_item)
            
            max_val = max(limit * 3, qty * 1.2) 
            percent = int((qty / max_val) * 100) if max_val > 0 else 0
            
            bar_color = Colors.STOCK_GOOD
            if qty <= 0: bar_color = Colors.STOCK_CRIT
            elif qty < limit: bar_color = Colors.STOCK_LOW
            
            pbar = QProgressBar()
            pbar.setValue(min(percent, 100))
            pbar.setTextVisible(False)
            pbar.setFixedHeight(12)
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {Colors.GRID};
                    border: none;
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 3px;
                }}
            """)
            
            w = QWidget()
            l = QVBoxLayout(w)
            l.addWidget(pbar)
            l.setAlignment(Qt.AlignCenter)
            l.setContentsMargins(5, 0, 5, 0)
            self.table.setCellWidget(row, 3, w)
            
            status_text = "YETERLİ"
            status_color = Colors.STOCK_GOOD
            
            if qty <= 0:
                status_text = "TÜKENDİ"
                status_color = Colors.STOCK_CRIT
            elif qty < limit:
                status_text = "KRİTİK"
                status_color = Colors.STOCK_LOW
                
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(status_color))
            status_item.setFont(QFont("Segoe UI", 8, QFont.Bold))
            self.table.setItem(row, 4, status_item)
            
            try:
                if last_updated and '-' in str(last_updated):
                    dt = datetime.strptime(str(last_updated), "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%d.%m %H:%M")
                else: date_str = "-"
            except: date_str = str(last_updated)
            
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.table.setItem(row, 5, date_item)

    def populate_plate_table(self):
        """Plaka tablosunu doldur"""
        if not hasattr(self, 'all_plates'):
            self.all_plates = []

        self.plate_table.setRowCount(0)
        self.plate_table.setRowCount(len(self.all_plates))

        for row, plate in enumerate(self.all_plates):
            # Kalınlık
            thick_item = QTableWidgetItem(f"{plate.get('thickness', 0)} mm")
            thick_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            thick_item.setTextAlignment(Qt.AlignCenter)
            self.plate_table.setItem(row, 0, thick_item)

            # Cam Tipi
            type_item = QTableWidgetItem(plate.get('glass_type', '-'))
            type_item.setTextAlignment(Qt.AlignCenter)
            self.plate_table.setItem(row, 1, type_item)

            # Boyut
            width = plate.get('width', 0)
            height = plate.get('height', 0)
            size_item = QTableWidgetItem(f"{width} x {height}")
            size_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            size_item.setTextAlignment(Qt.AlignCenter)
            self.plate_table.setItem(row, 2, size_item)

            # Adet
            qty = plate.get('quantity', 0)
            qty_item = QTableWidgetItem(f"{qty} adet")
            qty_item.setTextAlignment(Qt.AlignCenter)
            if qty == 0:
                qty_item.setForeground(QColor(Colors.STOCK_CRIT))
            elif qty < 5:
                qty_item.setForeground(QColor(Colors.STOCK_LOW))
            else:
                qty_item.setForeground(QColor(Colors.STOCK_GOOD))
            qty_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.plate_table.setItem(row, 3, qty_item)

            # Toplam m²
            total_m2 = (width * height * qty) / 10000.0
            m2_item = QTableWidgetItem(f"{total_m2:.2f} m²")
            m2_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            m2_item.setForeground(QColor(Colors.ACCENT))
            self.plate_table.setItem(row, 4, m2_item)

            # Konum
            location = plate.get('location', '-')
            loc_item = QTableWidgetItem(location if location else '-')
            loc_item.setTextAlignment(Qt.AlignCenter)
            loc_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.plate_table.setItem(row, 5, loc_item)

            # Tarih
            created = plate.get('created_at', '-')
            try:
                if created and '-' in str(created):
                    dt = datetime.strptime(str(created), "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%d.%m %H:%M")
                else:
                    date_str = "-"
            except:
                date_str = str(created)

            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.plate_table.setItem(row, 6, date_item)

            # İşlem butonu (Sil)
            btn_delete = QPushButton("🗑️")
            btn_delete.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.STOCK_CRIT};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: #B71C1C;
                }}
            """)
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.clicked.connect(lambda checked, p_id=plate.get('id'): self.delete_plate(p_id))

            w = QWidget()
            l = QHBoxLayout(w)
            l.addWidget(btn_delete)
            l.setAlignment(Qt.AlignCenter)
            l.setContentsMargins(5, 2, 5, 2)
            self.plate_table.setCellWidget(row, 7, w)

    def delete_plate(self, plate_id):
        """Plaka silme işlemi"""
        if not db or not plate_id:
            return

        reply = QMessageBox.question(
            self,
            "Plaka Sil",
            "Bu plakayı silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Veritabanından sil
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM plates WHERE id = ?", (plate_id,))
                    conn.commit()

                self.lbl_status.setText("✓ Plaka silindi.")
                self.refresh_data()
            except Exception as e:
                self.lbl_status.setText(f"Hata: {e}")
                QMessageBox.warning(self, "Hata", f"Plaka silinirken hata oluştu: {e}")

    def add_stock_dialog(self):
        """Stok veya Plaka Giriş Seçimi"""
        if not db: return

        # Kullanıcıya seçim sunalım
        msg = QMessageBox(self)
        msg.setWindowTitle("Stok Giriş Türü")
        msg.setText("Hangi tür stok girişi yapmak istiyorsunuz?")
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Colors.BG};
            }}
            QLabel {{
                color: {Colors.TEXT};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #0B5EA8;
            }}
        """)

        btn_plate = msg.addButton("📦 Plaka Girişi", QMessageBox.AcceptRole)
        btn_general = msg.addButton("📊 Genel Stok (m²)", QMessageBox.AcceptRole)
        msg.addButton("İptal", QMessageBox.RejectRole)

        msg.exec()
        clicked = msg.clickedButton()

        if clicked == btn_plate:
            # Plaka girişi
            dialog = PlateEntryDialog(self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.result_data
                db.add_plate(
                    thickness=data['thickness'],
                    glass_type=data['glass_type'],
                    width=data['width'],
                    height=data['height'],
                    quantity=data['quantity'],
                    location=data['location']
                )
                self.lbl_status.setText(
                    f"✓ {data['quantity']} adet {data['thickness']}mm {data['glass_type']} "
                    f"plaka ({data['width']}x{data['height']} cm) eklendi."
                )
                self.refresh_data()

        elif clicked == btn_general:
            # Genel stok girişi (eski sistem)
            dialog = StockEntryDialog(self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.result_data
                db.add_stock(data['name'], data['qty'])
                self.lbl_status.setText(f"{data['qty']} m² {data['name']} eklendi.")
                self.refresh_data()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = StockView()
    win.resize(1000, 600)
    win.show()
    sys.exit(app.exec())