from PySide6.QtGui import QColor, QFont, QPalette

class Theme:
    """
    EFES ROTA - MINIMAL KURUMSAL TEMA
    Temiz, profesyonel ve modern gorunum
    """
    
    # ANA RENK PALETİ - Turkuaz/Teal Tonları
    PRIMARY      = "#26A69A"  # Teal (ana renk)
    PRIMARY_DARK = "#00796B"  # Koyu teal
    PRIMARY_LIGHT= "#4DB6AC"  # Açık teal
    ACCENT       = "#26C6DA"  # Cyan aksanı
    
    # ARKA PLAN VE YÜZEYLER
    BACKGROUND   = "#F5F7FA"  # Çok açık gri arka plan
    SURFACE      = "#FFFFFF"  # Beyaz paneller
    SURFACE_DARK = "#FAFBFC"  # Hafif gri yüzey
    
    # METİN RENKLERİ
    TEXT_PRIMARY = "#2C3E50"  # Ana metin (koyu gri)
    TEXT_SECONDARY = "#546E7A"  # İkincil metin
    TEXT_DISABLED = "#90A4AE"  # Pasif metin
    TEXT_HINT = "#B0BEC5"     # İpucu metni
    TEXT_DARK = "#1A252F"     # En koyu metin
    
    # AYIRICI VE KENARLIKLAR
    DIVIDER = "#ECEFF1"       # Çok açık gri
    BORDER = "#E0E0E0"        # Hafif gri kenar
    BORDER_LIGHT = "#F5F5F5"  # Çok açık kenar
    
    # DURUM RENKLERİ - Yumuşak tonlar
    SUCCESS = "#66BB6A"       # Yumuşak yeşil
    WARNING = "#FFA726"       # Yumuşak turuncu
    DANGER = "#EF5350"        # Yumuşak kırmızı
    INFO = "#42A5F5"          # Yumuşak mavi
    
    # GÖLGE VE DERINLIK
    SHADOW_LIGHT = "0 1px 3px rgba(0,0,0,0.06)"
    SHADOW_MEDIUM = "0 2px 8px rgba(0,0,0,0.08)"
    SHADOW_STRONG = "0 4px 16px rgba(0,0,0,0.12)"
    
    # FONTLAR - Modern, temiz
    FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    FONT_SIZE_XS = "11px"
    FONT_SIZE_SM = "13px"
    FONT_SIZE_BASE = "14px"
    FONT_SIZE_LG = "16px"
    FONT_SIZE_XL = "20px"
    FONT_SIZE_2XL = "24px"
    FONT_SIZE_3XL = "32px"
    
    # BORDER RADIUS
    RADIUS_SM = "6px"
    RADIUS_MD = "8px"
    RADIUS_LG = "12px"
    RADIUS_XL = "16px"

    @staticmethod
    def apply_app_style(app):
        """Uygulamaya minimal ve kurumsal temayı uygula"""
        
        # Font ayarları
        font = QFont("Inter, Segoe UI, Roboto")
        font.setPixelSize(14)
        app.setFont(font)

        style = f"""
            /* GENEL WIDGET STİLLERİ */
            QWidget {{
                background-color: {Theme.BACKGROUND};
                color: {Theme.TEXT_PRIMARY};
                font-family: {Theme.FONT_FAMILY};
                font-size: {Theme.FONT_SIZE_BASE};
            }}
            
            /* PANELLER VE YÜZEYLER */
            QFrame, QWidget#Surface {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_LG};
            }}
            
            /* BAŞLIKLAR */
            QLabel#HeaderLabel {{
                font-size: {Theme.FONT_SIZE_2XL};
                font-weight: 600;
                color: {Theme.TEXT_PRIMARY};
                background: transparent;
                border: none;
            }}
            
            QLabel#SubHeader {{
                font-size: {Theme.FONT_SIZE_LG};
                font-weight: 500;
                color: {Theme.TEXT_SECONDARY};
                background: transparent;
            }}
            
            /* FORM ELEMANLARI - Minimal ve temiz */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SM};
                padding: 10px 14px;
                font-size: {Theme.FONT_SIZE_BASE};
                color: {Theme.TEXT_PRIMARY};
                min-height: 20px;
            }}
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
                background-color: {Theme.SURFACE};
                border: 2px solid {Theme.PRIMARY};
                padding: 9px 13px;
            }}
            
            QLineEdit:disabled, QComboBox:disabled {{
                background-color: {Theme.SURFACE_DARK};
                color: {Theme.TEXT_DISABLED};
            }}
            
            /* BUTONLAR - Minimal ve profesyonel */
            QPushButton {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SM};
                padding: 10px 20px;
                font-weight: 500;
                font-size: {Theme.FONT_SIZE_BASE};
                color: {Theme.TEXT_PRIMARY};
            }}
            
            QPushButton:hover {{
                background-color: {Theme.SURFACE_DARK};
                border-color: {Theme.PRIMARY_LIGHT};
            }}
            
            QPushButton:pressed {{
                background-color: {Theme.DIVIDER};
            }}
            
            QPushButton:disabled {{
                background-color: {Theme.SURFACE_DARK};
                color: {Theme.TEXT_DISABLED};
                border-color: {Theme.BORDER_LIGHT};
            }}
            
            /* PRIMARY BUTTON */
            QPushButton#PrimaryButton,
            QPushButton[text="KAYDET"],
            QPushButton[text="SİPARİŞİ KAYDET"],
            QPushButton[text="⟳ GÜNCELLE"] {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                font-weight: 500;
            }}
            
            QPushButton#PrimaryButton:hover,
            QPushButton[text="KAYDET"]:hover,
            QPushButton[text="⟳ GÜNCELLE"]:hover {{
                background-color: {Theme.PRIMARY_DARK};
            }}
            
            /* ACCENT BUTTON */
            QPushButton#AccentButton {{
                background-color: {Theme.WARNING};
                color: white;
                border: none;
            }}
            
            QPushButton#AccentButton:hover {{
                background-color: #FB8C00;
            }}
            
            /* GHOST BUTTON - Şeffaf */
            QPushButton#GhostButton {{
                background-color: transparent;
                border: 1px solid {Theme.BORDER};
                color: {Theme.TEXT_SECONDARY};
            }}
            
            QPushButton#GhostButton:hover {{
                background-color: {Theme.SURFACE_DARK};
                border-color: {Theme.PRIMARY};
                color: {Theme.PRIMARY};
            }}

            /* TABLOLAR - Temiz ve minimal */
            QTableWidget {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER_LIGHT};
                gridline-color: {Theme.DIVIDER};
                outline: none;
                selection-background-color: {Theme.PRIMARY_LIGHT};
                selection-color: white;
                border-radius: {Theme.RADIUS_MD};
            }}
            
            QHeaderView::section {{
                background-color: {Theme.SURFACE_DARK};
                color: {Theme.TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {Theme.DIVIDER};
                padding: 14px 16px;
                font-weight: 600;
                font-size: {Theme.FONT_SIZE_SM};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QTableWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {Theme.DIVIDER};
            }}
            
            QTableWidget::item:selected {{
                background-color: rgba(38, 166, 154, 0.1);
                color: {Theme.TEXT_PRIMARY};
            }}

            /* SIDEBAR - Minimal ve temiz */
            QFrame#Sidebar {{
                background-color: {Theme.SURFACE};
                border: none;
                border-right: 1px solid {Theme.DIVIDER};
            }}
            
            /* TABS */
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER_LIGHT};
                background: {Theme.SURFACE};
                border-radius: {Theme.RADIUS_MD};
                top: -1px;
            }}
            
            QTabBar::tab {{
                background: transparent;
                color: {Theme.TEXT_SECONDARY};
                padding: 12px 24px;
                border: none;
                border-bottom: 2px solid transparent;
                margin-right: 8px;
                font-weight: 500;
            }}
            
            QTabBar::tab:hover {{
                color: {Theme.PRIMARY};
                background-color: {Theme.SURFACE_DARK};
            }}
            
            QTabBar::tab:selected {{
                background: transparent;
                color: {Theme.PRIMARY};
                border-bottom: 2px solid {Theme.PRIMARY};
            }}

            /* SCROLLBAR - İnce ve minimal */
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER};
                min-height: 30px;
                border-radius: 3px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {Theme.PRIMARY_LIGHT};
            }}
            
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                border: none;
                background: transparent;
                height: 6px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {Theme.BORDER};
                min-width: 30px;
                border-radius: 3px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {Theme.PRIMARY_LIGHT};
            }}
            
            /* SCROLL AREA */
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            /* TOOLTIP */
            QToolTip {{
                background-color: {Theme.TEXT_PRIMARY};
                color: white;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                padding: 6px 12px;
                font-size: {Theme.FONT_SIZE_SM};
            }}
        """
        
        app.setStyleSheet(style)