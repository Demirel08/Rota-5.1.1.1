"""
EFES ROTA X - Merkezi Renk Tanımları
Tüm UI renkleri burada tanımlanır.
"""


class Colors:
    """Uygulama genelinde kullanılan renkler"""
    
    # === ANA RENKLER ===
    PRIMARY = "#2C3E50"          # Ana koyu renk
    SECONDARY = "#34495E"        # İkincil koyu renk
    ACCENT = "#3498DB"           # Vurgu rengi (mavi)
    
    # === ARKA PLAN RENKLERİ ===
    BACKGROUND = "#F5F6FA"       # Ana arka plan
    SURFACE = "#FFFFFF"          # Kart/panel arka planı
    HEADER = "#2C3E50"           # Header arka planı
    SIDEBAR = "#34495E"          # Sidebar arka planı
    
    # === METİN RENKLERİ ===
    TEXT_PRIMARY = "#2C3E50"     # Ana metin
    TEXT_SECONDARY = "#7F8C8D"   # İkincil metin
    TEXT_LIGHT = "#FFFFFF"       # Açık metin (koyu arka plan için)
    TEXT_MUTED = "#95A5A6"       # Soluk metin
    
    # === DURUM RENKLERİ ===
    SUCCESS = "#27AE60"          # Başarılı/Tamamlandı
    SUCCESS_LIGHT = "#E8F8F0"    # Başarılı arka plan
    WARNING = "#F39C12"          # Uyarı
    WARNING_LIGHT = "#FEF9E7"    # Uyarı arka plan
    DANGER = "#E74C3C"           # Tehlike/Hata
    DANGER_LIGHT = "#FDEDEC"     # Tehlike arka plan
    INFO = "#3498DB"             # Bilgi
    INFO_LIGHT = "#EBF5FB"       # Bilgi arka plan
    
    # === GECİKME RENKLERİ ===
    DELAY_CRITICAL = "#E74C3C"   # Kritik gecikme (>5 gün)
    DELAY_HIGH = "#E67E22"       # Yüksek gecikme (3-5 gün)
    DELAY_MEDIUM = "#F39C12"     # Orta gecikme (1-3 gün)
    DELAY_LOW = "#F1C40F"        # Düşük gecikme (<1 gün)
    ON_TIME = "#27AE60"          # Zamanında
    
    # === ÖNCELİK RENKLERİ ===
    PRIORITY_URGENT = "#E74C3C"  # Acil
    PRIORITY_HIGH = "#E67E22"    # Yüksek
    PRIORITY_NORMAL = "#3498DB"  # Normal
    PRIORITY_LOW = "#95A5A6"     # Düşük
    
    # === TABLO RENKLERİ ===
    TABLE_HEADER = "#2C3E50"     # Tablo başlık
    TABLE_ROW_ALT = "#F8F9FA"    # Alternatif satır
    TABLE_BORDER = "#E0E0E0"     # Tablo kenarlık
    TABLE_HOVER = "#EBF5FB"      # Hover durumu
    TABLE_SELECTED = "#D4E6F1"   # Seçili satır
    
    # === BUTON RENKLERİ ===
    BTN_PRIMARY = "#3498DB"      # Ana buton
    BTN_PRIMARY_HOVER = "#2980B9"
    BTN_SUCCESS = "#27AE60"      # Başarı butonu
    BTN_SUCCESS_HOVER = "#229954"
    BTN_DANGER = "#E74C3C"       # Tehlike butonu
    BTN_DANGER_HOVER = "#C0392B"
    BTN_SECONDARY = "#95A5A6"    # İkincil buton
    BTN_SECONDARY_HOVER = "#7F8C8D"
    
    # === İSTASYON GRUPLARI ===
    STATION_KESIM = "#2ECC71"
    STATION_ISLEME = "#3498DB"
    STATION_YUZEY = "#9B59B6"
    STATION_TEMPER = "#E74C3C"
    STATION_BIRLESTIRME = "#F39C12"
    STATION_SEVKIYAT = "#34495E"
    
    # === GANTT CHART ===
    GANTT_COMPLETED = "#27AE60"
    GANTT_IN_PROGRESS = "#3498DB"
    GANTT_WAITING = "#95A5A6"
    GANTT_DELAYED = "#E74C3C"
    
    # === DİĞER ===
    BORDER = "#E0E0E0"           # Genel kenarlık
    DIVIDER = "#BDC3C7"          # Ayırıcı çizgi
    DISABLED = "#BDC3C7"         # Devre dışı
    SHADOW = "rgba(0,0,0,0.1)"   # Gölge
    
    @classmethod
    def get_delay_color(cls, days_remaining: float) -> str:
        """Kalan güne göre gecikme rengi döndür"""
        if days_remaining < 0:
            return cls.DELAY_CRITICAL
        elif days_remaining < 1:
            return cls.DELAY_HIGH
        elif days_remaining < 3:
            return cls.DELAY_MEDIUM
        elif days_remaining < 5:
            return cls.DELAY_LOW
        else:
            return cls.ON_TIME
    
    @classmethod
    def get_priority_color(cls, priority: str) -> str:
        """Öncelik seviyesine göre renk döndür"""
        priority_map = {
            "acil": cls.PRIORITY_URGENT,
            "urgent": cls.PRIORITY_URGENT,
            "yüksek": cls.PRIORITY_HIGH,
            "high": cls.PRIORITY_HIGH,
            "normal": cls.PRIORITY_NORMAL,
            "düşük": cls.PRIORITY_LOW,
            "low": cls.PRIORITY_LOW,
        }
        return priority_map.get(priority.lower(), cls.PRIORITY_NORMAL)
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        """Durum metnine göre renk döndür"""
        status_lower = status.lower()
        if "tamamlan" in status_lower or "bitti" in status_lower:
            return cls.SUCCESS
        elif "devam" in status_lower or "işlem" in status_lower:
            return cls.INFO
        elif "bekl" in status_lower:
            return cls.WARNING
        elif "gecik" in status_lower or "iptal" in status_lower:
            return cls.DANGER
        return cls.TEXT_SECONDARY
    
    @classmethod
    def get_station_group_color(cls, group_name: str) -> str:
        """İstasyon grubuna göre renk döndür"""
        group_map = {
            "kesim": cls.STATION_KESIM,
            "işleme": cls.STATION_ISLEME,
            "yüzey": cls.STATION_YUZEY,
            "temper": cls.STATION_TEMPER,
            "birleştirme": cls.STATION_BIRLESTIRME,
            "sevkiyat": cls.STATION_SEVKIYAT,
        }
        for key, color in group_map.items():
            if key in group_name.lower():
                return color
        return cls.ACCENT


