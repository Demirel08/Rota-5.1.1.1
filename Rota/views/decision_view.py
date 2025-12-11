"""
EFES ROTA X - Akilli Uretim Planlama ve Karar Destek Sistemi

Ozellikler:
- Critical Ratio (CR) hesaplama
- Darbogaz analizi
- Alternatif rota onerileri
- Batch optimizasyonu (kalinlik bazli gruplama)
- Istasyon bazli kuyruk simulasyonu
- Gercek zamanli oneri motoru
"""

import sys
from datetime import datetime, timedelta
from collections import defaultdict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView,
    QFileDialog, QFrame, QApplication, QScrollArea,
    QProgressBar, QToolTip
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QCursor

try:
    from core.db_manager import db
    # --- DEĞİŞİKLİK 1: Akıllı Planlayıcıyı Dahil Ettik ---
    from core.smart_planner import planner
except ImportError:
    db = None
    planner = None


# =============================================================================
# TEMA RENKLERI (Excel Tarzi)
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
    
    # Istasyon durumlari
    IDLE = "#4CAF50"       # Bos
    NORMAL = "#2196F3"     # Normal
    BUSY = "#FF9800"       # Yogun
    OVERLOAD = "#F44336"   # Asiri yuk


# =============================================================================
# FABRIKA YAPISI VE KURALLARI
# =============================================================================
class FactoryConfig:
    """Cam fabrikasi yapilandirmasi"""
    
    # Istasyon gruplari
    STATION_GROUPS = {
        "KESIM": ["INTERMAC", "LIVA KESIM", "LAMINE KESIM"],
        "ISLEME": ["CNC RODAJ", "DOUBLEDGER", "ZIMPARA"],
        "YUZEY": ["TESIR A1", "TESIR B1", "TESIR B1-1", "TESIR B1-2", "DELIK", "OYGU"],
        "TEMPER": ["TEMPER A1", "TEMPER B1", "TEMPER BOMBE"],
        "BIRLESTIRME": ["LAMINE A1", "ISICAM B1"],
        "SEVKIYAT": ["SEVKIYAT"]
    }
    
    # Alternatif istasyonlar (ayni isi yapabilenler)
    ALTERNATIVE_STATIONS = {
        "INTERMAC": ["LIVA KESIM"],
        "LIVA KESIM": ["INTERMAC"],
        "TEMPER A1": ["TEMPER B1"],
        "TEMPER B1": ["TEMPER A1"],
        "TESIR A1": ["TESIR B1", "TESIR B1-1", "TESIR B1-2"],
        "TESIR B1": ["TESIR A1", "TESIR B1-1", "TESIR B1-2"],
        "TESIR B1-1": ["TESIR A1", "TESIR B1", "TESIR B1-2"],
        "TESIR B1-2": ["TESIR A1", "TESIR B1", "TESIR B1-1"],
    }
    
    # Gunluk kapasiteler (m2/gun)
    DEFAULT_CAPACITIES = {
        "INTERMAC": 800, "LIVA KESIM": 800, "LAMINE KESIM": 600,
        "CNC RODAJ": 100, "DOUBLEDGER": 400, "ZIMPARA": 300,
        "TESIR A1": 400, "TESIR B1": 400, "TESIR B1-1": 400, "TESIR B1-2": 400,
        "DELIK": 200, "OYGU": 200,
        "TEMPER A1": 550, "TEMPER B1": 750, "TEMPER BOMBE": 300,
        "LAMINE A1": 250, "ISICAM B1": 500, "SEVKIYAT": 5000
    }
    
    # Istasyon sirasi (uretim akisi)
    STATION_ORDER = [
        "INTERMAC", "LIVA KESIM", "LAMINE KESIM",
        "CNC RODAJ", "DOUBLEDGER", "ZIMPARA",
        "TESIR A1", "TESIR B1", "TESIR B1-1", "TESIR B1-2", "DELIK", "OYGU",
        "TEMPER A1", "TEMPER B1", "TEMPER BOMBE",
        "LAMINE A1", "ISICAM B1",
        "SEVKIYAT"
    ]
    
    # Batch islemleri icin istasyonlar (kalinlik bazli gruplama)
    BATCH_STATIONS = ["TEMPER A1", "TEMPER B1", "TEMPER BOMBE"]
    
    @classmethod
    def get_station_group(cls, station_name):
        for group, stations in cls.STATION_GROUPS.items():
            if station_name in stations:
                return group
        return None
    
    @classmethod
    def get_alternatives(cls, station_name):
        return cls.ALTERNATIVE_STATIONS.get(station_name, [])
    
    @classmethod
    def is_cutting_station(cls, station_name):
        return station_name in cls.STATION_GROUPS.get("KESIM", [])


# =============================================================================
# ISTASYON KUYRUK YONETICISI
# =============================================================================
class StationQueueManager:
    """Her istasyon icin kuyruk yonetimi"""
    
    def __init__(self):
        self.capacities = FactoryConfig.DEFAULT_CAPACITIES.copy()
        self.queues = defaultdict(list)  # station -> [orders]
        self.loads = defaultdict(float)   # station -> total m2
        
        if db:
            try:
                self.capacities = db.get_all_capacities()
            except:
                pass
    
    def build_queues(self, orders):
        """Siparislerden istasyon kuyruklarini olustur"""
        self.queues = defaultdict(list)
        self.loads = defaultdict(float)
        
        for order in orders:
            route = order.get('route', '')
            m2 = order.get('declared_total_m2', 0)
            
            if not route:
                continue
            
            # Tamamlanmis istasyonlari al
            completed = []
            if db:
                try:
                    completed = db.get_completed_stations_list(order['id'])
                except:
                    pass
            
            # Rotadaki her istasyon icin
            for station in route.split(','):
                station = station.strip()
                if station and station not in completed:
                    self.queues[station].append(order)
                    self.loads[station] += m2
    
    def get_station_status(self, station_name):
        """Istasyon durumunu dondur"""
        cap = self.capacities.get(station_name, 500)
        load = self.loads.get(station_name, 0)
        queue_count = len(self.queues.get(station_name, []))
        
        if cap <= 0:
            cap = 500
        
        ratio = load / cap
        queue_days = ratio
        
        if load == 0:
            status = "idle"
            color = Colors.IDLE
        elif ratio <= 1:
            status = "normal"
            color = Colors.NORMAL
        elif ratio <= 2:
            status = "busy"
            color = Colors.BUSY
        else:
            status = "overload"
            color = Colors.OVERLOAD
        
        return {
            "station": station_name,
            "load_m2": load,
            "capacity": cap,
            "ratio": ratio,
            "queue_days": queue_days,
            "queue_count": queue_count,
            "status": status,
            "color": color
        }
    
    def get_all_station_statuses(self):
        """Tum istasyonlarin durumunu dondur"""
        statuses = []
        for station in FactoryConfig.STATION_ORDER:
            statuses.append(self.get_station_status(station))
        return statuses
    
    def get_idle_stations(self):
        """Bos istasyonlari dondur"""
        idle = []
        for station in FactoryConfig.STATION_ORDER:
            if station == "SEVKIYAT":
                continue
            status = self.get_station_status(station)
            if status['status'] == 'idle':
                idle.append(station)
        return idle
    
    def get_bottlenecks(self):
        """Darbogaz istasyonlari dondur"""
        bottlenecks = []
        for station in FactoryConfig.STATION_ORDER:
            status = self.get_station_status(station)
            if status['ratio'] > 2:  # 2 gunluk kuyruktan fazla
                bottlenecks.append(status)
        return sorted(bottlenecks, key=lambda x: x['ratio'], reverse=True)


# =============================================================================
# CRITICAL RATIO HESAPLAYICI
# =============================================================================
class CriticalRatioCalculator:
    """
    Critical Ratio (CR) = (Teslim Tarihi - Bugun) / Kalan Islem Suresi
    
    CR < 1.0: Gecikme riski (oncelikli)
    CR = 1.0: Tam zamaninda
    CR > 1.0: Guvenli
    """
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
    
    def calculate_remaining_time(self, order):
        """Kalan islem suresini gun olarak hesapla"""
        route = order.get('route', '')
        m2 = order.get('declared_total_m2', 0)
        
        if not route or m2 <= 0:
            return 0
        
        # Tamamlanmis istasyonlar
        completed = []
        if db:
            try:
                completed = db.get_completed_stations_list(order['id'])
            except:
                pass
        
        total_days = 0
        capacities = self.queue_manager.capacities
        
        for station in route.split(','):
            station = station.strip()
            if station and station not in completed:
                cap = capacities.get(station, 500)
                if cap > 0:
                    # Kuyruk bekleme suresi + islem suresi
                    queue_load = self.queue_manager.loads.get(station, 0)
                    queue_wait = queue_load / cap
                    process_time = m2 / cap
                    total_days += queue_wait + process_time
        
        return max(total_days, 0.1)  # Minimum 0.1 gun
    
    def calculate_cr(self, order):
        """Critical Ratio hesapla"""
        delivery_str = order.get('delivery_date', '')
        
        if not delivery_str:
            return None, "unknown"
        
        try:
            delivery_date = datetime.strptime(delivery_str, '%Y-%m-%d')
            today = datetime.now()
            
            # Kalan gun
            days_until_due = (delivery_date - today).days
            
            # Kalan islem suresi
            remaining_time = self.calculate_remaining_time(order)
            
            if remaining_time <= 0:
                remaining_time = 0.1
            
            cr = days_until_due / remaining_time
            
            # Durum belirleme
            if cr < 0:
                status = "late"  # Zaten gecmis
            elif cr < 0.8:
                status = "critical"  # Kritik gecikme riski
            elif cr < 1.0:
                status = "risk"  # Risk altinda
            elif cr < 1.5:
                status = "tight"  # Sikisik ama yapilabilir
            else:
                status = "safe"  # Guvenli
            
            return round(cr, 2), status
            
        except:
            return None, "unknown"
    
    def estimate_completion_date(self, order, queue_position, all_orders):
        """Tahmini tamamlanma tarihi"""
        remaining_days = self.calculate_remaining_time(order)
        completion_date = datetime.now() + timedelta(days=remaining_days)
        return completion_date, remaining_days


