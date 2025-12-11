"""
EFES ROTA X - Haftalık Üretim Programı (Modernize Edilmiş)
Excel temalı, tablo bazlı görünüm.
Veriler 'SmartPlanner' simülasyonundan gelir, yani Karar Destek sıralamasıyla uyumludur.
"""

import sys
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QWidget, QFileDialog, 
    QMessageBox, QFrame, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon

try:
    from ui.theme import Theme
    from core.smart_planner import planner
    from core.pdf_engine import PDFEngine
except ImportError:
    pass

# --- RENKLER (DASHBOARD ILE AYNI) ---
class Colors:
    BG = "#FFFFFF"
    HEADER_BG = "#F8F9FA"
    BORDER = "#E0E0E0"
    TEXT = "#212529"
    TEXT_SECONDARY = "#6C757D"
    ACCENT = "#0F6CBD"       # Mavi
    SUCCESS = "#2E7D32"      # Yeşil

class WeeklyScheduleView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Haftalık Üretim Programı")
        self.resize(1100, 750)
        self.schedule_data = {}
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- BAŞLIK ---
        header_layout = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title = QLabel("Haftalık İş Emri Listesi")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Colors.TEXT};")
        
        sub = QLabel("Akıllı planlama motoruna göre simüle edilmiş üretim takvimi.")
        sub.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header_layout.addLayout(title_box)
        
        header_layout.addStretch()
        
        # PDF Butonu
        btn_print = QPushButton("PDF İndir")
        btn_print.setCursor(Qt.PointingHandCursor)
        btn_print.clicked.connect(self.export_to_pdf)
        btn_print.setFixedSize(120, 36)
        btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #0B5EA8; }}
        """)
        header_layout.addWidget(btn_print)
        
        # Kapat Butonu
        btn_close = QPushButton("Kapat")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_close.setFixedSize(80, 36)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {Colors.BORDER}; }}
        """)
        header_layout.addWidget(btn_close)
        
        layout.addLayout(header_layout)

        # --- SEKMELER ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER};
                background: {Colors.BG};
                border-radius: 4px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {Colors.TEXT_SECONDARY};
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
                margin-right: 4px;
                font-weight: 600;
                font-size: 12px;
            }}
            QTabBar::tab:hover {{
                color: {Colors.ACCENT};
                background-color: {Colors.HEADER_BG};
            }}
            QTabBar::tab:selected {{
                background: {Colors.HEADER_BG};
                color: {Colors.ACCENT};
                border-bottom: 2px solid {Colors.ACCENT};
            }}
        """)
        
        layout.addWidget(self.tabs)

    def load_data(self):
        """SmartPlanner'dan verileri çeker ve tabloları oluşturur"""
        if 'planner' not in globals() or planner is None:
            QMessageBox.warning(self, "Hata", "Planlama motoru bulunamadı!")
            return

        try:
            # Akıllı motordan veriyi çek (Karar Destek ile aynı mantığı kullanır)
            result = planner.calculate_forecast()
            
            # Sonuç formatı: (forecast_grid, details_grid, loads_grid, ...)
            # Bizim ihtiyacımız olan 'details_grid' (2. eleman)
            if isinstance(result, tuple) and len(result) >= 2:
                self.schedule_data = result[1]
                self.create_tabs()
            else:
                print("Veri formatı hatalı!")
                
        except Exception as e:
            print(f"Planlama verisi alınırken hata: {e}")

    def create_tabs(self):
        """7 Günlük sekmeleri oluşturur"""
        self.tabs.clear()
        today = datetime.now()
        tr_days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        
        # Makineleri alfabetik veya mantıksal sıraya dizmek için
        machines = sorted(list(self.schedule_data.keys()))
        
        # 7 Gün döngüsü
        for day_idx in range(7):
            day_date = today + timedelta(days=day_idx)
            day_name = tr_days[day_date.weekday()]
            tab_title = f"{day_name} ({day_date.strftime('%d.%m')})"
            
            # Her gün için bir tablo oluştur
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            
            table = self.create_day_table(day_idx, machines)
            page_layout.addWidget(table)
            
            self.tabs.addTab(page, tab_title)

    def create_day_table(self, day_idx, machines):
        """O güne ait işleri gösteren Excel benzeri tablo"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["İstasyon", "Sipariş Kodu", "Müşteri", "Ürün / Kalınlık", "m²"])
        
        # Tablo Ayarları
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QAbstractItemView.NoSelection) # Sadece izleme
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Stil
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG};
                gridline-color: {Colors.BORDER};
                border: none;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT_SECONDARY};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                border-right: 1px solid {Colors.BORDER};
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 6px;
                color: {Colors.TEXT};
                border-bottom: 1px solid {Colors.BORDER};
            }}
            QTableWidget::item:alternate {{
                background-color: #FAFAFA;
            }}
        """)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # İstasyon
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Kod
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Müşteri (Esnek)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Ürün
        header.setSectionResizeMode(4, QHeaderView.Fixed)            # m2
        table.setColumnWidth(4, 70)

        # Verileri Doldur
        row_count = 0
        
        # Her makine için o günkü işleri kontrol et
        for machine in machines:
            # Veri var mı?
            daily_jobs = []
            try:
                if len(self.schedule_data[machine]) > day_idx:
                    daily_jobs = self.schedule_data[machine][day_idx]
            except:
                continue
            
            if not daily_jobs:
                continue
                
            # İşleri tabloya ekle
            for job in daily_jobs:
                table.insertRow(row_count)
                
                # İstasyon (Renkli ve Kalın)
                item_station = QTableWidgetItem(machine)
                item_station.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item_station.setForeground(QColor(Colors.ACCENT))
                table.setItem(row_count, 0, item_station)
                
                # Kod
                table.setItem(row_count, 1, QTableWidgetItem(job.get('code', '-')))
                
                # Müşteri
                table.setItem(row_count, 2, QTableWidgetItem(job.get('customer', '-')))
                
                # Batch Bilgisi (Örn: 4mm) veya Ürün
                # SmartPlanner'dan 'batch' veya 'product' bilgisi gelebilir
                batch_info = job.get('batch', '') 
                if not batch_info:
                    batch_info = "Cam" # Varsayılan
                table.setItem(row_count, 3, QTableWidgetItem(batch_info))
                
                # m2
                m2 = job.get('m2', 0)
                item_m2 = QTableWidgetItem(f"{m2:.1f}")
                item_m2.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_count, 4, item_m2)
                
                row_count += 1
                
        if row_count == 0:
            # Boş gün uyarısı
            table.setRowCount(1)
            item = QTableWidgetItem("Bugün için planlanmış iş bulunmamaktadır.")
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor(Colors.TEXT_SECONDARY))
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, 5)
            
        return table

    def export_to_pdf(self):
        """Listeyi PDF olarak kaydeder"""
        default_name = f"Haftalik_Plan_{datetime.now().strftime('%Y%m%d')}.pdf"
        filename, _ = QFileDialog.getSaveFileName(self, "Listeyi Kaydet", default_name, "PDF Files (*.pdf)")
        
        if not filename: return

        engine = PDFEngine(filename)
        
        # Not: self.schedule_data zaten SmartPlanner formatındadır
        success, msg = engine.generate_weekly_schedule_pdf(self.schedule_data)
        
        if success:
            QMessageBox.information(self, "Başarılı", f"Rapor kaydedildi:\n{filename}")
            try:
                import os
                os.startfile(filename)
            except:
                pass
        else:
            QMessageBox.critical(self, "Hata", f"PDF hatası:\n{msg}")