class Styles:
    """Hazır stil şablonları"""
    
    @staticmethod
    def card(padding: int = 20, radius: int = 8) -> str:
        """Kart stili"""
        return f"""
            background-color: {Colors.SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: {radius}px;
            padding: {padding}px;
        """
    
    @staticmethod
    def button_primary() -> str:
        """Ana buton stili"""
        return f"""
            QPushButton {{
                background-color: {Colors.BTN_PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BTN_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #1F618D;
            }}
            QPushButton:disabled {{
                background-color: {Colors.DISABLED};
            }}
        """
    
    @staticmethod
    def button_success() -> str:
        """Başarı butonu stili"""
        return f"""
            QPushButton {{
                background-color: {Colors.BTN_SUCCESS};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BTN_SUCCESS_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #1E8449;
            }}
        """
    
    @staticmethod
    def button_danger() -> str:
        """Tehlike butonu stili"""
        return f"""
            QPushButton {{
                background-color: {Colors.BTN_DANGER};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BTN_DANGER_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #A93226;
            }}
        """
    
    @staticmethod
    def input_field() -> str:
        """Input alanı stili"""
        return f"""
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {Colors.ACCENT};
            }}
        """
    
    @staticmethod
    def table() -> str:
        """Tablo stili"""
        return f"""
            QTableWidget {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                gridline-color: {Colors.TABLE_BORDER};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Colors.TABLE_BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.TABLE_SELECTED};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item:hover {{
                background-color: {Colors.TABLE_HOVER};
            }}
            QHeaderView::section {{
                background-color: {Colors.TABLE_HEADER};
                color: {Colors.TEXT_LIGHT};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """
    
    @staticmethod
    def group_box(title_color: str = None) -> str:
        """GroupBox stili"""
        title_color = title_color or Colors.TEXT_PRIMARY
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: {title_color};
            }}
        """
    
    @staticmethod
    def status_badge(color: str) -> str:
        """Durum etiketi stili"""
        return f"""
            background-color: {color};
            color: white;
            border-radius: 4px;
            padding: 4px 8px;
            font-weight: bold;
            font-size: 11px;
        """