# =============================================================================
# ALTERNATIF ROTA OPTIMIZER
# =============================================================================
class AlternativeRouteOptimizer:
    """Alternatif rota ve istasyon onerileri"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
    
    def find_alternative_routes(self, order):
        """Siparis icin alternatif rota onerileri"""
        suggestions = []
        route = order.get('route', '')
        
        if not route:
            return suggestions
        
        # Tamamlanmis istasyonlar
        completed = []
        if db:
            try:
                completed = db.get_completed_stations_list(order['id'])
            except:
                pass
        
        for station in route.split(','):
            station = station.strip()
            if not station or station in completed:
                continue
            
            # Mevcut istasyon durumu
            current_status = self.queue_manager.get_station_status(station)
            
            # Alternatif istasyonlar
            alternatives = FactoryConfig.get_alternatives(station)
            
            for alt in alternatives:
                alt_status = self.queue_manager.get_station_status(alt)
                
                # Alternatif daha bossa oner
                if alt_status['ratio'] < current_status['ratio'] - 0.5:
                    time_saved = current_status['queue_days'] - alt_status['queue_days']
                    suggestions.append({
                        "order_code": order['order_code'],
                        "current_station": station,
                        "alternative_station": alt,
                        "current_queue_days": round(current_status['queue_days'], 1),
                        "alt_queue_days": round(alt_status['queue_days'], 1),
                        "time_saved_days": round(time_saved, 1),
                        "message": f"{order['order_code']}: {station} yerine {alt} kullanilabilir ({time_saved:.1f} gun kazanc)"
                    })
        
        return suggestions


# =============================================================================
# BATCH OPTIMIZER (Kalinlik Bazli Gruplama)
# =============================================================================
class BatchOptimizer:
    """Temper icin kalinlik bazli gruplama onerileri"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
    
    def find_batch_opportunities(self, orders):
        """Batch firsatlarini bul"""
        suggestions = []
        
        # Temper bekleyen siparisleri kalinliga gore grupla
        thickness_groups = defaultdict(list)
        
        for order in orders:
            route = order.get('route', '')
            thickness = order.get('thickness', 0)
            
            # Temper istasyonu rotada var mi?
            has_temper = any(st in route for st in FactoryConfig.BATCH_STATIONS)
            
            if has_temper and thickness:
                # Tamamlanmis istasyonlar
                completed = []
                if db:
                    try:
                        completed = db.get_completed_stations_list(order['id'])
                    except:
                        pass
                
                # Temper henuz yapilmamissa
                temper_pending = any(
                    st in route and st not in completed 
                    for st in FactoryConfig.BATCH_STATIONS
                )
                
                if temper_pending:
                    thickness_groups[thickness].append(order)
        
        # 2'den fazla siparis olan gruplari oner
        for thickness, group_orders in thickness_groups.items():
            if len(group_orders) >= 2:
                total_m2 = sum(o.get('declared_total_m2', 0) for o in group_orders)
                order_codes = [o['order_code'] for o in group_orders[:5]]
                
                suggestions.append({
                    "type": "batch",
                    "thickness": thickness,
                    "count": len(group_orders),
                    "total_m2": round(total_m2, 1),
                    "orders": order_codes,
                    "message": f"Temper Batch: {len(group_orders)} siparis {thickness}mm kalinlikta ({total_m2:.0f} m2). Birlikte islenmeli."
                })
        
        return suggestions


