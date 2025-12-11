"""
EFES ROTA X - Raporlama Merkezi
Excel temali, kompakt tasarim
"""

import sys
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QPushButton, QAbstractItemView, QDateEdit, 
    QComboBox, QMessageBox, QFileDialog, QTabWidget, 
    QFrame, QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont

try:
    from core.db_manager import db
except ImportError:
    db = None


# =============================================================================
# EXCEL TEMASI
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
# RAPORLAMA EKRANI
# =============================================================================
class ReportView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # HEADER
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("Raporlama Merkezi")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.TEXT};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)

        # SEKMELER
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {Colors.BG};
            }}
            QTabBar::tab {{
                background: {Colors.HEADER_BG};
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                padding: 8px 20px;
                margin-right: 2px;
                font-size: 11px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QTabBar::tab:selected {{
                background: {Colors.BG};
                color: {Colors.ACCENT};
                font-weight: bold;
                border-bottom: 2px solid {Colors.ACCENT};
            }}
            QTabBar::tab:hover {{
                background: {Colors.BG};
            }}
        """)

        # Sekme 1: Uretim Hareketleri
        self.tab_logs = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.tab_logs, "Uretim Hareketleri")

        # Sekme 2: Personel Performans
        self.tab_perf = QWidget()
        self.setup_performance_tab()
        self.tabs.addTab(self.tab_perf, "Personel Performansi")

        # Sekme 3: Fire Analizi
        self.tab_fire = QWidget()
        self.setup_fire_tab()
        self.tabs.addTab(self.tab_fire, "Fire Analizi")

        layout.addWidget(self.tabs)

    # =========================================================================
    # SEKME 1: URETIM HAREKETLERI
    # =========================================================================
    def setup_logs_tab(self):
        layout = QVBoxLayout(self.tab_logs)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Filtre bari
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(16)
        
        # Tarih alanlari
        date_style = f"""
            QDateEdit {{
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 6px 10px;
                font-size: 11px;
                background-color: {Colors.BG};
                min-width: 110px;
            }}
            QDateEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
        """
        
        lbl_start = QLabel("Baslangic:")
        lbl_start.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY}; background: transparent;")
        filter_layout.addWidget(lbl_start)
        
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        self.date_start.setDisplayFormat("dd.MM.yyyy")
        self.date_start.setStyleSheet(date_style)
        filter_layout.addWidget(self.date_start)
        
        lbl_end = QLabel("Bitis:")
        lbl_end.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY}; background: transparent;")
        filter_layout.addWidget(lbl_end)
        
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setDisplayFormat("dd.MM.yyyy")
        self.date_end.setStyleSheet(date_style)
        filter_layout.addWidget(self.date_end)
        
        filter_layout.addStretch()
        
        # Sorgula butonu
        btn_query = QPushButton("Sorgula")
        btn_query.setFixedHeight(32)
        btn_query.setCursor(Qt.PointingHandCursor)
        btn_query.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 4px;
                padding: 0 20px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_query.clicked.connect(self.query_logs)
        filter_layout.addWidget(btn_query)
        
        # Excel export butonu
        btn_export = QPushButton("Excel'e Aktar")
        btn_export.setFixedHeight(32)
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.ACCENT};
                border-radius: 4px;
                padding: 0 16px;
                color: {Colors.ACCENT};
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.ACCENT};
                color: white;
            }}
        """)
        btn_export.clicked.connect(self.export_logs)
        filter_layout.addWidget(btn_export)
        
        layout.addWidget(filter_frame)

        # Sonuc bilgisi
        self.lbl_result_count = QLabel("")
        self.lbl_result_count.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.lbl_result_count)

        # Tablo
        self.table_logs = QTableWidget()
        self.table_logs.setColumnCount(6)
        self.table_logs.setHorizontalHeaderLabels(["Tarih", "Siparis", "Musteri", "Istasyon", "Islem", "Operator"])
        self.table_logs.verticalHeader().setVisible(False)
        self.table_logs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_logs.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_logs.setColumnWidth(0, 140)
        self.table_logs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_logs.setAlternatingRowColors(True)
        self.table_logs.setStyleSheet(self._get_table_style())
        layout.addWidget(self.table_logs)

    def query_logs(self):
        if not db:
            return
            
        d1 = self.date_start.date().toString("yyyy-MM-dd")
        d2 = self.date_end.date().toString("yyyy-MM-dd")
        data = db.get_production_report_data(d1, d2)
        
        self.table_logs.setRowCount(len(data))
        self.lbl_result_count.setText(f"{len(data)} kayit bulundu")
        
        for r, item in enumerate(data):
            # Tarih
            date_item = QTableWidgetItem(str(item.get('islem_tarihi', '')))
            date_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.table_logs.setItem(r, 0, date_item)
            
            # Siparis
            order_item = QTableWidgetItem(str(item.get('siparis_no', '')))
            order_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_logs.setItem(r, 1, order_item)
            
            # Musteri
            self.table_logs.setItem(r, 2, QTableWidgetItem(str(item.get('musteri', ''))))
            
            # Istasyon
            station_item = QTableWidgetItem(str(item.get('istasyon', '')))
            station_item.setForeground(QColor(Colors.ACCENT))
            self.table_logs.setItem(r, 3, station_item)
            
            # Islem
            action = str(item.get('islem', ''))
            action_item = QTableWidgetItem(action)
            if 'Fire' in action or 'Hata' in action:
                action_item.setForeground(QColor(Colors.CRITICAL))
            elif 'Tamamla' in action or 'Yapıldı' in action:
                action_item.setForeground(QColor(Colors.SUCCESS))
            self.table_logs.setItem(r, 4, action_item)
            
            # Operator
            self.table_logs.setItem(r, 5, QTableWidgetItem(str(item.get('operator', ''))))

    def export_logs(self):
        """Loglari Excel'e aktar"""
        if self.table_logs.rowCount() == 0:
            QMessageBox.warning(self, "Uyari", "Aktarilacak veri yok. Once sorgulama yapin.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Excel Dosyasi Kaydet", 
            f"uretim_raporu_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Uretim Hareketleri"
                
                # Basliklar
                headers = ["Tarih", "Siparis", "Musteri", "Istasyon", "Islem", "Operator"]
                ws.append(headers)
                
                # Veriler
                for row in range(self.table_logs.rowCount()):
                    row_data = []
                    for col in range(self.table_logs.columnCount()):
                        item = self.table_logs.item(row, col)
                        row_data.append(item.text() if item else "")
                    ws.append(row_data)
                
                wb.save(file_path)
                QMessageBox.information(self, "Basarili", f"Rapor kaydedildi:\n{file_path}")
            except ImportError:
                QMessageBox.critical(self, "Hata", "openpyxl kutuphanesi yuklu degil.\npip install openpyxl")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayit hatasi: {e}")

    # =========================================================================
    # SEKME 2: PERSONEL PERFORMANSI
    # =========================================================================
    def setup_performance_tab(self):
        layout = QVBoxLayout(self.tab_perf)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Ust bar
        top_bar = QHBoxLayout()
        
        info_label = QLabel("Son 30 gundeki operator performanslari")
        info_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        top_bar.addWidget(info_label)
        
        top_bar.addStretch()
        
        btn_refresh = QPushButton("Yenile")
        btn_refresh.setFixedHeight(32)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 4px;
                padding: 0 20px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_refresh.clicked.connect(self.refresh_performance)
        top_bar.addWidget(btn_refresh)
        
        layout.addLayout(top_bar)
        
        # Tablo
        self.table_perf = QTableWidget()
        self.table_perf.setColumnCount(4)
        self.table_perf.setHorizontalHeaderLabels(["Operator", "Tamamlanan Islem", "Performans", ""])
        self.table_perf.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_perf.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_perf.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_perf.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_perf.setColumnWidth(1, 130)
        self.table_perf.setColumnWidth(2, 80)
        self.table_perf.verticalHeader().setVisible(False)
        self.table_perf.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_perf.setAlternatingRowColors(True)
        self.table_perf.setStyleSheet(self._get_table_style())
        layout.addWidget(self.table_perf)

    def refresh_performance(self):
        if not db:
            return
            
        try:
            data = db.get_operator_performance(days=30)
        except:
            QMessageBox.warning(self, "Uyari", "Performans verisi alinamadi.")
            return
            
        if not data:
            self.table_perf.setRowCount(0)
            return
            
        self.table_perf.setRowCount(len(data))
        max_val = data[0]['toplam_adet'] if data else 1
        
        for r, item in enumerate(data):
            # Operator adi
            name_item = QTableWidgetItem(str(item.get('operator_name', '')))
            name_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_perf.setItem(r, 0, name_item)
            
            # Tamamlanan islem
            qty = item.get('toplam_adet', 0)
            qty_item = QTableWidgetItem(f"{qty} adet")
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.table_perf.setItem(r, 1, qty_item)
            
            # Performans skoru
            score_val = int((qty / max_val) * 100) if max_val > 0 else 0
            score_item = QTableWidgetItem(f"%{score_val}")
            score_item.setTextAlignment(Qt.AlignCenter)
            
            if score_val >= 80:
                score_item.setForeground(QColor(Colors.SUCCESS))
            elif score_val >= 50:
                score_item.setForeground(QColor(Colors.WARNING))
            else:
                score_item.setForeground(QColor(Colors.CRITICAL))
            score_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_perf.setItem(r, 2, score_item)
            
            # Progress bar
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(score_val)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            
            if score_val >= 80:
                bar_color = Colors.SUCCESS
            elif score_val >= 50:
                bar_color = Colors.WARNING
            else:
                bar_color = Colors.CRITICAL
                
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {Colors.GRID};
                    border: none;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 4px;
                }}
            """)
            self.table_perf.setCellWidget(r, 3, bar)
            self.table_perf.setRowHeight(r, 40)

    # =========================================================================
    # SEKME 3: FIRE ANALIZI
    # =========================================================================
    def setup_fire_tab(self):
        layout = QVBoxLayout(self.tab_fire)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Uyari kutusu
        warning_frame = QFrame()
        warning_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CRITICAL_BG};
                border: 1px solid {Colors.CRITICAL};
                border-radius: 4px;
            }}
        """)
        warning_layout = QHBoxLayout(warning_frame)
        warning_layout.setContentsMargins(12, 10, 12, 10)
        
        warning_icon = QLabel("⚠")
        warning_icon.setStyleSheet(f"font-size: 16px; color: {Colors.CRITICAL};")
        warning_layout.addWidget(warning_icon)
        
        warning_text = QLabel("Fire ve hata kayitlari asagida istasyon bazli listelenmektedir.")
        warning_text.setStyleSheet(f"font-size: 11px; color: {Colors.CRITICAL};")
        warning_layout.addWidget(warning_text)
        warning_layout.addStretch()
        
        layout.addWidget(warning_frame)
        
        # Ust bar
        top_bar = QHBoxLayout()
        
        self.lbl_total_fire = QLabel("")
        self.lbl_total_fire.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.CRITICAL};")
        top_bar.addWidget(self.lbl_total_fire)
        
        top_bar.addStretch()
        
        btn_refresh = QPushButton("Analizi Guncelle")
        btn_refresh.setFixedHeight(32)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CRITICAL};
                border: none;
                border-radius: 4px;
                padding: 0 20px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #A00000;
            }}
        """)
        btn_refresh.clicked.connect(self.refresh_fire)
        top_bar.addWidget(btn_refresh)
        
        layout.addLayout(top_bar)
        
        # Tablo
        self.table_fire = QTableWidget()
        self.table_fire.setColumnCount(3)
        self.table_fire.setHorizontalHeaderLabels(["Istasyon", "Fire Adedi", "Oran"])
        self.table_fire.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_fire.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_fire.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_fire.setColumnWidth(1, 120)
        self.table_fire.verticalHeader().setVisible(False)
        self.table_fire.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_fire.setAlternatingRowColors(True)
        self.table_fire.setStyleSheet(self._get_table_style())
        layout.addWidget(self.table_fire)

    def refresh_fire(self):
        if not db:
            return
            
        try:
            data = db.get_fire_analysis_data()
        except:
            QMessageBox.warning(self, "Uyari", "Fire verisi alinamadi.")
            return
            
        if not data:
            self.table_fire.setRowCount(0)
            self.lbl_total_fire.setText("Toplam: 0 adet fire")
            return
        
        total_fire = sum(item.get('fire_adedi', 0) for item in data)
        self.lbl_total_fire.setText(f"Toplam: {total_fire} adet fire")
        
        self.table_fire.setRowCount(len(data))
        
        for r, item in enumerate(data):
            # Istasyon
            station_item = QTableWidgetItem(str(item.get('station_name', '')))
            station_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table_fire.setItem(r, 0, station_item)
            
            # Fire adedi
            fire_count = item.get('fire_adedi', 0)
            qty_item = QTableWidgetItem(f"{fire_count} adet")
            qty_item.setTextAlignment(Qt.AlignCenter)
            qty_item.setForeground(QColor(Colors.CRITICAL))
            qty_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_fire.setItem(r, 1, qty_item)
            
            # Oran bar
            ratio = (fire_count / total_fire * 100) if total_fire > 0 else 0
            
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(ratio))
            bar.setFormat(f"%{ratio:.1f}")
            bar.setFixedHeight(18)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {Colors.GRID};
                    border: none;
                    border-radius: 4px;
                    text-align: center;
                    font-size: 10px;
                    color: {Colors.TEXT};
                }}
                QProgressBar::chunk {{
                    background-color: {Colors.CRITICAL};
                    border-radius: 4px;
                }}
            """)
            self.table_fire.setCellWidget(r, 2, bar)
            self.table_fire.setRowHeight(r, 36)

    # =========================================================================
    # ORTAK STIL
    # =========================================================================
    def _get_table_style(self):
        return f"""
            QTableWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                gridline-color: {Colors.GRID};
                font-size: 11px;
                background-color: {Colors.BG};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Colors.GRID};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.SELECTION};
                color: {Colors.TEXT};
            }}
            QTableWidget::item:alternate {{
                background-color: {Colors.ROW_ALT};
            }}
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                border: none;
                border-bottom: 2px solid {Colors.BORDER};
                border-right: 1px solid {Colors.GRID};
                padding: 10px 8px;
                font-size: 11px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """