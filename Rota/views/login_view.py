import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QGraphicsDropShadowEffect, 
                               QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor, QFont

try:
    from core.db_manager import db
    from ui.theme import Theme
except ImportError:
    pass


class LoginView(QWidget):
    login_successful = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("REFLEKS 360 ROTA - Giriş")
        self.resize(1200, 800)
        # Arka planı tema renginden al
        self.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # --- ORTA KART - Daha minimal ---
        self.login_card = QFrame()
        self.login_card.setFixedSize(420, 520)
        self.login_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER_LIGHT};
                border-radius: {Theme.RADIUS_LG};
            }}
        """)
        
        # Yumuşak gölge
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.login_card.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.login_card)

        # --- KART İÇERİĞİ ---
        card_layout = QVBoxLayout(self.login_card)
        card_layout.setContentsMargins(48, 56, 48, 48)
        card_layout.setSpacing(24)

        # Logo/Brand alanı
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(8)
        
        # Başlık - Daha temiz
        title = QLabel("REFLEKS 360 ROTA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-family: {Theme.FONT_FAMILY}; 
            font-size: 32px;
            font-weight: 700;
            color: {Theme.TEXT_PRIMARY};
            letter-spacing: 1px;
        """)
        brand_layout.addWidget(title)
        
        # Alt başlık - Daha yumuşak
        subtitle = QLabel("Üretim Yönetim Sistemi")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 13px; 
            font-weight: 500; 
            color: {Theme.TEXT_SECONDARY}; 
            letter-spacing: 0.5px;
        """)
        brand_layout.addWidget(subtitle)
        
        card_layout.addLayout(brand_layout)
        card_layout.addSpacing(16)

        # Form alanı
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)

        # Kullanıcı Adı
        username_label = QLabel("Kullanıcı Adı")
        username_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {Theme.TEXT_PRIMARY};
            margin-bottom: 4px;
        """)
        form_layout.addWidget(username_label)
        
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Kullanıcı adınızı girin")
        self.txt_username.setMinimumHeight(48)
        self.txt_username.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SM};
                padding: 0 16px;
                background-color: {Theme.SURFACE};
                font-size: 14px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ 
                border: 2px solid {Theme.PRIMARY}; 
                padding: 0 15px;
            }}
            QLineEdit::placeholder {{
                color: {Theme.TEXT_HINT};
            }}
        """)
        form_layout.addWidget(self.txt_username)
        
        form_layout.addSpacing(8)

        # Şifre
        password_label = QLabel("Şifre")
        password_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {Theme.TEXT_PRIMARY};
            margin-bottom: 4px;
        """)
        form_layout.addWidget(password_label)
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Şifrenizi girin")
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setMinimumHeight(48)
        self.txt_password.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SM};
                padding: 0 16px;
                background-color: {Theme.SURFACE};
                font-size: 14px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ 
                border: 2px solid {Theme.PRIMARY}; 
                padding: 0 15px;
            }}
            QLineEdit::placeholder {{
                color: {Theme.TEXT_HINT};
            }}
        """)
        self.txt_password.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.txt_password)

        card_layout.addLayout(form_layout)
        card_layout.addSpacing(8)

        # Giriş Butonu - Daha modern
        self.btn_login = QPushButton("GİRİŞ YAP")
        self.btn_login.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_login.setMinimumHeight(52)
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                font-size: 15px;
                font-weight: 600;
                border-radius: {Theme.RADIUS_SM};
                border: none;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{ 
                background-color: {Theme.PRIMARY_DARK}; 
            }}
            QPushButton:pressed {{
                background-color: {Theme.PRIMARY_DARK};
            }}
        """)
        self.btn_login.clicked.connect(self.handle_login)
        card_layout.addWidget(self.btn_login)

        card_layout.addStretch()
        
        # Alt Bilgi - Daha minimal
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignCenter)
        
        lbl_ver = QLabel("v2.0")
        lbl_ver.setStyleSheet(f"""
            color: {Theme.TEXT_HINT}; 
            font-size: 11px;
            font-weight: 500;
        """)
        footer_layout.addWidget(lbl_ver)
        
        separator = QLabel("•")
        separator.setStyleSheet(f"color: {Theme.TEXT_HINT}; font-size: 11px; margin: 0 8px;")
        footer_layout.addWidget(separator)
        
        lbl_powered = QLabel("Powered by Python")
        lbl_powered.setStyleSheet(f"""
            color: {Theme.TEXT_HINT}; 
            font-size: 11px;
            font-weight: 500;
        """)
        footer_layout.addWidget(lbl_powered)
        
        card_layout.addLayout(footer_layout)

    def handle_login(self):
        """Login işlemini yönet"""
        username = self.txt_username.text().strip()
        password = self.txt_password.text()

        if not username or not password:
            self.show_error("Eksik Bilgi", "Lütfen kullanıcı adı ve şifre giriniz.")
            return

        user = db.check_login(username, password)
        
        if user:
            self.login_successful.emit(user)
        else:
            self.show_error("Giriş Başarısız", "Kullanıcı adı veya şifre hatalı!")
            self.txt_password.clear()
            self.txt_password.setFocus()
    
    def show_error(self, title, message):
        """Hata mesajı göster - Minimal stil"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Theme.SURFACE};
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                padding: 8px 20px;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_DARK};
            }}
        """)
        msg.exec()