# =============================================================================
# AKILLI ONERI MOTORU
# =============================================================================
class SmartRecommendationEngine:
    """Tum analizleri birlestiren oneri motoru"""
    
    def __init__(self):
        self.queue_manager = StationQueueManager()
        self.cr_calculator = CriticalRatioCalculator(self.queue_manager)
        self.route_optimizer = AlternativeRouteOptimizer(self.queue_manager)
        self.batch_optimizer = BatchOptimizer(self.queue_manager)
    
    def analyze(self, orders):
        """Kapsamli analiz yap"""
        # Kuyruklari olustur
        self.queue_manager.build_queues(orders)
        
        recommendations = []
        
        # 1. Critical Ratio analizi
        for order in orders:
            cr, status = self.cr_calculator.calculate_cr(order)
            if status in ["late", "critical"]:
                recommendations.append({
                    "type": "critical",
                    "priority": 1,
                    "message": f"{order['order_code']}: CR={cr:.2f} - Gecikme riski yuksek! Hemen one alinmali."
                })
            elif status == "risk":
                recommendations.append({
                    "type": "warning",
                    "priority": 2,
                    "message": f"{order['order_code']}: CR={cr:.2f} - Teslim tarihine yakin, dikkat."
                })
        
        # 2. Darbogaz analizi
        bottlenecks = self.queue_manager.get_bottlenecks()
        for bn in bottlenecks[:3]:  # En kritik 3 darbogaz
            recommendations.append({
                "type": "warning",
                "priority": 3,
                "message": f"Darbogaz: {bn['station']} - {bn['load_m2']:.0f} m2 yuk, {bn['queue_days']:.1f} gunluk kuyruk"
            })
        
        # 3. Alternatif rota onerileri
        for order in orders[:10]:  # Ilk 10 siparis icin
            alt_routes = self.route_optimizer.find_alternative_routes(order)
            for alt in alt_routes:
                if alt['time_saved_days'] >= 0.5:  # Yarim gun veya daha fazla kazanc
                    recommendations.append({
                        "type": "info",
                        "priority": 4,
                        "message": alt['message']
                    })
        
        # 4. Batch onerileri
        batch_suggestions = self.batch_optimizer.find_batch_opportunities(orders)
        for batch in batch_suggestions:
            recommendations.append({
                "type": "info",
                "priority": 5,
                "message": batch['message']
            })
        
        # 5. Bos istasyonlar
        idle = self.queue_manager.get_idle_stations()
        if idle:
            recommendations.append({
                "type": "info",
                "priority": 6,
                "message": f"Bos istasyonlar: {', '.join(idle)}"
            })
        
        # Oncelik sirasina gore sirala
        recommendations.sort(key=lambda x: x['priority'])
        
        return recommendations
    
    def get_order_current_station(self, order):
        """Siparisin mevcut istasyonunu bul"""
        if not db:
            return None
        
        try:
            route = order.get('route', '')
            if not route:
                return None
            
            completed = db.get_completed_stations_list(order['id'])
            
            for station in route.split(','):
                station = station.strip()
                if station and station not in completed:
                    return station
            
            return None
        except:
            return None
    
    def can_reorder(self, order_to_move, target_order):
        """Siparis yer degistirebilir mi?"""
        if order_to_move.get('status') == 'Beklemede':
            return True, ""
        
        current_station = self.get_order_current_station(order_to_move)
        if current_station and FactoryConfig.is_cutting_station(current_station):
            return False, f"Siparis {current_station} istasyonunda, one alinamaz"
        
        return True, ""


