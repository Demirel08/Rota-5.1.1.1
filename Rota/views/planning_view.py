"""
EFES ROTA X - İş Yükü ve Kapasite Planlama (Delegate Düzeltildi)
- İstasyon isimlerinin görünmeme sorunu çözüldü (Delegate column 0 check).
- Isı haritası renkleri mavi tonlarında sabitlendi.
"""

import sys
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QPushButton, QAbstractItemView, QStyledItemDelegate, 
    QDialog, QListWidget, QMessageBox, QApplication, QStyle, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush

# Modülleri güvenli şekilde içeri al
factory_config = None
planner = None
WeeklyScheduleView = None

try:
    from ui.theme import Theme
    from core.smart_planner import planner 
    from core.factory_config import factory_config 
    try:
        from views.weekly_schedule_dialog import WeeklyScheduleView
    except ImportError:
        pass
except ImportError:
    pass


# =============================================================================
# TEMA RENKLERİ (Sadeleştirilmiş Mavi Tonlar)
# =============================================================================
class Colors:
    BG = "#FFFFFF"
    HEADER_BG = "#F8F9FA"
    BORDER = "#E0E0E0"
    TEXT = "#212529"
    TEXT_SECONDARY = "#6C757D"
    
    # Isı Haritası Renkleri (Sadece Mavi Tonları - Kırmızı Yok)
    LOAD_EMPTY = "#FFFFFF"    # %0 (Beyaz)
    LOAD_LOW = "#E3F2FD"      # %1-40 (Çok Açık Mavi)
    LOAD_MED = "#64B5F6"      # %40-80 (Orta Mavi)
    LOAD_FULL = "#1565C0"     # %80-100+ (Koyu Lacivert - Tam Dolu)


# =============================================================================
# ÖZEL HÜCRE BOYAYICI (DÜZELTİLDİ)
# =============================================================================
class GanttDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # --- KRİTİK DÜZELTME ---
        # Eğer 0. sütunsa (İstasyon Adları), özel boyama YAPMA! Standart boyamayı kullan.
        # Böylece istasyon isimleri silinmez, olduğu gibi görünür.
        if index.column() == 0:
            super().paint(painter, option, index)
            return

        # Diğer sütunlar (Günler) için Isı Haritası boyaması:
        percent = index.data(Qt.UserRole)
        text = index.data(Qt.DisplayRole)
        
        if percent is None:
            percent = 0

        painter.save()
        
        # 1. Arka Plan Rengi Belirle
        if percent <= 0:
            bg_color = QColor(Colors.LOAD_EMPTY)
            text_color = QColor(Colors.TEXT_SECONDARY)
        elif percent <= 40:
            bg_color = QColor(Colors.LOAD_LOW)
            text_color = QColor(Colors.TEXT)
        elif percent <= 80:
            bg_color = QColor(Colors.LOAD_MED)
            text_color = QColor("#000000")
        else:
            # %80 ve üzeri artık "TAM DOLU" (Mavi)
            bg_color = QColor(Colors.LOAD_FULL)
            text_color = QColor("#FFFFFF")
            
        # Seçili durum kontrolü
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#B4D7FF")) # Seçim rengi
            pen = QPen(QColor(Colors.LOAD_FULL), 2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1,1,-1,-1))
        else:
            painter.fillRect(option.rect, bg_color)
            # Hücre çizgileri
            painter.setPen(QColor(Colors.BORDER))
            painter.drawRect(option.rect)

        # 2. Metin Yazdırma
        if text and percent > 0:
            painter.setPen(text_color)
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            
            # Eğer %100'ü aşıyorsa bile sadece %100 gösterelim
            display_pct = min(int(percent), 100)
            display_text = f"%{display_pct}"
            
            painter.drawText(option.rect, Qt.AlignCenter, display_text)

        painter.restore()


