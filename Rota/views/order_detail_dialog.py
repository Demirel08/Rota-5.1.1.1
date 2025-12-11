"""
EFES ROTA X - Siparis Detay Dialogu
Excel temali, patron odakli tasarim

Patron icin kritik bilgiler:
- Siparis nerede? (hangi istasyonda)
- Ne kadar kaldi? (tamamlanma yuzdesi)
- Tahmini bitis tarihi
- Gecikme riski var mi?
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QScrollArea, QWidget,
    QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime, timedelta

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
# FABRIKA BILGILERI
# =============================================================================
class FactoryConfig:
    """Fabrika yapilandirmasi"""
    
    STATION_ORDER = [
        "INTERMAC", "LIVA KESIM", "LAMINE KESIM",
        "CNC RODAJ", "DOUBLEDGER", "ZIMPARA",
        "TESIR A1", "TESIR B1", "TESIR B1-1", "TESIR B1-2", "DELIK", "OYGU",
        "TEMPER A1", "TEMPER B1", "TEMPER BOMBE",
        "LAMINE A1", "ISICAM B1", "KUMLAMA",
        "SEVKIYAT"
    ]
    
    @classmethod
    def get_station_index(cls, station):
        try:
            return cls.STATION_ORDER.index(station)
        except ValueError:
            return 999
    
    @classmethod
    def get_capacity(cls, station):
        """Veritabanindan kapasite cek"""
        if db:
            try:
                caps = db.get_all_capacities()
                return caps.get(station, 500)
            except:
                pass
        return 500  # Varsayilan


# =============================================================================
# ANA DIALOG
# =============================================================================
class OrderDetailDialog(QDialog):
    """Siparis Detay Dialogu"""
    
    def __init__(self, order_code, parent=None):
        super().__init__(parent)
        self.order_code = order_code
        self.order = {}
        self.station_progress = {}  # {station_name: completed_qty}
        
        self.setWindowTitle(f"Siparis: {order_code}")
        self.setMinimumSize(650, 550)
        self.resize(700, 600)
        
        self.load_order_data()
        self.setup_ui()
        
        # Canli yenileme (3 saniye)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(3000)
    
    def load_order_data(self):
        """Veritabanindan siparis bilgilerini cek"""
        if not db:
            return
        
        try:
            # Siparis bilgilerini al
            self.order = db.get_order_by_code(self.order_code) or {}
            
            if not self.order:
                return
            
            order_id = self.order.get('id')
            if not order_id:
                return
            
            # Rota istasyonlarini al
            route = self.order.get('route', '')
            stations = [s.strip() for s in route.split(',') if s.strip()]
            
            # Her istasyonun ilerlemesini db.get_station_progress ile al
            self.station_progress = {}
            for station in stations:
                done = db.get_station_progress(order_id, station)
                self.station_progress[station] = done
                
        except Exception as e:
            print(f"Siparis yukleme hatasi: {e}")
    
    def refresh_data(self):
        """Verileri yenile ve UI'i guncelle"""
        if not db or not self.order:
            return
        
        order_id = self.order.get('id')
        if not order_id:
            return
        
        try:
            # Guncel siparis bilgilerini al
            updated_order = db.get_order_by_code(self.order_code)
            if updated_order:
                self.order = updated_order
            
            # Istasyon ilerlemelerini guncelle
            route = self.order.get('route', '')
            stations = [s.strip() for s in route.split(',') if s.strip()]
            
            for station in stations:
                done = db.get_station_progress(order_id, station)
                self.station_progress[station] = done
            
            # UI'i yeniden olustur
            self.rebuild_content()
            
        except Exception as e:
            print(f"Yenileme hatasi: {e}")
    
    def rebuild_content(self):
        """Icerik alanini yeniden olustur"""
        # Scroll area icindeki content'i bul ve guncelle
        if hasattr(self, 'content_widget') and self.content_widget:
            # Mevcut layout'u temizle
            layout = self.content_widget.layout()
            if layout:
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                
                # Yeni icerikleri ekle
                if self.order:
                    info_section = self._create_info_section()
                    layout.addWidget(info_section)
                    
                    route_section = self._create_route_section()
                    layout.addWidget(route_section)
                    
                    estimate_section = self._create_estimate_section()
                    layout.addWidget(estimate_section)
                
                layout.addStretch()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG};
            }}
            QLabel {{
                color: {Colors.TEXT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Ozet cubugu
        if self.order:
            summary = self._create_summary_bar()
            layout.addWidget(summary)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {Colors.BG};")
        
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(16)
        
        if self.order:
            # Siparis bilgileri
            info_section = self._create_info_section()
            content_layout.addWidget(info_section)
            
            # Uretim rotasi
            route_section = self._create_route_section()
            content_layout.addWidget(route_section)
            
            # Tahmini tamamlanma
            estimate_section = self._create_estimate_section()
            content_layout.addWidget(estimate_section)
        else:
            # Siparis bulunamadi
            error_label = QLabel("Siparis bulunamadi.")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px; padding: 40px;")
            content_layout.addWidget(error_label)
        
        content_layout.addStretch()
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll, 1)
        
        # Footer
        footer = self._create_footer()
        layout.addWidget(footer)
    
    def _create_header(self):
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Siparis kodu
        title = QLabel(f"Siparis: {self.order_code}")
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(title)
        
        # Musteri
        if self.order:
            customer = self.order.get('customer', self.order.get('customer_name', '-'))
            lbl_customer = QLabel(f"| {customer}")
            lbl_customer.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
            layout.addWidget(lbl_customer)
        
        layout.addStretch()
        
        # Oncelik badge
        if self.order:
            priority = self.order.get('priority', 'Normal')
            if priority in ['Kritik', 'Acil']:
                badge_color = Colors.CRITICAL if priority == 'Kritik' else Colors.WARNING
                lbl_priority = QLabel(f"⚠ {priority}")
                lbl_priority.setStyleSheet(f"""
                    font-size: 11px; 
                    font-weight: bold; 
                    color: white;
                    background-color: {badge_color};
                    padding: 4px 10px;
                    border-radius: 3px;
                """)
                layout.addWidget(lbl_priority)
        
        return header
    
    def _create_summary_bar(self):
        """Ozet cubugu - toplam ilerleme"""
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(20)
        
        # Hesaplamalar
        route = self.order.get('route', '')
        stations = [s.strip() for s in route.split(',') if s.strip() and s.strip() not in ['SEVKIYAT', 'SEVKİYAT']]
        total_qty = self.order.get('quantity', 1)
        
        completed_stations = 0
        partial_stations = 0
        total_progress = 0
        
        for station in stations:
            done = self.station_progress.get(station, 0)
            if done >= total_qty:
                completed_stations += 1
                total_progress += 100
            elif done > 0:
                partial_stations += 1
                total_progress += int((done / total_qty) * 100)
        
        avg_progress = int(total_progress / len(stations)) if stations else 0
        
        # Genel ilerleme
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(4)
        
        lbl_progress_title = QLabel("Genel Ilerleme")
        lbl_progress_title.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_MUTED};")
        progress_layout.addWidget(lbl_progress_title)
        
        progress_bar_layout = QHBoxLayout()
        progress_bar_layout.setSpacing(8)
        
        progress_bar = QProgressBar()
        progress_bar.setFixedSize(150, 8)
        progress_bar.setValue(avg_progress)
        progress_bar.setTextVisible(False)
        
        bar_color = Colors.SUCCESS if avg_progress == 100 else Colors.INFO
        progress_bar.setStyleSheet(f"""
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
        progress_bar_layout.addWidget(progress_bar)
        
        lbl_pct = QLabel(f"%{avg_progress}")
        lbl_pct.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {bar_color};")
        progress_bar_layout.addWidget(lbl_pct)
        
        progress_layout.addLayout(progress_bar_layout)
        layout.addWidget(progress_frame)
        
        # Seperator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {Colors.BORDER};")
        layout.addWidget(sep)
        
        # Istasyon durumu
        for label, value, color in [
            ("Tamamlanan", completed_stations, Colors.SUCCESS),
            ("Devam Eden", partial_stations, Colors.WARNING),
            ("Bekleyen", len(stations) - completed_stations - partial_stations, Colors.TEXT_MUTED)
        ]:
            item = QVBoxLayout()
            item.setSpacing(2)
            
            lbl_t = QLabel(label)
            lbl_t.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_MUTED};")
            item.addWidget(lbl_t)
            
            lbl_v = QLabel(str(value))
            lbl_v.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
            item.addWidget(lbl_v)
            
            layout.addLayout(item)
        
        layout.addStretch()
        
        # Durum badge
        status = self.order.get('status', 'Beklemede')
        status_color = Colors.TEXT_MUTED
        if status == "Beklemede":
            status_color = Colors.WARNING
        elif status == "Üretimde":
            status_color = Colors.INFO
        elif status == "Tamamlandı":
            status_color = Colors.SUCCESS
        elif "Hata" in status or "Fire" in status:
            status_color = Colors.CRITICAL
        
        lbl_status = QLabel(status)
        lbl_status.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: white;
            background-color: {status_color};
            padding: 6px 12px;
            border-radius: 3px;
        """)
        layout.addWidget(lbl_status)
        
        return bar
    
    def _create_info_section(self):
        """Siparis bilgileri bolumu"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.ROW_ALT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        
        layout = QGridLayout(section)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Bilgi satirlari
        info_items = [
            ("Siparis Kodu", self.order.get('code', self.order.get('order_code', '-'))),
            ("Musteri", self.order.get('customer', self.order.get('customer_name', '-'))),
            ("Urun", f"{self.order.get('thickness', '')}mm {self.order.get('product', self.order.get('product_type', ''))}"),
            ("Adet", str(self.order.get('quantity', 0))),
            ("Toplam m²", f"{self.order.get('total_m2', self.order.get('declared_total_m2', 0)):.1f}"),
            ("Teslim Tarihi", self.order.get('date', self.order.get('delivery_date', '-'))),
        ]

        for i, (label, value) in enumerate(info_items):
            row = i // 3
            col = i % 3

            item_layout = QVBoxLayout()
            item_layout.setSpacing(2)

            lbl_title = QLabel(label)
            lbl_title.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_MUTED};")
            item_layout.addWidget(lbl_title)

            lbl_value = QLabel(str(value))
            lbl_value.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.TEXT};")
            item_layout.addWidget(lbl_value)

            layout.addLayout(item_layout, row, col)

        # Not alani (varsa)
        notes = self.order.get('notes', '').strip()
        if notes:
            row = len(info_items) // 3
            item_layout = QVBoxLayout()
            item_layout.setSpacing(2)

            lbl_title = QLabel("📝 Siparis Notu")
            lbl_title.setStyleSheet(f"font-size: 10px; color: {Colors.ACCENT}; font-weight: bold;")
            item_layout.addWidget(lbl_title)

            lbl_value = QLabel(notes)
            lbl_value.setWordWrap(True)
            lbl_value.setStyleSheet(f"""
                font-size: 11px;
                color: {Colors.TEXT};
                background-color: {Colors.INFO_BG};
                padding: 8px;
                border-radius: 4px;
                border-left: 3px solid {Colors.ACCENT};
            """)
            item_layout.addWidget(lbl_value)

            layout.addLayout(item_layout, row, 0, 1, 3)  # 3 sutun genisliginde

        return section
    
    def _create_route_section(self):
        """Uretim rotasi bolumu"""
        section = QFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Baslik
        header = QHBoxLayout()
        
        lbl_title = QLabel("Uretim Rotasi")
        lbl_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT};")
        header.addWidget(lbl_title)
        
        header.addStretch()
        
        # Anlik konum
        current = self._get_current_station()
        if current:
            lbl_current = QLabel(f"Simdi: {current}")
            lbl_current.setStyleSheet(f"""
                font-size: 10px;
                color: white;
                background-color: {Colors.INFO};
                padding: 3px 8px;
                border-radius: 3px;
            """)
            header.addWidget(lbl_current)
        
        layout.addLayout(header)
        
        # Istasyon listesi
        content = QFrame()
        content.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(4)
        
        route = self.order.get('route', '')
        stations = [s.strip() for s in route.split(',') if s.strip()]
        total_qty = self.order.get('quantity', 1)
        
        # Hangi istasyonda oldugunu bul
        current_station = None
        for station in stations:
            if station in ['SEVKIYAT', 'SEVKİYAT']:
                continue
            done = self.station_progress.get(station, 0)
            if done < total_qty:
                current_station = station
                break
        
        for station in stations:
            if station in ['SEVKIYAT', 'SEVKİYAT']:
                continue  # Sevkiyati gosterme
            
            done = self.station_progress.get(station, 0)
            
            if done >= total_qty:
                status = 'completed'
            elif done > 0:
                status = 'partial'
            elif station == current_station:
                status = 'current'
            else:
                status = 'pending'
            
            station_row = self._create_station_row(station, done, total_qty, status)
            content_layout.addWidget(station_row)
        
        layout.addWidget(content)
        
        return section
    
    def _get_current_station(self):
        """Siparişin şu an bulunduğu istasyonu bul"""
        route = self.order.get('route', '')
        stations = [s.strip() for s in route.split(',') if s.strip()]
        total_qty = self.order.get('quantity', 1)
        
        for station in stations:
            if station in ['SEVKIYAT', 'SEVKİYAT']:
                continue
            done = self.station_progress.get(station, 0)
            if done < total_qty:
                if done > 0:
                    return f"{station} ({done}/{total_qty})"
                return station
        
        return None
    
    def _create_station_row(self, station, done, total, status):
        """Tek istasyon satiri"""
        row = QFrame()
        row.setFixedHeight(36)
        
        if status == 'completed':
            bg_color = Colors.SUCCESS_BG
            border_color = Colors.SUCCESS
            icon = "●"
            icon_color = Colors.SUCCESS
        elif status == 'partial':
            bg_color = Colors.WARNING_BG
            border_color = Colors.WARNING
            icon = "◐"
            icon_color = Colors.WARNING
        elif status == 'current':
            bg_color = Colors.INFO_BG
            border_color = Colors.INFO
            icon = "▶"
            icon_color = Colors.INFO
        else:
            bg_color = Colors.BG
            border_color = Colors.BORDER
            icon = "○"
            icon_color = Colors.TEXT_MUTED
        
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
        """)
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)
        
        # Ikon
        lbl_icon = QLabel(icon)
        lbl_icon.setFixedWidth(16)
        lbl_icon.setStyleSheet(f"color: {icon_color}; font-size: 12px;")
        layout.addWidget(lbl_icon)
        
        # Istasyon adi
        lbl_name = QLabel(station)
        lbl_name.setFixedWidth(120)
        lbl_name.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(lbl_name)
        
        # Ilerleme
        pct = int((done / total * 100)) if total > 0 else 0
        
        progress = QProgressBar()
        progress.setFixedSize(80, 6)
        progress.setValue(pct)
        progress.setTextVisible(False)
        
        chunk_color = icon_color if status != 'pending' else Colors.GRID
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.GRID};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(progress)
        
        # Adet bilgisi
        lbl_qty = QLabel(f"{done}/{total}")
        lbl_qty.setFixedWidth(60)
        lbl_qty.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(lbl_qty)
        
        layout.addStretch()
        
        # Durum metni
        if status == 'completed':
            status_text = "Tamamlandı"
        elif status == 'partial':
            status_text = "Devam ediyor"
        elif status == 'current':
            status_text = "Sırada"
        else:
            status_text = "Bekliyor"
        
        lbl_status = QLabel(status_text)
        lbl_status.setStyleSheet(f"font-size: 10px; color: {icon_color};")
        layout.addWidget(lbl_status)
        
        return row
    
    def _create_estimate_section(self):
        """Tahmini tamamlanma bolumu"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.INFO_BG};
                border: 1px solid {Colors.INFO};
                border-radius: 4px;
                padding: 12px;
            }}
        """)
        
        layout = QHBoxLayout(section)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)
        
        # Hesaplama
        route = self.order.get('route', '')
        stations = [s.strip() for s in route.split(',') if s.strip() and s.strip() not in ['SEVKIYAT', 'SEVKİYAT']]
        total_qty = self.order.get('quantity', 1)
        total_m2 = self.order.get('total_m2', self.order.get('declared_total_m2', 0)) or 0
        
        remaining_days = 0
        remaining_stations = []
        
        for station in stations:
            done = self.station_progress.get(station, 0)
            if done < total_qty:
                remaining_stations.append(station)
                cap = FactoryConfig.get_capacity(station)
                remaining_m2 = total_m2 * (1 - done / total_qty) if total_qty > 0 else total_m2
                if cap > 0:
                    remaining_days += remaining_m2 / cap + 0.5  # +0.5 kuyruk
        
        remaining_days = max(1, int(remaining_days)) if remaining_stations else 0
        estimated_completion = datetime.now().date() + timedelta(days=remaining_days)
        
        # Ikon
        lbl_icon = QLabel("⏱")
        lbl_icon.setStyleSheet(f"font-size: 20px;")
        layout.addWidget(lbl_icon)
        
        # Bilgi
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        lbl_title = QLabel("Tahmini Tamamlanma")
        lbl_title.setStyleSheet(f"font-size: 10px; color: {Colors.INFO};")
        info_layout.addWidget(lbl_title)
        
        if remaining_stations:
            lbl_date = QLabel(f"{estimated_completion.strftime('%d.%m.%Y')} ({remaining_days} gün)")
        else:
            lbl_date = QLabel("Tamamlandı ✓")
        lbl_date.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {Colors.TEXT};")
        info_layout.addWidget(lbl_date)
        
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Kalan istasyon
        if remaining_stations:
            lbl_remaining = QLabel(f"{len(remaining_stations)} istasyon kaldı")
        else:
            lbl_remaining = QLabel("Tüm istasyonlar tamamlandı")
        lbl_remaining.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(lbl_remaining)
        
        return section
    
    def _create_footer(self):
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-top: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 8, 20, 8)
        
        # Yenileme gostergesi
        self.lbl_refresh = QLabel("Her 3 saniyede yenileniyor")
        self.lbl_refresh.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_MUTED};")
        layout.addWidget(self.lbl_refresh)
        
        layout.addStretch()
        
        btn_close = QPushButton("Kapat")
        btn_close.setFixedSize(100, 34)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        return footer
    
    def closeEvent(self, event):
        """Dialog kapanirken timer'i durdur"""
        self.timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    
    # Test icin ornek siparis kodu
    dialog = OrderDetailDialog("I2025-001")
    dialog.show()
    
    sys.exit(app.exec())