# =============================================================================
# ANA WIDGET
# =============================================================================
class DecisionView(QWidget):
    """Karar Destek Sistemi Ana Ekrani"""
    
    def __init__(self):
        super().__init__()
        self.all_orders = []
        self.original_orders = []
        self.engine = SmartRecommendationEngine()
        self.panel_visible = False
        self.setup_ui()
        self.load_orders()
    
    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Ana icerik
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Tablo
        self.table = self._create_table()
        content_layout.addWidget(self.table, 1)
        
        # Sag panel (acilir-kapanir)
        self.side_panel = self._create_side_panel()
        self.side_panel.setFixedWidth(300)
        self.side_panel.setVisible(False)
        content_layout.addWidget(self.side_panel)
        
        layout.addWidget(content, 1)
        
        # Status bar
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
        layout.setSpacing(2)
        
        btn_style = f"""
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
        """
        
        btn_toggle_style = f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 2px;
                padding: 4px 10px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #E5E5E5;
            }}
            QPushButton:checked {{
                background-color: {Colors.INFO_BG};
                border: 1px solid {Colors.INFO};
                color: {Colors.INFO};
            }}
        """
        
        # Yenile
        btn_refresh = QPushButton("Yenile")
        btn_refresh.setStyleSheet(btn_style)
        btn_refresh.clicked.connect(self.load_orders)
        layout.addWidget(btn_refresh)
        
        self._add_separator(layout)
        
        # Siralama
        for text, func in [
            ("CR Sirala", self.sort_by_cr),
            ("Termin", self.sort_by_deadline),
            ("Oncelik", self.sort_by_priority),
            ("Kisa Is", self.sort_by_duration),
            ("Sifirla", self.reset_order)
        ]:
            btn = QPushButton(text)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(func)
            layout.addWidget(btn)
        
        self._add_separator(layout)
        
        # Hareket
        for text, func in [
            ("Yukari", self.move_up),
            ("Asagi", self.move_down),
            ("En Ust", self.move_to_top),
            ("En Alt", self.move_to_bottom)
        ]:
            btn = QPushButton(text)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(func)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Istatistikler
        stat_style = f"color: {Colors.TEXT}; font-size: 11px; font-weight: bold;"
        
        self.lbl_total = QLabel("Siparis: 0")
        self.lbl_total.setStyleSheet(stat_style)
        layout.addWidget(self.lbl_total)
        
        layout.addSpacing(12)
        
        self.lbl_critical = QLabel("Kritik: 0")
        self.lbl_critical.setStyleSheet(f"color: {Colors.CRITICAL}; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.lbl_critical)
        
        layout.addSpacing(12)
        
        self.lbl_bottleneck = QLabel("Darbogaz: 0")
        self.lbl_bottleneck.setStyleSheet(f"color: {Colors.WARNING}; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.lbl_bottleneck)
        
        self._add_separator(layout)
        
        # Panel toggle
        self.btn_panel = QPushButton("Analiz Paneli")
        self.btn_panel.setCheckable(True)
        self.btn_panel.setStyleSheet(btn_toggle_style)
        self.btn_panel.clicked.connect(self.toggle_panel)
        layout.addWidget(self.btn_panel)
        
        self._add_separator(layout)
        
        # Aksiyon
        btn_export = QPushButton("Excel")
        btn_export.setStyleSheet(btn_style)
        btn_export.clicked.connect(self.export_to_excel)
        layout.addWidget(btn_export)
        
        btn_apply = QPushButton("Uygula")
        btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 2px;
                padding: 4px 14px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_apply.clicked.connect(self.apply_order)
        layout.addWidget(btn_apply)
        
        return toolbar
    
    def _create_table(self):
        table = QTableWidget()
        table.setColumnCount(13)
        table.setHorizontalHeaderLabels([
            "#", "Kod", "Musteri", "Urun", "m2",
            "CR", "Termin", "Tahmini", "Fark",
            "Durum", "Istasyon", "Uyari", "📝"
        ])
        table.cellClicked.connect(self.on_cell_clicked)
        
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG};
                alternate-background-color: {Colors.ROW_ALT};
                gridline-color: {Colors.GRID};
                border: none;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 2px 6px;
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.SELECTION};
                color: {Colors.TEXT};
            }}
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT};
                padding: 4px 6px;
                border: none;
                border-right: 1px solid {Colors.GRID};
                border-bottom: 1px solid {Colors.BORDER};
                font-size: 11px;
                font-weight: 600;
            }}
            QScrollBar:vertical {{
                background: {Colors.HEADER_BG};
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background: #C1C1C1;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        table.setColumnWidth(0, 35)
        table.setColumnWidth(1, 90)
        table.setColumnWidth(2, 140)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 50)
        table.setColumnWidth(5, 50)
        table.setColumnWidth(6, 80)
        table.setColumnWidth(7, 80)
        table.setColumnWidth(8, 50)
        table.setColumnWidth(9, 70)
        table.setColumnWidth(10, 85)
        table.setColumnWidth(11, 45)
        table.setColumnWidth(12, 40)
        
        header.setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(22)
        
        return table
    
    def _create_side_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG};
                border-left: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Baslik
        header = QFrame()
        header.setFixedHeight(28)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        
        lbl = QLabel("Analiz ve Oneriler")
        lbl.setStyleSheet(f"color: {Colors.TEXT}; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()
        
        btn_close = QPushButton("X")
        btn_close.setFixedSize(20, 20)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_MUTED};
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {Colors.TEXT};
                background-color: {Colors.BORDER};
            }}
        """)
        btn_close.clicked.connect(self.toggle_panel)
        header_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {Colors.BG};
            }}
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        scroll_layout.setSpacing(12)
        
        # Istasyon Durumlari
        station_header = QLabel("Istasyon Durumlari")
        station_header.setStyleSheet(f"color: {Colors.TEXT}; font-size: 11px; font-weight: bold;")
        scroll_layout.addWidget(station_header)
        
        self.station_container = QWidget()
        self.station_layout = QVBoxLayout(self.station_container)
        self.station_layout.setContentsMargins(0, 0, 0, 0)
        self.station_layout.setSpacing(4)
        scroll_layout.addWidget(self.station_container)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.BORDER};")
        scroll_layout.addWidget(sep)
        
        # Oneriler
        rec_header = QLabel("Oneriler")
        rec_header.setStyleSheet(f"color: {Colors.TEXT}; font-size: 11px; font-weight: bold;")
        scroll_layout.addWidget(rec_header)
        
        self.recommendations_container = QWidget()
        self.recommendations_layout = QVBoxLayout(self.recommendations_container)
        self.recommendations_layout.setContentsMargins(0, 0, 0, 0)
        self.recommendations_layout.setSpacing(6)
        scroll_layout.addWidget(self.recommendations_container)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
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
    
    def _create_station_bar(self, status):
        """Istasyon durum cubugu olustur"""
        widget = QWidget()
        widget.setFixedHeight(24)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Istasyon adi
        lbl_name = QLabel(status['station'][:12])
        lbl_name.setFixedWidth(80)
        lbl_name.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 10px;")
        layout.addWidget(lbl_name)
        
        # Progress bar
        progress = QProgressBar()
        progress.setFixedHeight(12)
        progress.setMaximum(100)
        progress.setValue(min(int(status['ratio'] * 50), 100))
        progress.setTextVisible(False)
        
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BORDER};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {status['color']};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(progress)
        
        # Gun
        lbl_days = QLabel(f"{status['queue_days']:.1f}g")
        lbl_days.setFixedWidth(35)
        lbl_days.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_days.setStyleSheet(f"color: {status['color']}; font-size: 10px; font-weight: bold;")
        layout.addWidget(lbl_days)
        
        return widget
    
    def toggle_panel(self):
        self.panel_visible = not self.panel_visible
        self.side_panel.setVisible(self.panel_visible)
        self.btn_panel.setChecked(self.panel_visible)
        
        if self.panel_visible:
            self.update_side_panel()
    
    def update_side_panel(self):
        """Yan paneli guncelle"""
        # Istasyon durumlarini temizle
        while self.station_layout.count():
            item = self.station_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Istasyon durumlarini ekle
        statuses = self.engine.queue_manager.get_all_station_statuses()
        for status in statuses:
            if status['station'] != "SEVKIYAT":
                bar = self._create_station_bar(status)
                self.station_layout.addWidget(bar)
        
        # Onerileri temizle
        while self.recommendations_layout.count():
            item = self.recommendations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Onerileri ekle
        recommendations = self.engine.analyze(self.all_orders)
        
        if not recommendations:
            lbl = QLabel("Sistem normal, oneri yok.")
            lbl.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 11px;")
            lbl.setWordWrap(True)
            self.recommendations_layout.addWidget(lbl)
        else:
            for rec in recommendations[:15]:  # Max 15 oneri
                color = {
                    "critical": Colors.CRITICAL,
                    "warning": Colors.WARNING,
                    "info": Colors.INFO
                }.get(rec['type'], Colors.TEXT_SECONDARY)
                
                lbl = QLabel(rec['message'])
                lbl.setStyleSheet(f"color: {color}; font-size: 10px;")
                lbl.setWordWrap(True)
                self.recommendations_layout.addWidget(lbl)
    
    # =========================================================================
    # VERI ISLEMLERI (GÜNCELLENDİ)
    # =========================================================================
    
    def load_orders(self):
        try:
            if db:
                # 1. Ham veriyi çek
                raw_orders = db.get_orders_by_status(["Beklemede", "Uretimde"])
                
                # 2. --- DEĞİŞİKLİK 2: PLANLAYICI İLE SIRALA ---
                # "3 ay sonraki işi öne çekme" hatasını düzelten yer burasıdır.
                if planner:
                    self.all_orders = planner.optimize_production_sequence(raw_orders)
                else:
                    self.all_orders = raw_orders
            else:
                self.all_orders = []
            
            self.original_orders = self.all_orders.copy()
            self.engine.queue_manager.build_queues(self.all_orders)
            self.refresh_table()
            self.update_stats()
            
            if self.panel_visible:
                self.update_side_panel()
            
            self.status_label.setText(f"{len(self.all_orders)} sipariş yüklendi ve akıllı sıralandı")
        except Exception as e:
            self.status_label.setText(f"Hata: {str(e)}")
    
    def refresh_table(self):
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.all_orders))
        
        critical_count = 0
        
        for row, order in enumerate(self.all_orders):
            # CR hesapla
            cr, cr_status = self.engine.cr_calculator.calculate_cr(order)
            
            # Tahmini tamamlanma
            est_date, remaining_days = self.engine.cr_calculator.estimate_completion_date(
                order, row, self.all_orders
            )
            
            # Mevcut istasyon
            current_station = self.engine.get_order_current_station(order)
            
            # Fark hesapla
            delivery_str = order.get('delivery_date', '')
            diff_days = None
            if delivery_str and est_date:
                try:
                    delivery_date = datetime.strptime(delivery_str, '%Y-%m-%d')
                    diff_days = (delivery_date - est_date).days
                except:
                    pass
            
            if cr_status in ["late", "critical"]:
                critical_count += 1
            
            # Sutunlar
            self._set_cell(row, 0, str(row + 1), Qt.AlignCenter, Colors.TEXT_MUTED)
            self._set_cell(row, 1, order['order_code'], Qt.AlignLeft, Colors.TEXT, bold=True)
            self._set_cell(row, 2, order['customer_name'], Qt.AlignLeft)
            self._set_cell(row, 3, order['product_type'], Qt.AlignLeft, Colors.TEXT_SECONDARY)
            
            m2 = order.get('declared_total_m2', 0)
            self._set_cell(row, 4, f"{m2:.0f}", Qt.AlignRight)
            
            # CR
            if cr is not None:
                cr_color = {
                    "late": Colors.CRITICAL,
                    "critical": Colors.CRITICAL,
                    "risk": Colors.WARNING,
                    "tight": Colors.WARNING,
                    "safe": Colors.SUCCESS
                }.get(cr_status, Colors.TEXT_SECONDARY)
                self._set_cell(row, 5, f"{cr:.2f}", Qt.AlignCenter, cr_color)
            else:
                self._set_cell(row, 5, "-", Qt.AlignCenter, Colors.TEXT_MUTED)
            
            # Termin
            self._set_cell(row, 6, delivery_str, Qt.AlignCenter)
            
            # Tahmini
            est_str = est_date.strftime('%Y-%m-%d') if est_date else "-"
            self._set_cell(row, 7, est_str, Qt.AlignCenter)
            
            # Fark
            if diff_days is not None:
                if diff_days < 0:
                    diff_color = Colors.CRITICAL
                    diff_str = str(diff_days)
                elif diff_days < 3:
                    diff_color = Colors.WARNING
                    diff_str = f"+{diff_days}"
                else:
                    diff_color = Colors.SUCCESS
                    diff_str = f"+{diff_days}"
                self._set_cell(row, 8, diff_str, Qt.AlignCenter, diff_color)
            else:
                self._set_cell(row, 8, "-", Qt.AlignCenter, Colors.TEXT_MUTED)
            
            # Durum
            status = order.get('status', 'Beklemede')
            status_colors = {
                'Uretimde': (Colors.SUCCESS, Colors.SUCCESS_BG),
                'Beklemede': (Colors.INFO, Colors.INFO_BG),
            }
            s_fg, s_bg = status_colors.get(status, (Colors.TEXT_SECONDARY, None))
            self._set_cell(row, 9, status, Qt.AlignCenter, s_fg, s_bg)
            
            # Istasyon
            self._set_cell(row, 10, current_station or "-", Qt.AlignCenter, Colors.TEXT_SECONDARY)
            
            # Uyari
            if cr_status in ["late", "critical"]:
                self._set_cell(row, 11, "!", Qt.AlignCenter, Colors.CRITICAL, Colors.CRITICAL_BG)
            elif cr_status == "risk":
                self._set_cell(row, 11, "!", Qt.AlignCenter, Colors.WARNING, Colors.WARNING_BG)
            else:
                self._set_cell(row, 11, "", Qt.AlignCenter)

            # Not ikonu
            notes = order.get('notes', '').strip()
            if notes:
                item_note = QTableWidgetItem("📝")
                item_note.setTextAlignment(Qt.AlignCenter)
                item_note.setToolTip(notes)
                item_note.setForeground(QColor(Colors.ACCENT))
                item_note.setData(Qt.UserRole, notes)
                self.table.setItem(row, 12, item_note)
            else:
                self._set_cell(row, 12, "", Qt.AlignCenter)

        self.lbl_critical.setText(f"Kritik: {critical_count}")
    
    def _set_cell(self, row, col, text, alignment=Qt.AlignLeft, 
                  fg_color=None, bg_color=None, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(alignment | Qt.AlignVCenter)
        
        if fg_color:
            item.setForeground(QColor(fg_color))
        if bg_color:
            item.setBackground(QColor(bg_color))
        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        
        self.table.setItem(row, col, item)
    
    def update_stats(self):
        if not self.all_orders:
            self.lbl_total.setText("Siparis: 0")
            self.lbl_bottleneck.setText("Darbogaz: 0")
            return
        
        total = len(self.all_orders)
        bottlenecks = len(self.engine.queue_manager.get_bottlenecks())
        
        self.lbl_total.setText(f"Siparis: {total}")
        self.lbl_bottleneck.setText(f"Darbogaz: {bottlenecks}")
    
    # =========================================================================
    # SIRALAMA
    # =========================================================================
    
    def get_selected_row(self):
        selected = self.table.selectedItems()
        if not selected:
            self.status_label.setText("Bir satir secin")
            return None
        return selected[0].row()
    
    def sort_by_cr(self):
        """Critical Ratio'ya gore sirala (dusuk CR once)"""
        def get_cr(order):
            cr, _ = self.engine.cr_calculator.calculate_cr(order)
            return cr if cr is not None else 999
        
        self.all_orders.sort(key=get_cr)
        self.refresh_table()
        if self.panel_visible:
            self.update_side_panel()
        self.status_label.setText("CR sirasina gore siralandi (kritik once)")
    
    def sort_by_priority(self):
        priority_map = {"Kritik": 1, "Cok Acil": 2, "Acil": 3, "Normal": 4}
        self.all_orders.sort(
            key=lambda x: (
                priority_map.get(x.get('priority', 'Normal'), 4),
                x.get('delivery_date', '9999-12-31')
            )
        )
        self.refresh_table()
        if self.panel_visible:
            self.update_side_panel()
        self.status_label.setText("Oncelik sirasina gore siralandi")
    
    def sort_by_deadline(self):
        self.all_orders.sort(key=lambda x: x.get('delivery_date', '9999-12-31'))
        self.refresh_table()
        if self.panel_visible:
            self.update_side_panel()
        self.status_label.setText("Termin tarihine gore siralandi")
    
    def sort_by_duration(self):
        self.all_orders.sort(key=lambda x: x.get('declared_total_m2', 999999))
        self.refresh_table()
        if self.panel_visible:
            self.update_side_panel()
        self.status_label.setText("Kisa is once siralandi")
    
    def reset_order(self):
        self.all_orders = self.original_orders.copy()
        self.refresh_table()
        if self.panel_visible:
            self.update_side_panel()
        self.status_label.setText("Sifirlandi")
    
    def move_up(self):
        row = self.get_selected_row()
        if row is None or row == 0:
            return
        
        order = self.all_orders[row]
        target = self.all_orders[row - 1]
        can_move, reason = self.engine.can_reorder(order, target)
        
        if not can_move:
            self.status_label.setText(f"Engellendi: {reason}")
            return
        
        self.all_orders[row], self.all_orders[row - 1] = \
            self.all_orders[row - 1], self.all_orders[row]
        
        self.refresh_table()
        self.table.selectRow(row - 1)
        if self.panel_visible:
            self.update_side_panel()
    
    def move_down(self):
        row = self.get_selected_row()
        if row is None or row >= len(self.all_orders) - 1:
            return
        
        self.all_orders[row], self.all_orders[row + 1] = \
            self.all_orders[row + 1], self.all_orders[row]
        
        self.refresh_table()
        self.table.selectRow(row + 1)
        if self.panel_visible:
            self.update_side_panel()
    
    def move_to_top(self):
        row = self.get_selected_row()
        if row is None or row == 0:
            return
        
        order = self.all_orders[row]
        can_move, reason = self.engine.can_reorder(order, self.all_orders[0])
        
        if not can_move:
            self.status_label.setText(f"Engellendi: {reason}")
            return
        
        order = self.all_orders.pop(row)
        self.all_orders.insert(0, order)
        
        self.refresh_table()
        self.table.selectRow(0)
        if self.panel_visible:
            self.update_side_panel()
    
    def move_to_bottom(self):
        row = self.get_selected_row()
        if row is None or row >= len(self.all_orders) - 1:
            return

        order = self.all_orders.pop(row)
        self.all_orders.append(order)

        self.refresh_table()
        self.table.selectRow(len(self.all_orders) - 1)
        if self.panel_visible:
            self.update_side_panel()

    def on_cell_clicked(self, row, column):
        """Hücreye tıklandığında - Not sütununa tıklanırsa mesaj kutusu göster"""
        if column == 12:  # Not sütunu
            item = self.table.item(row, column)
            if item:
                notes = item.data(Qt.UserRole)
                if notes:
                    QMessageBox.information(
                        self,
                        "Sipariş Notu",
                        notes,
                        QMessageBox.Ok
                    )

    # =========================================================================
    # AKSIYON
    # =========================================================================
    
    def export_to_excel(self):
        if not self.all_orders:
            self.status_label.setText("Veri yok")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Kaydet",
            f"Uretim_Plani_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8-sig') as f:
                f.write("SIRA,KOD,MUSTERI,URUN,M2,CR,TERMIN,TAHMINI,FARK,DURUM,ISTASYON\n")
                
                for idx, order in enumerate(self.all_orders):
                    cr, _ = self.engine.cr_calculator.calculate_cr(order)
                    est_date, _ = self.engine.cr_calculator.estimate_completion_date(order, idx, self.all_orders)
                    est_str = est_date.strftime('%Y-%m-%d') if est_date else ""
                    current_st = self.engine.get_order_current_station(order)
                    
                    f.write(f"{idx+1},")
                    f.write(f"{order['order_code']},")
                    f.write(f"{order['customer_name']},")
                    f.write(f"{order['product_type']},")
                    f.write(f"{order.get('declared_total_m2', 0):.1f},")
                    f.write(f"{cr if cr else ''},")
                    f.write(f"{order.get('delivery_date', '')},")
                    f.write(f"{est_str},")
                    f.write(f",")
                    f.write(f"{order.get('status', 'Beklemede')},")
                    f.write(f"{current_st or ''}\n")
            
            self.status_label.setText(f"Kaydedildi: {filename}")
            
            try:
                import os
                os.startfile(filename)
            except:
                pass
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi:\n{str(e)}")
    
    def apply_order(self):
        if not self.all_orders:
            self.status_label.setText("Veri yok")
            return
        
        total = len(self.all_orders)
        kritik_count = max(1, total // 5)
        acil_count = total // 2
        
        reply = QMessageBox.question(
            self, "Onayla",
            f"Toplam {total} siparis yeniden onceliklendirilecek:\n\n"
            f"Kritik: {kritik_count}\n"
            f"Acil: {acil_count - kritik_count}\n"
            f"Normal: {total - acil_count}\n\n"
            f"Sira numaralari ve oncelikler kaydedilecek.\n"
            f"Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            if db:
                with db.get_connection() as conn:
                    # Oncelikle queue_position kolonu var mi kontrol et, yoksa ekle
                    try:
                        conn.execute("ALTER TABLE orders ADD COLUMN queue_position INTEGER DEFAULT 9999")
                    except:
                        pass  # Kolon zaten var
                    
                    for idx, order in enumerate(self.all_orders):
                        if idx < kritik_count:
                            new_priority = "Kritik"
                        elif idx < acil_count:
                            new_priority = "Acil"
                        else:
                            new_priority = "Normal"
                        
                        # Hem priority hem de queue_position guncelle
                        conn.execute(
                            "UPDATE orders SET priority = ?, queue_position = ? WHERE id = ?",
                            (new_priority, idx + 1, order['id'])
                        )
            
            self.status_label.setText(f"Uygulandi - K:{kritik_count} A:{acil_count-kritik_count} N:{total-acil_count}")
            self.load_orders()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 9))
    
    window = DecisionView()
    window.setWindowTitle("EFES ROTA X - Akilli Uretim Planlama")
    window.resize(1400, 800)
    window.show()
    
    sys.exit(app.exec())