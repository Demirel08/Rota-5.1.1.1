"""
EFES ROTA X - Sistem Ayarlari
Excel temali, kompakt tasarim
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QMessageBox, QFrame, 
    QAbstractItemView, QTabWidget, QSpinBox, QScrollArea,
    QGridLayout, QGroupBox, QDialog, QFormLayout,
    QCheckBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

try:
    from core.db_manager import db
    from core.factory_config import factory_config, StationGroup
except ImportError as e:
    print(f"Import hatasi: {e}")
    db = None
    factory_config = None


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
    WARNING = "#C65911"
    SUCCESS = "#107C41"
    INFO = "#0066CC"


# =============================================================================
# ANA AYARLAR EKRANI
# =============================================================================
class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_users()

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
        
        title = QLabel("Sistem Ayarlari")
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
        
        # Sekme 1: Personel Yonetimi
        self.tab_users = QWidget()
        self.setup_users_tab()
        self.tabs.addTab(self.tab_users, "Personel Yonetimi")
        
        # Sekme 2: Istasyon Ayarlari (YENİ - Excel tarzı)
        self.tab_stations = QWidget()
        self.setup_stations_tab()
        self.tabs.addTab(self.tab_stations, "Istasyon Ayarlari")

        # Sekme 3: Istasyon Yönetimi (İsim/Kategori Düzenleme)
        self.tab_station_mgmt = QWidget()
        self.setup_station_management_tab()
        self.tabs.addTab(self.tab_station_mgmt, "Istasyon Yonetimi")

        layout.addWidget(self.tabs)

    # =========================================================================
    # SEKME 1: PERSONEL YONETIMI
    # =========================================================================
    def setup_users_tab(self):
        layout = QHBoxLayout(self.tab_users)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # SOL: FORM
        form_frame = QFrame()
        form_frame.setFixedWidth(280)
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(12)
        
        # Form basligi
        form_title = QLabel("Yeni Kullanici Ekle")
        form_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT}; background: transparent;")
        form_layout.addWidget(form_title)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.BORDER};")
        form_layout.addWidget(sep)
        
        # Form alanlari
        label_style = f"font-size: 11px; color: {Colors.TEXT_SECONDARY}; background: transparent;"
        input_style = f"""
            QLineEdit, QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 6px 10px;
                font-size: 11px;
                background-color: {Colors.BG};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {Colors.ACCENT};
            }}
        """
        
        form_layout.addWidget(QLabel("Ad Soyad:"))
        form_layout.itemAt(form_layout.count()-1).widget().setStyleSheet(label_style)
        self.inp_name = QLineEdit()
        self.inp_name.setStyleSheet(input_style)
        form_layout.addWidget(self.inp_name)
        
        form_layout.addWidget(QLabel("Kullanici Adi:"))
        form_layout.itemAt(form_layout.count()-1).widget().setStyleSheet(label_style)
        self.inp_user = QLineEdit()
        self.inp_user.setStyleSheet(input_style)
        form_layout.addWidget(self.inp_user)
        
        form_layout.addWidget(QLabel("Sifre:"))
        form_layout.itemAt(form_layout.count()-1).widget().setStyleSheet(label_style)
        self.inp_pass = QLineEdit()
        self.inp_pass.setEchoMode(QLineEdit.Password)
        self.inp_pass.setStyleSheet(input_style)
        form_layout.addWidget(self.inp_pass)
        
        form_layout.addWidget(QLabel("Rol:"))
        form_layout.itemAt(form_layout.count()-1).widget().setStyleSheet(label_style)
        self.combo_role = QComboBox()
        self.combo_role.addItems(["operator", "admin", "planlama"])
        self.combo_role.setStyleSheet(input_style)
        self.combo_role.currentTextChanged.connect(self.toggle_station_combo)
        form_layout.addWidget(self.combo_role)
        
        form_layout.addWidget(QLabel("Istasyon:"))
        form_layout.itemAt(form_layout.count()-1).widget().setStyleSheet(label_style)
        self.combo_station = QComboBox()
        self.combo_station.setStyleSheet(input_style)
        self.combo_station.addItem("-")
        
        # Istasyonlari factory_config'den al
        if factory_config:
            try:
                for station in factory_config.get_station_order():
                    self.combo_station.addItem(station)
            except:
                pass
        form_layout.addWidget(self.combo_station)
        
        form_layout.addStretch()
        
        # Kaydet butonu
        btn_save = QPushButton("Kullanici Ekle")
        btn_save.setFixedHeight(34)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"""
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
        btn_save.clicked.connect(self.save_user)
        form_layout.addWidget(btn_save)
        
        layout.addWidget(form_frame)
        
        # SAG: TABLO
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Tablo basligi
        table_header = QHBoxLayout()
        table_title = QLabel("Kayitli Kullanicilar")
        table_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT};")
        table_header.addWidget(table_title)
        table_header.addStretch()
        
        btn_del = QPushButton("Seciliyi Sil")
        btn_del.setFixedHeight(28)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.CRITICAL};
                border-radius: 3px;
                padding: 0 12px;
                color: {Colors.CRITICAL};
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.CRITICAL};
                color: white;
            }}
        """)
        btn_del.clicked.connect(self.delete_user)
        table_header.addWidget(btn_del)
        
        right_layout.addLayout(table_header)
        
        # Tablo
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(["ID", "Ad Soyad", "Kullanici", "Rol", "Istasyon"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.user_table.setColumnWidth(0, 50)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                gridline-color: {Colors.GRID};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px;
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
                border-bottom: 1px solid {Colors.BORDER};
                border-right: 1px solid {Colors.GRID};
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """)
        right_layout.addWidget(self.user_table)
        
        layout.addWidget(right_frame, 1)

    # =========================================================================
    # SEKME 2: ISTASYON AYARLARI (Excel tarzi)
    # =========================================================================
    def setup_stations_tab(self):
        layout = QVBoxLayout(self.tab_stations)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Ust bilgi
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #E3F2FD;
                border: 1px solid #90CAF9;
                border-radius: 4px;
            }}
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)
        
        info_icon = QLabel("ℹ")
        info_icon.setStyleSheet(f"font-size: 14px; color: {Colors.INFO};")
        info_layout.addWidget(info_icon)
        
        info_text = QLabel("Istasyon kapasitelerini buradan ayarlayabilirsiniz. Degisiklikler aninda uygulanir.")
        info_text.setStyleSheet(f"font-size: 11px; color: {Colors.INFO};")
        info_layout.addWidget(info_text)
        info_layout.addStretch()
        
        layout.addWidget(info_frame)
        
        # Scroll alani
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: {Colors.BG};
            }}
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(16, 16, 16, 16)
        scroll_layout.setSpacing(20)
        
        # Grup bazli istasyonlar
        if factory_config:
            groups = factory_config.get_station_groups()
            
            self.capacity_inputs = {}
            
            for group_name, stations in groups.items():
                # Grup basligi
                group_frame = QFrame()
                group_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.HEADER_BG};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 4px;
                    }}
                """)
                group_layout = QVBoxLayout(group_frame)
                group_layout.setContentsMargins(0, 0, 0, 0)
                group_layout.setSpacing(0)
                
                # Grup header
                group_header = QFrame()
                group_header.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Colors.ACCENT};
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                    }}
                """)
                header_layout = QHBoxLayout(group_header)
                header_layout.setContentsMargins(12, 8, 12, 8)
                
                group_title = QLabel(group_name)
                group_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: white;")
                header_layout.addWidget(group_title)
                
                group_count = QLabel(f"({len(stations)} istasyon)")
                group_count.setStyleSheet(f"font-size: 10px; color: rgba(255,255,255,0.7);")
                header_layout.addWidget(group_count)
                header_layout.addStretch()
                
                group_layout.addWidget(group_header)
                
                # Istasyonlar tablosu
                for i, station_name in enumerate(stations):
                    station = factory_config.get_station(station_name)
                    if not station:
                        continue
                    
                    row = QFrame()
                    row.setStyleSheet(f"""
                        QFrame {{
                            background-color: {Colors.ROW_ALT if i % 2 else Colors.BG};
                            border-bottom: 1px solid {Colors.GRID};
                        }}
                    """)
                    row_layout = QHBoxLayout(row)
                    row_layout.setContentsMargins(12, 8, 12, 8)
                    row_layout.setSpacing(16)
                    
                    # Istasyon adi
                    lbl_name = QLabel(station_name)
                    lbl_name.setFixedWidth(140)
                    lbl_name.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.TEXT};")
                    row_layout.addWidget(lbl_name)
                    
                    # Kapasite input
                    spin = QSpinBox()
                    spin.setRange(1, 10000)
                    spin.setValue(station.default_capacity)
                    spin.setSuffix(" m²/gun")
                    spin.setFixedWidth(120)
                    spin.setStyleSheet(f"""
                        QSpinBox {{
                            border: 1px solid {Colors.BORDER};
                            border-radius: 3px;
                            padding: 4px 8px;
                            font-size: 11px;
                            background-color: {Colors.BG};
                        }}
                        QSpinBox:focus {{
                            border-color: {Colors.ACCENT};
                        }}
                    """)
                    row_layout.addWidget(spin)
                    self.capacity_inputs[station_name] = spin
                    
                    # Durum
                    status_text = "Aktif" if station.is_active else "Pasif"
                    status_color = Colors.SUCCESS if station.is_active else Colors.TEXT_MUTED
                    lbl_status = QLabel(f"● {status_text}")
                    lbl_status.setStyleSheet(f"font-size: 10px; color: {status_color};")
                    row_layout.addWidget(lbl_status)
                    
                    row_layout.addStretch()
                    
                    group_layout.addWidget(row)
                
                scroll_layout.addWidget(group_frame)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # Alt butonlar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        
        btn_save_all = QPushButton("Tum Kapasiteleri Kaydet")
        btn_save_all.setFixedHeight(34)
        btn_save_all.setCursor(Qt.PointingHandCursor)
        btn_save_all.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 4px;
                padding: 0 24px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_save_all.clicked.connect(self.save_all_capacities)
        bottom_bar.addWidget(btn_save_all)
        
        layout.addLayout(bottom_bar)

    # =========================================================================
    # FONKSIYONLAR
    # =========================================================================
    def refresh_users(self):
        if not db:
            return
        self.user_table.setRowCount(0)
        users = db.get_all_users()
        self.user_table.setRowCount(len(users))
        for r, u in enumerate(users):
            self.user_table.setItem(r, 0, QTableWidgetItem(str(u['id'])))
            self.user_table.setItem(r, 1, QTableWidgetItem(u['full_name']))
            self.user_table.setItem(r, 2, QTableWidgetItem(u['username']))
            self.user_table.setItem(r, 3, QTableWidgetItem(u['role']))
            self.user_table.setItem(r, 4, QTableWidgetItem(u['station_name'] or "-"))

    def toggle_station_combo(self, text):
        self.combo_station.setEnabled(text == "operator")

    def save_user(self):
        if not db:
            return
        name = self.inp_name.text().strip()
        user = self.inp_user.text().strip()
        pwd = self.inp_pass.text()
        
        if not name or not user or not pwd:
            QMessageBox.warning(self, "Uyari", "Tum alanlari doldurun!")
            return
        
        role = self.combo_role.currentText()
        st = self.combo_station.currentText() if role == "operator" else None
        if st == "-":
            st = None
        
        success, msg = db.add_new_user(user, pwd, role, name, st)
        if success:
            self.refresh_users()
            self.inp_name.clear()
            self.inp_user.clear()
            self.inp_pass.clear()
            QMessageBox.information(self, "Basarili", "Kullanici eklendi.")
        else:
            QMessageBox.critical(self, "Hata", f"Eklenemedi: {msg}")

    def delete_user(self):
        if not db:
            return
        sel = self.user_table.selectedItems()
        if not sel:
            QMessageBox.warning(self, "Uyari", "Silmek icin bir kullanici secin.")
            return
        
        uid = int(self.user_table.item(sel[0].row(), 0).text())
        
        reply = QMessageBox.question(
            self, "Onay", 
            "Bu kullaniciyi silmek istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if db.delete_user(uid):
                self.refresh_users()

    def save_all_capacities(self):
        """Tum kapasiteleri kaydet"""
        if not factory_config:
            return

        try:
            for station_name, spin in self.capacity_inputs.items():
                factory_config.update_capacity(station_name, spin.value())

            # Factory config'i yenile
            factory_config.refresh()

            QMessageBox.information(
                self, "Basarili",
                "Tum kapasite degerleri kaydedildi.\nPlanlama motoru yeni degerleri kullanacak."
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi: {e}")

    # =========================================================================
    # SEKME 3: ISTASYON YONETIMI (Isim/Kategori Duzenleme)
    # =========================================================================
    def setup_station_management_tab(self):
        layout = QVBoxLayout(self.tab_station_mgmt)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Ust bilgi
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFF3E0;
                border: 1px solid #FFB74D;
                border-radius: 4px;
            }}
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)

        info_icon = QLabel("⚙")
        info_icon.setStyleSheet(f"font-size: 14px; color: {Colors.WARNING};")
        info_layout.addWidget(info_icon)

        info_text = QLabel("Buradan istasyon isimlerini, kategorilerini duzenleyebilir ve yeni istasyon ekleyebilirsiniz.")
        info_text.setStyleSheet(f"font-size: 11px; color: {Colors.WARNING};")
        info_layout.addWidget(info_text)
        info_layout.addStretch()

        layout.addWidget(info_frame)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_add = QPushButton("+ Yeni Istasyon Ekle")
        btn_add.setFixedHeight(32)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SUCCESS};
                border: none;
                border-radius: 4px;
                padding: 0 20px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0D8A3F;
            }}
        """)
        btn_add.clicked.connect(self.add_new_station)
        btn_layout.addWidget(btn_add)

        layout.addLayout(btn_layout)

        # Tablo
        self.station_table = QTableWidget()
        self.station_table.setColumnCount(6)
        self.station_table.setHorizontalHeaderLabels([
            "Istasyon Adi", "Kategori", "Kapasite", "Sira", "Durum", "Islemler"
        ])

        header = self.station_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)

        # Sütun genişliklerini ayarla
        self.station_table.setColumnWidth(0, 180)  # Istasyon Adi
        self.station_table.setColumnWidth(1, 150)  # Kategori
        self.station_table.setColumnWidth(2, 120)  # Kapasite
        self.station_table.setColumnWidth(3, 60)   # Sira
        self.station_table.setColumnWidth(4, 80)   # Durum
        self.station_table.setColumnWidth(5, 200)  # Islemler

        self.station_table.verticalHeader().setVisible(False)
        self.station_table.verticalHeader().setDefaultSectionSize(40)  # Satır yüksekliği
        self.station_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.station_table.setAlternatingRowColors(True)
        self.station_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                gridline-color: {Colors.GRID};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px;
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
                border-bottom: 1px solid {Colors.BORDER};
                border-right: 1px solid {Colors.GRID};
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """)

        layout.addWidget(self.station_table)

        # Tabloyu doldur
        self.refresh_station_table()

    def refresh_station_table(self):
        """Istasyon tablosunu yenile"""
        if not factory_config:
            return

        self.station_table.setRowCount(0)
        stations = factory_config.get_all_stations(active_only=False)

        row = 0
        for name, info in sorted(stations.items(), key=lambda x: x[1].order_index):
            self.station_table.insertRow(row)

            # Istasyon adi
            name_item = QTableWidgetItem(info.name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.station_table.setItem(row, 0, name_item)

            # Kategori
            group_item = QTableWidgetItem(info.group.value)
            group_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.station_table.setItem(row, 1, group_item)

            # Kapasite
            cap_item = QTableWidgetItem(f"{info.default_capacity} m²/gun")
            cap_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.station_table.setItem(row, 2, cap_item)

            # Sira
            order_item = QTableWidgetItem(str(info.order_index))
            order_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.station_table.setItem(row, 3, order_item)

            # Durum
            status_item = QTableWidgetItem("Aktif" if info.is_active else "Pasif")
            status_item.setForeground(QColor(Colors.SUCCESS if info.is_active else Colors.TEXT_MUTED))
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.station_table.setItem(row, 4, status_item)

            # Islem butonlari
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            btn_edit = QPushButton("Duzenle")
            btn_edit.setFixedSize(85, 28)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.INFO};
                    border: none;
                    border-radius: 3px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #0052A3;
                }}
            """)
            btn_edit.clicked.connect(lambda checked, n=name: self.edit_station(n))
            btn_layout.addWidget(btn_edit)

            if info.is_active:
                btn_deactivate = QPushButton("Pasif Et")
                btn_deactivate.setFixedSize(85, 28)
                btn_deactivate.setCursor(Qt.PointingHandCursor)
                btn_deactivate.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.TEXT_MUTED};
                        border: none;
                        border-radius: 3px;
                        color: white;
                        font-size: 10px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: #666666;
                    }}
                """)
                btn_deactivate.clicked.connect(lambda checked, n=name: self.toggle_station_status(n))
                btn_layout.addWidget(btn_deactivate)
            else:
                btn_activate = QPushButton("Aktif Et")
                btn_activate.setFixedSize(85, 28)
                btn_activate.setCursor(Qt.PointingHandCursor)
                btn_activate.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.SUCCESS};
                        border: none;
                        border-radius: 3px;
                        color: white;
                        font-size: 10px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: #0D8A3F;
                    }}
                """)
                btn_activate.clicked.connect(lambda checked, n=name: self.toggle_station_status(n))
                btn_layout.addWidget(btn_activate)

            btn_layout.addStretch()
            self.station_table.setCellWidget(row, 5, btn_widget)

            row += 1

    def add_new_station(self):
        """Yeni istasyon ekle dialog"""
        dialog = StationEditDialog(self, mode="add")
        if dialog.exec():
            self.refresh_station_table()
            QMessageBox.information(self, "Basarili", "Yeni istasyon eklendi.")

    def edit_station(self, station_name):
        """Istasyon duzenle"""
        dialog = StationEditDialog(self, mode="edit", station_name=station_name)
        if dialog.exec():
            self.refresh_station_table()
            QMessageBox.information(self, "Basarili", "Istasyon bilgileri guncellendi.")

    def toggle_station_status(self, station_name):
        """Istasyon aktif/pasif durumunu degistir"""
        if not factory_config:
            return

        station = factory_config.get_station(station_name)
        if not station:
            return

        new_status = not station.is_active
        factory_config.update_station(station_name, is_active=new_status)
        factory_config.refresh()
        self.refresh_station_table()


# =============================================================================
# ISTASYON DUZENLEME DIALOG
# =============================================================================
class StationEditDialog(QDialog):
    """Istasyon ekleme/duzenleme dialogu"""

    def __init__(self, parent=None, mode="add", station_name=None):
        super().__init__(parent)
        self.mode = mode
        self.station_name = station_name

        self.setWindowTitle("Yeni Istasyon Ekle" if mode == "add" else f"Istasyon Duzenle: {station_name}")
        self.setFixedSize(450, 400)
        self.setStyleSheet(f"background-color: {Colors.BG};")

        self.setup_ui()

        if mode == "edit" and station_name:
            self.load_station_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        label_style = f"font-size: 11px; color: {Colors.TEXT}; font-weight: bold;"
        input_style = f"""
            QLineEdit, QComboBox, QSpinBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 6px 10px;
                font-size: 11px;
                background-color: {Colors.BG};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border-color: {Colors.ACCENT};
            }}
        """

        # Istasyon adi
        lbl_name = QLabel("Istasyon Adi:")
        lbl_name.setStyleSheet(label_style)
        self.inp_name = QLineEdit()
        self.inp_name.setStyleSheet(input_style)
        self.inp_name.setEnabled(self.mode == "add")  # Adi sadece ekleme modunda degistirilebilir
        form_layout.addRow(lbl_name, self.inp_name)

        # Kategori
        lbl_group = QLabel("Kategori:")
        lbl_group.setStyleSheet(label_style)
        self.combo_group = QComboBox()
        self.combo_group.setStyleSheet(input_style)
        self.combo_group.addItems([g.value for g in StationGroup])
        form_layout.addRow(lbl_group, self.combo_group)

        # Kapasite
        lbl_capacity = QLabel("Kapasite (m²/gun):")
        lbl_capacity.setStyleSheet(label_style)
        self.spin_capacity = QSpinBox()
        self.spin_capacity.setStyleSheet(input_style)
        self.spin_capacity.setRange(1, 10000)
        self.spin_capacity.setValue(500)
        form_layout.addRow(lbl_capacity, self.spin_capacity)

        # Sira indeksi
        lbl_order = QLabel("Sira Indeksi:")
        lbl_order.setStyleSheet(label_style)
        self.spin_order = QSpinBox()
        self.spin_order.setStyleSheet(input_style)
        self.spin_order.setRange(1, 999)
        self.spin_order.setValue(50)
        form_layout.addRow(lbl_order, self.spin_order)

        # Renk kodu
        lbl_color = QLabel("Renk Kodu:")
        lbl_color.setStyleSheet(label_style)

        color_layout = QHBoxLayout()
        self.inp_color = QLineEdit("#3498DB")
        self.inp_color.setStyleSheet(input_style)
        color_layout.addWidget(self.inp_color)

        btn_color = QPushButton("Sec")
        btn_color.setFixedSize(60, 30)
        btn_color.setCursor(Qt.PointingHandCursor)
        btn_color.clicked.connect(self.choose_color)
        btn_color.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BORDER};
                border: none;
                border-radius: 3px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #C0C0C0;
            }}
        """)
        color_layout.addWidget(btn_color)

        form_layout.addRow(lbl_color, color_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Iptal")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BORDER};
                border: none;
                border-radius: 4px;
                padding: 0 20px;
                color: {Colors.TEXT};
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C0C0C0;
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Kaydet")
        btn_save.setFixedHeight(34)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"""
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
        btn_save.clicked.connect(self.save_station)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def load_station_data(self):
        """Duzenleme modunda mevcut istasyon verilerini yukle"""
        if not factory_config or not self.station_name:
            return

        station = factory_config.get_station(self.station_name)
        if not station:
            return

        self.inp_name.setText(station.name)
        self.combo_group.setCurrentText(station.group.value)
        self.spin_capacity.setValue(station.default_capacity)
        self.spin_order.setValue(station.order_index)
        self.inp_color.setText(station.color_code)

    def choose_color(self):
        """Renk secici ac"""
        current_color = QColor(self.inp_color.text())
        color = QColorDialog.getColor(current_color, self, "Renk Sec")
        if color.isValid():
            self.inp_color.setText(color.name())

    def save_station(self):
        """Istasyon bilgilerini kaydet"""
        if not factory_config:
            QMessageBox.critical(self, "Hata", "Factory config bulunamadi!")
            return

        name = self.inp_name.text().strip().upper()
        if not name:
            QMessageBox.warning(self, "Uyari", "Istasyon adi bos olamaz!")
            return

        # Grup enum'unu bul
        group_text = self.combo_group.currentText()
        group = None
        for g in StationGroup:
            if g.value == group_text:
                group = g
                break

        if not group:
            QMessageBox.warning(self, "Uyari", "Gecerli bir kategori secin!")
            return

        capacity = self.spin_capacity.value()
        order_index = self.spin_order.value()
        color_code = self.inp_color.text()

        try:
            if self.mode == "add":
                # Yeni istasyon ekle
                success = factory_config.add_station(
                    name=name,
                    group=group,
                    capacity=capacity,
                    order_index=order_index,
                    color_code=color_code
                )
                if not success:
                    QMessageBox.critical(self, "Hata", "Bu isimde bir istasyon zaten var!")
                    return
            else:
                # Mevcut istasyonu guncelle
                factory_config.update_station(
                    self.station_name,
                    default_capacity=capacity,
                    order_index=order_index,
                    color_code=color_code
                )

            # Factory config'i yenile
            factory_config.refresh()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayit hatasi: {e}")