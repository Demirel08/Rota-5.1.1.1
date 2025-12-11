"""
UI Cards - Yeni Minimal Tema İçin Uyumluluk Katmanı
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

try:
    from ui.theme import Theme
except ImportError:
    # Tema yüklenemezse varsayılan değerler
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
        RADIUS_MD = "8px"


class StatCard(QFrame):
    """
    ESKİ StatCard - GERİYE UYUMLULUK İÇİN
    Artık MetricWidget kullanılıyor, ama eski importlar çalışsın diye burada
    """
    
    def __init__(self, title="", value="0", color=None):
        super().__init__()
        
        if color is None:
            color = Theme.PRIMARY
        
        self.setObjectName("StatCard")
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_MD};
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Başlık
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: {Theme.TEXT_SECONDARY};
            text-transform: uppercase;
        """)
        layout.addWidget(lbl_title)
        
        # Değer
        self.lbl_value = QLabel(str(value))
        self.lbl_value.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {color};
        """)
        layout.addWidget(self.lbl_value)
    
    def set_value(self, value):
        """Değeri güncelle"""
        self.lbl_value.setText(str(value))