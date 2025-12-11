"""
EFES ROTA X - İstasyon Yönetimi Ayarları
Fabrika istasyonlarını ekleme, düzenleme, silme ve sıralama işlemleri
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QMessageBox, QDialog, QFormLayout,
    QCheckBox, QColorDialog, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon

from ui.colors import Colors, Styles
from core.factory_config import factory_config, StationGroup, StationInfo


class StationEditDialog(QDialog):
    """İstasyon düzenleme dialogu"""
    
    def __init__(self, station_info: StationInfo = None, parent=None):
        super().__init__(parent)
        self.station_info = station_info
        self.is_new = station_info is None
        self.selected_color = station_info.color_code if station_info else "#3498DB"
        
        self.setWindowTitle("Yeni İstasyon" if self.is_new else f"{station_info.name} Düzenle")
        self.setMinimumWidth(450)
        self.setup_ui()
        
        if station_info:
            self.load_station_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # İstasyon Adı
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: TEMPER C1")
        self.name_input.setStyleSheet(Styles.input_field())
        if not self.is_new:
            self.name_input.setEnabled(False)  # Mevcut istasyon adı değiştirilemez
        form_layout.addRow("İstasyon Adı:", self.name_input)
        
        # Grup
        self.group_combo = QComboBox()
        self.group_combo.setStyleSheet(Styles.input_field())
        for group in StationGroup:
            self.group_combo.addItem(group.value, group)
        form_layout.addRow("Grup:", self.group_combo)
        
        # Kapasite
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 10000)
        self.capacity_spin.setValue(500)
        self.capacity_spin.setSuffix(" m²/gün")
        self.capacity_spin.setStyleSheet(Styles.input_field())
        form_layout.addRow("Günlük Kapasite:", self.capacity_spin)
        
        # Sıra İndeksi
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 999)
        self.order_spin.setValue(50)
        self.order_spin.setStyleSheet(Styles.input_field())
        form_layout.addRow("Sıra Numarası:", self.order_spin)
        
        # Renk Seçimi
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(40, 30)
        self.color_preview.setStyleSheet(f"background-color: {self.selected_color}; border-radius: 4px;")
        color_layout.addWidget(self.color_preview)
        
        self.color_btn = QPushButton("Renk Seç")
        self.color_btn.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        form_layout.addRow("Renk:", color_layout)
        
        # Özellikler
        self.batch_check = QCheckBox("Batch İşlem İstasyonu (Temper gibi)")
        self.active_check = QCheckBox("Aktif")
        self.active_check.setChecked(True)
        
        form_layout.addRow("", self.batch_check)
        form_layout.addRow("", self.active_check)
        
        # Alternatifler
        self.alternatives_input = QLineEdit()
        self.alternatives_input.setPlaceholderText("Virgülle ayırın: TEMPER A1, TEMPER B1")
        self.alternatives_input.setStyleSheet(Styles.input_field())
        form_layout.addRow("Alternatifler:", self.alternatives_input)
        
        layout.addLayout(form_layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BTN_SECONDARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.BTN_SECONDARY_HOVER};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Kaydet")
        save_btn.setStyleSheet(Styles.button_primary())
        save_btn.clicked.connect(self.save_station)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def load_station_data(self):
        """Mevcut istasyon verilerini yükle"""
        self.name_input.setText(self.station_info.name)
        
        # Grubu seç
        for i in range(self.group_combo.count()):
            if self.group_combo.itemData(i) == self.station_info.group:
                self.group_combo.setCurrentIndex(i)
                break
        
        self.capacity_spin.setValue(self.station_info.default_capacity)
        self.order_spin.setValue(self.station_info.order_index)
        self.batch_check.setChecked(self.station_info.is_batch_station)
        self.active_check.setChecked(self.station_info.is_active)
        self.alternatives_input.setText(", ".join(self.station_info.alternatives))
        self.selected_color = self.station_info.color_code
        self.color_preview.setStyleSheet(f"background-color: {self.selected_color}; border-radius: 4px;")
    
    def select_color(self):
        """Renk seçici aç"""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Renk Seç")
        if color.isValid():
            self.selected_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.selected_color}; border-radius: 4px;")
    
    def save_station(self):
        """İstasyonu kaydet"""
        name = self.name_input.text().strip().upper()
        
        if not name:
            QMessageBox.warning(self, "Hata", "İstasyon adı boş olamaz!")
            return
        
        if self.is_new and name in factory_config.get_all_stations(active_only=False):
            QMessageBox.warning(self, "Hata", f"'{name}' istasyonu zaten mevcut!")
            return
        
        # Alternatifleri parse et
        alternatives = []
        if self.alternatives_input.text().strip():
            alternatives = [a.strip().upper() for a in self.alternatives_input.text().split(",")]
        
        self.result_data = {
            'name': name,
            'group': self.group_combo.currentData(),
            'default_capacity': self.capacity_spin.value(),
            'order_index': self.order_spin.value(),
            'is_batch_station': self.batch_check.isChecked(),
            'is_active': self.active_check.isChecked(),
            'alternatives': alternatives,
            'color_code': self.selected_color
        }
        
        self.accept()


class StationSettingsWidget(QWidget):
    """İstasyon ayarları widget'ı"""
    
    stations_changed = Signal()  # İstasyonlar değiştiğinde sinyal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_stations()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Başlık ve butonlar
        header_layout = QHBoxLayout()
        
        title = QLabel("İstasyon Yönetimi")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Yeni istasyon butonu
        add_btn = QPushButton("+ Yeni İstasyon")
        add_btn.setStyleSheet(Styles.button_success())
        add_btn.clicked.connect(self.add_station)
        header_layout.addWidget(add_btn)
        
        # Sıfırla butonu
        reset_btn = QPushButton("Varsayılana Dön")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BTN_SECONDARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.BTN_SECONDARY_HOVER};
            }}
        """)
        reset_btn.clicked.connect(self.reset_to_defaults)
        header_layout.addWidget(reset_btn)
        
        layout.addLayout(header_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "İstasyon", "Grup", "Kapasite", "Sıra", "Batch", "Aktif", "İşlemler"
        ])
        self.table.setStyleSheet(Styles.table())
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 150)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Grup bazlı özet
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.summary_label)
    
    def load_stations(self):
        """İstasyonları tabloya yükle"""
        stations = factory_config.get_all_stations(active_only=False)
        sorted_stations = sorted(stations.values(), key=lambda x: x.order_index)
        
        self.table.setRowCount(len(sorted_stations))
        
        for row, station in enumerate(sorted_stations):
            # İstasyon adı (renkli)
            name_item = QTableWidgetItem(station.name)
            name_item.setBackground(QColor(station.color_code))
            name_item.setForeground(QColor("white"))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Grup
            group_item = QTableWidgetItem(station.group.value)
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, group_item)
            
            # Kapasite
            capacity_item = QTableWidgetItem(f"{station.default_capacity} m²")
            capacity_item.setFlags(capacity_item.flags() & ~Qt.ItemIsEditable)
            capacity_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, capacity_item)
            
            # Sıra
            order_item = QTableWidgetItem(str(station.order_index))
            order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
            order_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, order_item)
            
            # Batch
            batch_item = QTableWidgetItem("✓" if station.is_batch_station else "")
            batch_item.setFlags(batch_item.flags() & ~Qt.ItemIsEditable)
            batch_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, batch_item)
            
            # Aktif
            active_item = QTableWidgetItem("✓" if station.is_active else "✗")
            active_item.setForeground(QColor(Colors.SUCCESS if station.is_active else Colors.DANGER))
            active_item.setFlags(active_item.flags() & ~Qt.ItemIsEditable)
            active_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, active_item)
            
            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.setSpacing(5)
            
            edit_btn = QPushButton("Düzenle")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BTN_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.BTN_PRIMARY_HOVER};
                }}
            """)
            edit_btn.clicked.connect(lambda checked, s=station.name: self.edit_station(s))
            btn_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Sil")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BTN_DANGER};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.BTN_DANGER_HOVER};
                }}
            """)
            delete_btn.clicked.connect(lambda checked, s=station.name: self.delete_station(s))
            btn_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 6, btn_widget)
        
        self.update_summary()
    
    def update_summary(self):
        """Özet bilgisini güncelle"""
        groups = factory_config.get_station_groups()
        summary_parts = []
        for group_name, stations in groups.items():
            summary_parts.append(f"{group_name}: {len(stations)}")
        
        total = sum(len(s) for s in groups.values())
        self.summary_label.setText(f"Toplam {total} istasyon | " + " | ".join(summary_parts))
    
    def add_station(self):
        """Yeni istasyon ekle"""
        dialog = StationEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.result_data
            success = factory_config.add_station(
                name=data['name'],
                group=data['group'],
                capacity=data['default_capacity'],
                order_index=data['order_index'],
                is_batch_station=data['is_batch_station'],
                is_active=data['is_active'],
                alternatives=data['alternatives'],
                color_code=data['color_code']
            )
            
            if success:
                self.load_stations()
                self.stations_changed.emit()
                QMessageBox.information(self, "Başarılı", f"'{data['name']}' istasyonu eklendi.")
            else:
                QMessageBox.warning(self, "Hata", "İstasyon eklenemedi!")
    
    def edit_station(self, station_name: str):
        """İstasyonu düzenle"""
        station = factory_config.get_station(station_name)
        if not station:
            return
        
        dialog = StationEditDialog(station, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.result_data
            success = factory_config.update_station(
                station_name,
                default_capacity=data['default_capacity'],
                order_index=data['order_index'],
                is_batch_station=data['is_batch_station'],
                is_active=data['is_active'],
                alternatives=data['alternatives'],
                color_code=data['color_code']
            )
            
            if success:
                self.load_stations()
                self.stations_changed.emit()
    
    def delete_station(self, station_name: str):
        """İstasyonu sil (deaktif et)"""
        reply = QMessageBox.question(
            self, "Onay",
            f"'{station_name}' istasyonunu silmek istediğinize emin misiniz?\n\n"
            "Not: İstasyon tamamen silinmez, sadece deaktif edilir.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            factory_config.remove_station(station_name)
            self.load_stations()
            self.stations_changed.emit()
    
    def reset_to_defaults(self):
        """Varsayılan ayarlara dön"""
        reply = QMessageBox.question(
            self, "Onay",
            "Tüm istasyon ayarları varsayılana döndürülecek.\n\n"
            "Eklediğiniz özel istasyonlar silinecek.\n"
            "Devam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            factory_config._load_defaults()
            # Veritabanını da sıfırla
            if factory_config._db:
                try:
                    with factory_config._db.get_connection() as conn:
                        conn.execute("DELETE FROM stations")
                        factory_config._create_stations_table(conn)
                except Exception as e:
                    print(f"Sıfırlama hatası: {e}")
            
            self.load_stations()
            self.stations_changed.emit()
            QMessageBox.information(self, "Başarılı", "İstasyonlar varsayılan ayarlara döndürüldü.")


class CapacitySettingsWidget(QWidget):
    """Kapasite ayarları widget'ı - Hızlı kapasite düzenleme"""
    
    capacities_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.capacity_inputs = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("Günlük Kapasite Ayarları")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Grup bazlı kapasiteler
        groups = factory_config.get_station_groups()
        
        for group_name, stations in groups.items():
            group_box = QGroupBox(group_name)
            group_box.setStyleSheet(Styles.group_box())
            group_layout = QGridLayout(group_box)
            group_layout.setSpacing(10)
            
            for i, station_name in enumerate(stations):
                station = factory_config.get_station(station_name)
                if not station:
                    continue
                
                row = i // 2
                col = (i % 2) * 2
                
                label = QLabel(station_name)
                label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
                group_layout.addWidget(label, row, col)
                
                spin = QSpinBox()
                spin.setRange(1, 10000)
                spin.setValue(station.default_capacity)
                spin.setSuffix(" m²")
                spin.setStyleSheet(Styles.input_field())
                spin.setFixedWidth(120)
                group_layout.addWidget(spin, row, col + 1)
                
                self.capacity_inputs[station_name] = spin
            
            scroll_layout.addWidget(group_box)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Kaydet butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("Kapasiteleri Kaydet")
        save_btn.setStyleSheet(Styles.button_primary())
        save_btn.clicked.connect(self.save_capacities)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def save_capacities(self):
        """Kapasiteleri kaydet"""
        for station_name, spin in self.capacity_inputs.items():
            factory_config.update_capacity(station_name, spin.value())
        
        self.capacities_changed.emit()
        QMessageBox.information(self, "Başarılı", "Kapasiteler kaydedildi.")
    
    def refresh(self):
        """Kapasiteleri yenile"""
        for station_name, spin in self.capacity_inputs.items():
            station = factory_config.get_station(station_name)
            if station:
                spin.setValue(station.default_capacity)