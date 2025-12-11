from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

try:
    from ui.theme import Theme
except ImportError:
    class Theme:
        PRIMARY = "#26A69A"
        SUCCESS = "#66BB6A"
        WARNING = "#FFA726"
        DANGER = "#EF5350"
        TEXT_PRIMARY = "#2C3E50"
        TEXT_SECONDARY = "#546E7A"
        TEXT_DARK = "#1A252F"
        SURFACE = "#FFFFFF"
        BORDER_LIGHT = "#F5F5F5"
        RADIUS_SM = "6px"


class CapacityBar(QWidget):
    """Minimal ve temiz istasyon doluluk çubuğu"""
    
    def __init__(self, station_name, percent, status="normal"):
        super().__init__()
        self.station_name = station_name
        self.percent = percent
        self.status = status
        
        self.setup_ui()
    
    def setup_ui(self):
        """Widget'ı oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Üst kısım - İstasyon adı ve yüzde
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        # İstasyon adı
        lbl_name = QLabel(self.station_name)
        lbl_name.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: {Theme.TEXT_PRIMARY};
        """)
        top_layout.addWidget(lbl_name)
        
        top_layout.addStretch()
        
        # Yüzde değeri
        lbl_percent = QLabel(f"{self.percent}%")
        lbl_percent.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {self._get_color()};
        """)
        top_layout.addWidget(lbl_percent)
        
        layout.addLayout(top_layout)
        
        # Progress bar
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setValue(self.percent)
        progress.setTextVisible(False)
        progress.setFixedHeight(8)
        
        # Minimal progress bar stili
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BORDER_LIGHT};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {self._get_color()};
                border-radius: 4px;
            }}
        """)
        
        layout.addWidget(progress)
    
    def _get_color(self):
        """Doluluk oranına göre renk belirle"""
        if self.status == "critical" or self.percent >= 90:
            return Theme.DANGER
        elif self.status == "warning" or self.percent >= 70:
            return Theme.WARNING
        elif self.status == "good" or self.percent >= 40:
            return Theme.PRIMARY
        else:
            return Theme.SUCCESS