# =============================================================================
# DETAY PENCERESİ
# =============================================================================
class DayDetailDialog(QDialog):
    def __init__(self, station, date_str, orders, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"İş Listesi: {station} - {date_str}")
        self.setFixedSize(500, 600)
        self.setStyleSheet(f"background-color: {Colors.BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel(f"{station} Programı")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(title)

        sub = QLabel(f"Tarih: {date_str}")
        sub.setStyleSheet(f"font-size: 13px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(sub)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {Colors.BORDER};")
        layout.addWidget(line)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                background-color: {Colors.BG};
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {Colors.BORDER};
                color: {Colors.TEXT};
            }}
        """)

        if not orders:
            self.list_widget.addItem("Bu tarih için planlanmış iş bulunamadı.")
        else:
            total_m2 = 0
            for order in orders:
                code = order.get('code', '-')
                cust = order.get('customer', '-')
                m2 = order.get('m2', 0)
                notes = order.get('notes', '').strip()
                total_m2 += m2

                # Not varsa emoji ile göster
                if notes:
                    item_text = f"📝 {code} - {cust} ({m2:.1f} m²)"
                    from PySide6.QtWidgets import QListWidgetItem
                    item = QListWidgetItem(item_text)
                    item.setToolTip(f"Not: {notes}")
                    self.list_widget.addItem(item)
                else:
                    self.list_widget.addItem(f"{code} - {cust} ({m2:.1f} m²)")
            
            total_lbl = QLabel(f"Toplam Yük: {total_m2:.1f} m²")
            total_lbl.setStyleSheet(f"font-weight: bold; color: {Colors.LOAD_FULL}; margin-top: 5px;")
            layout.addWidget(total_lbl)

        layout.addWidget(self.list_widget)

        btn = QPushButton("Kapat")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.accept)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BORDER};
                color: {Colors.TEXT};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #D6D6D6; }}
        """)
        layout.addWidget(btn)


