import sys
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QPushButton, QLineEdit, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

try:
    from core.db_manager import db
    from ui.theme import Theme
except ImportError:
    pass

class LogsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- BAŞLIK ---
        header = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title = QLabel("İŞLEM GEÇMİŞİ (LOG KAYITLARI)")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {Theme.TEXT_DARK};")
        sub = QLabel("Fabrikadaki tüm ayak izleri burada saklanır.")
        sub.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        
        header.addLayout(title_box)
        header.addStretch()
        
        # Arama Kutusu
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 Sipariş Kodu veya Personel Ara...")
        self.inp_search.setFixedWidth(300)
        self.inp_search.setStyleSheet("""
            QLineEdit { border: 1px solid #BDC3C7; border-radius: 15px; padding: 8px 15px; background-color: white; }
            QLineEdit:focus { border: 1px solid #3498DB; }
        """)
        self.inp_search.textChanged.connect(self.search_logs) # Yazdıkça ara
        header.addWidget(self.inp_search)
        
        # Yenile Butonu
        btn_refresh = QPushButton("⟳ YENİLE")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_data)
        btn_refresh.setStyleSheet("padding: 8px 15px; background-color: #2C3E50; color: white; border-radius: 6px; font-weight: bold;")
        header.addWidget(btn_refresh)
        
        layout.addLayout(header)

        # --- LOG TABLOSU ---
        self.table = QTableWidget()
        
        columns = ["TARİH / SAAT", "PERSONEL", "İSTASYON", "DURUM", "SİPARİŞ KODU", "MÜŞTERİ"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Görünüm Ayarları
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False) # Yatay çizgiler daha şık durur
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        
        # Header
        header_obj = self.table.horizontalHeader()
        header_obj.setSectionResizeMode(QHeaderView.Stretch)
        header_obj.setStyleSheet("QHeaderView::section { background-color: #ECF0F1; color: #2C3E50; font-weight: bold; padding: 8px; border: none; }")
        
        # Satır stilleri
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #BDC3C7; border-radius: 6px; gridline-color: #F2F3F4; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid #F2F3F4; }
        """)
        
        layout.addWidget(self.table)

    def refresh_data(self):
        """Tüm logları getir"""
        data = db.get_system_logs()
        self.fill_table(data)

    def search_logs(self):
        """Arama yap"""
        keyword = self.inp_search.text().strip()
        if not keyword:
            self.refresh_data()
            return
            
        data = db.search_logs(keyword)
        self.fill_table(data)

    def fill_table(self, data):
        """Tabloyu doldurur"""
        self.table.setRowCount(0)
        self.table.setRowCount(len(data))
        
        for row_idx, item in enumerate(data):
            # Tarih Formatı (YYYY-MM-DD HH:MM:SS -> DD.MM HH:MM)
            raw_date = item['timestamp']
            try:
                dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d.%m.%Y  %H:%M")
            except:
                date_str = raw_date

            # 1. Tarih
            cell_date = QTableWidgetItem(date_str)
            cell_date.setForeground(QColor("#7F8C8D")) # Gri tarih
            cell_date.setFont(QFont("Consolas", 10))
            self.table.setItem(row_idx, 0, cell_date)
            
            # 2. Personel
            cell_user = QTableWidgetItem(str(item['operator_name']).upper())
            cell_user.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row_idx, 1, cell_user)
            
            # 3. İstasyon
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(item['station_name'])))
            
            # 4. Durum (Renkli)
            action = str(item['action'])
            cell_action = QTableWidgetItem(action)
            cell_action.setFont(QFont("Segoe UI", 10, QFont.Bold))
            
            if "Tamamlandi" in action:
                cell_action.setText("✅ TAMAMLANDI")
                cell_action.setForeground(QColor("#27AE60"))
            elif "Fire" in action or "Kirildi" in action:
                cell_action.setText("🔥 FİRE / KIRIK")
                cell_action.setForeground(QColor("#C0392B"))
            else:
                cell_action.setForeground(QColor("#3498DB"))
                
            self.table.setItem(row_idx, 3, cell_action)
            
            # 5. Sipariş
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(item['order_code'])))
            
            # 6. Müşteri
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(item['customer_name'])))