# =============================================================================
# ANA PLANLAMA EKRANI
# =============================================================================
class PlanningView(QWidget):
    def __init__(self):
        super().__init__()

        self.DAYS_RANGE = 30
        self.cached_details = {}

        # --- MAKİNE LİSTESİNİ YÜKLETablo başlatma yap
        self.load_machines()

        self.setup_ui()
        self.init_table_structure()
        self.table.setItemDelegate(GanttDelegate())

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_plan)
        self.timer.start(10000)
        self.refresh_plan()

    def load_machines(self):
        """Makina listesini factory_config'den yükle"""
        self.machines = []

        if factory_config:
            try:
                # Sevkiyat hariç listeyi al
                self.machines = factory_config.get_station_order(include_shipping=False)
            except:
                pass

        # Eğer liste boşsa varsayılanları yükle
        if not self.machines:
            self.machines = [
                "INTERMAC", "LIVA KESIM", "LAMINE KESIM",
                "CNC RODAJ", "DOUBLEDGER", "ZIMPARA",
                "TESIR A1", "TESIR B1", "DELİK", "OYGU",
                "TEMPER A1", "TEMPER B1", "TEMPER BOMBE",
                "LAMINE A1", "ISICAM B1"
            ]

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(f"background-color: {Colors.HEADER_BG}; border-bottom: 1px solid {Colors.BORDER};")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("İş Yükü & Kapasite Planlama")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.TEXT};")
        tb_layout.addWidget(title)
        
        tb_layout.addStretch()
        
        # Renk Lejantı
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)
        
        legends = [
            ("Boş", Colors.LOAD_EMPTY, Colors.TEXT_SECONDARY),
            ("Normal", Colors.LOAD_MED, "black"),
            ("Tam Dolu", Colors.LOAD_FULL, "white")
        ]
        
        for text, bg, fg in legends:
            lbl = QLabel(f" {text} ")
            lbl.setStyleSheet(f"""
                background-color: {bg}; 
                color: {fg}; 
                border-radius: 3px; 
                font-size: 10px; 
                padding: 2px 6px; 
                font-weight: bold;
                border: 1px solid {Colors.BORDER};
            """)
            legend_layout.addWidget(lbl)
            
        tb_layout.addLayout(legend_layout)
        tb_layout.addSpacing(20)

        if WeeklyScheduleView:
            btn_list = QPushButton("Haftalık Liste")
            btn_list.setCursor(Qt.PointingHandCursor)
            btn_list.clicked.connect(self.open_weekly_schedule)
            btn_list.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 4px;
                    padding: 6px 12px;
                    color: {Colors.TEXT};
                    font-size: 11px;
                }}
                QPushButton:hover {{ background-color: {Colors.HEADER_BG}; }}
            """)
            tb_layout.addWidget(btn_list)

        btn_refresh = QPushButton("Yenile")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_plan)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.LOAD_FULL};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #0D47A1; }}
        """)
        tb_layout.addWidget(btn_refresh)
        
        layout.addWidget(toolbar)

        # Tablo
        self.table = QTableWidget()
        self.table.cellClicked.connect(self.on_cell_clicked)
        layout.addWidget(self.table)

    def init_table_structure(self):
        columns = ["İSTASYON"]
        today = datetime.now()
        tr_days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        
        for i in range(self.DAYS_RANGE):
            day_date = today + timedelta(days=i)
            col_name = f"{day_date.strftime('%d.%m')}\n{tr_days[day_date.weekday()]}"
            columns.append(col_name)
            
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(self.machines))
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setShowGrid(False) 
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 180)
        
        for i in range(1, self.DAYS_RANGE + 1):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
            self.table.setColumnWidth(i, 60)

        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT_SECONDARY};
                font-weight: bold;
                font-size: 11px;
                padding: 6px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                border-right: 1px solid {Colors.BORDER};
            }}
        """)
        self.table.setStyleSheet(f"border: none; background-color: {Colors.BG};")

        for row_idx, machine_name in enumerate(self.machines):
            item = QTableWidgetItem(machine_name)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item.setFlags(Qt.ItemIsEnabled)
            # İstasyon adı hücresi, daha görünür olması için koyu renk
            item.setBackground(QColor(Colors.HEADER_BG))
            item.setForeground(QColor("#000000")) 
            item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(row_idx, 0, item)

    def refresh_plan(self):
        """Planlama verilerini yenile"""
        # Factory config'i yenile (kapasite değişikliklerini al)
        if factory_config:
            try:
                factory_config.refresh()
            except:
                pass

        # Makina listesini yeniden yükle (isim değişiklikleri için)
        old_machines = self.machines.copy()
        self.load_machines()

        # Eğer makina listesi değiştiyse tabloyu yeniden oluştur
        if old_machines != self.machines:
            self.init_table_structure()

        if 'planner' not in globals() or planner is None:
            return

        try:
            result = planner.calculate_forecast()
            if isinstance(result, tuple) and len(result) >= 3:
                forecast, details, loads = result
                self.cached_details = details
            else:
                return
        except Exception as e:
            print(f"Planlama hatası: {e}")
            return

        for row_idx, machine_name in enumerate(self.machines):
            machine_key = machine_name.upper()

            daily_percents = forecast.get(machine_key, [0]*self.DAYS_RANGE)
            daily_loads = loads.get(machine_key, [0]*self.DAYS_RANGE)

            for day_idx in range(self.DAYS_RANGE):
                col_idx = day_idx + 1

                percent = daily_percents[day_idx] if day_idx < len(daily_percents) else 0
                load = daily_loads[day_idx] if day_idx < len(daily_loads) else 0

                text = ""
                if percent > 0:
                    text = f"{int(load)} m²"

                item = self.table.item(row_idx, col_idx)
                if not item:
                    item = QTableWidgetItem()
                    self.table.setItem(row_idx, col_idx, item)

                item.setData(Qt.DisplayRole, text)
                item.setData(Qt.UserRole, percent)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable) 

    def on_cell_clicked(self, row, col):
        if col == 0: return
        
        day_idx = col - 1
        machine_name = self.machines[row]
        machine_key = machine_name.upper()
        
        if machine_key in self.cached_details:
            try:
                orders = self.cached_details[machine_key][day_idx]
                if not orders: return 
                
                today = datetime.now()
                target_date = today + timedelta(days=day_idx)
                
                dialog = DayDetailDialog(machine_name, target_date.strftime("%d.%m.%Y"), orders, self)
                dialog.exec()
            except Exception as e:
                print(f"Detay hatası: {e}")

    def open_weekly_schedule(self):
        if WeeklyScheduleView:
            dialog = WeeklyScheduleView(self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Hata", "Haftalık Liste modülü yüklenemedi.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = PlanningView()
    win.resize(1200, 600)
    win.show()
    sys.exit(app.exec())