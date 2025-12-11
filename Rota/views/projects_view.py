"""
EFES ROTA X - Proje Yönetimi Ekranı
Müşteri bazlı toplu sipariş takibi
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QDialog, QLineEdit, QTextEdit,
    QComboBox, QMessageBox, QProgressBar, QListWidget, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

try:
    from core.db_manager import db
except ImportError:
    db = None


# =============================================================================
# TEMA RENKLERİ
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
# PROJE YÖNETIMI ANA EKRANI
# =============================================================================
class ProjectsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_projects()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # HEADER
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 2px solid {Colors.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Proje Yönetimi")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Colors.TEXT};")
        header_layout.addWidget(title)

        subtitle = QLabel("Müşteri bazlı toplu sipariş takibi")
        subtitle.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY}; margin-left: 20px;")
        header_layout.addWidget(subtitle)

        header_layout.addStretch()

        # Filtre combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tümü", "Aktif", "Tamamlandı"])
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                min-width: 120px;
            }}
        """)
        self.filter_combo.currentTextChanged.connect(self.refresh_projects)
        header_layout.addWidget(self.filter_combo)

        # Yeni proje butonu
        btn_new = QPushButton("+ Yeni Proje")
        btn_new.setFixedHeight(36)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0 24px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_new.clicked.connect(self.create_new_project)
        header_layout.addWidget(btn_new)

        layout.addWidget(header)

        # TABLO
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Proje Adı", "Müşteri", "Teslimat", "Durum", "İlerleme", "Sipariş/m²", "İşlemler"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)

        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 180)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                gridline-color: {Colors.GRID};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 8px;
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
                border-bottom: 2px solid {Colors.BORDER};
                border-right: 1px solid {Colors.GRID};
                padding: 10px;
                font-size: 11px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """)

        layout.addWidget(self.table)

    def refresh_projects(self):
        """Proje listesini yenile"""
        if not db:
            return

        self.table.setRowCount(0)

        # Filtre uygula
        filter_text = self.filter_combo.currentText()
        if filter_text == "Tümü":
            projects = db.get_all_projects()
        else:
            projects = db.get_all_projects(status_filter=filter_text)

        for row, project in enumerate(projects):
            self.table.insertRow(row)
            project_id = project['id']

            # Proje adı
            name_item = QTableWidgetItem(project['project_name'])
            name_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row, 0, name_item)

            # Müşteri
            customer_item = QTableWidgetItem(project.get('customer_name', '-'))
            self.table.setItem(row, 1, customer_item)

            # Teslimat
            delivery_item = QTableWidgetItem(project.get('delivery_date', '-'))
            self.table.setItem(row, 2, delivery_item)

            # Durum
            status = project['status']
            status_item = QTableWidgetItem(status)
            if status == 'Tamamlandı':
                status_item.setForeground(QColor(Colors.SUCCESS))
            else:
                status_item.setForeground(QColor(Colors.INFO))
            status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row, 3, status_item)

            # İlerleme
            summary = db.get_project_summary(project_id)
            progress_widget = QWidget()
            progress_layout = QVBoxLayout(progress_widget)
            progress_layout.setContentsMargins(4, 4, 4, 4)
            progress_layout.setSpacing(2)

            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            if summary:
                progress_percent = summary.get('progress_percent') or 0
                progress_bar.setValue(progress_percent)
            else:
                progress_bar.setValue(0)
            progress_bar.setTextVisible(True)
            progress_bar.setFormat("%p%")
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {Colors.BORDER};
                    border-radius: 3px;
                    text-align: center;
                    font-size: 9px;
                    font-weight: bold;
                    height: 18px;
                }}
                QProgressBar::chunk {{
                    background-color: {Colors.SUCCESS};
                }}
            """)
            progress_layout.addWidget(progress_bar)

            self.table.setCellWidget(row, 4, progress_widget)

            # Sipariş/m²
            if summary:
                total_orders = summary.get('total_orders') or 0
                total_m2 = summary.get('total_m2') or 0
                stats_text = f"{total_orders} sipariş\n{total_m2:.1f} m²"
            else:
                stats_text = "0 sipariş\n0.0 m²"
            stats_item = QTableWidgetItem(stats_text)
            stats_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, stats_item)

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            btn_detail = QPushButton("Detay")
            btn_detail.setFixedSize(70, 30)
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.setStyleSheet(f"""
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
            btn_detail.clicked.connect(lambda checked, pid=project_id: self.show_project_detail(pid))
            btn_layout.addWidget(btn_detail)

            btn_complete = QPushButton("Tamamla")
            btn_complete.setFixedSize(70, 30)
            btn_complete.setCursor(Qt.PointingHandCursor)
            btn_complete.setStyleSheet(f"""
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
            btn_complete.clicked.connect(lambda checked, pid=project_id: self.complete_project(pid))
            btn_layout.addWidget(btn_complete)

            btn_layout.addStretch()
            self.table.setCellWidget(row, 6, btn_widget)

    def create_new_project(self):
        """Yeni proje oluştur"""
        dialog = ProjectEditDialog(self, mode="add")
        if dialog.exec():
            self.refresh_projects()

    def show_project_detail(self, project_id):
        """Proje detayını göster"""
        dialog = ProjectDetailDialog(self, project_id)
        dialog.exec()
        self.refresh_projects()

    def complete_project(self, project_id):
        """Projeyi tamamla"""
        if not db:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu projeyi tamamlamak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            db.complete_project(project_id)
            self.refresh_projects()
            QMessageBox.information(self, "Başarılı", "Proje tamamlandı olarak işaretlendi.")


# =============================================================================
# PROJE EKLEME/DÜZENLEME DIALOGU
# =============================================================================
class ProjectEditDialog(QDialog):
    def __init__(self, parent=None, mode="add", project_id=None):
        super().__init__(parent)
        self.mode = mode
        self.project_id = project_id

        self.setWindowTitle("Yeni Proje Oluştur" if mode == "add" else "Proje Düzenle")
        self.setFixedSize(500, 480)
        self.setStyleSheet(f"background-color: {Colors.BG};")

        self.setup_ui()

        if mode == "edit" and project_id:
            self.load_project_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("Proje Bilgileri")
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(title)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        label_style = f"font-size: 11px; color: {Colors.TEXT}; font-weight: bold;"
        input_style = f"""
            QLineEdit, QComboBox, QTextEdit {{
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 8px;
                font-size: 11px;
                background-color: {Colors.BG};
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """

        # Proje adı
        lbl_name = QLabel("Proje Adı:")
        lbl_name.setStyleSheet(label_style)
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Örn: Yalıkavak Villa - Bay Ahmet")
        self.inp_name.setStyleSheet(input_style)
        form_layout.addRow(lbl_name, self.inp_name)

        # Müşteri
        lbl_customer = QLabel("Müşteri:")
        lbl_customer.setStyleSheet(label_style)
        self.inp_customer = QLineEdit()
        self.inp_customer.setPlaceholderText("Müşteri adı")
        self.inp_customer.setStyleSheet(input_style)
        form_layout.addRow(lbl_customer, self.inp_customer)

        # Teslimat tarihi
        lbl_delivery = QLabel("Teslimat Tarihi:")
        lbl_delivery.setStyleSheet(label_style)
        self.inp_delivery = QLineEdit()
        self.inp_delivery.setPlaceholderText("YYYY-MM-DD")
        self.inp_delivery.setStyleSheet(input_style)
        form_layout.addRow(lbl_delivery, self.inp_delivery)

        # Öncelik
        lbl_priority = QLabel("Öncelik:")
        lbl_priority.setStyleSheet(label_style)
        self.combo_priority = QComboBox()
        self.combo_priority.addItems(["Normal", "Acil", "Çok Acil", "Kritik"])
        self.combo_priority.setStyleSheet(input_style)
        form_layout.addRow(lbl_priority, self.combo_priority)

        # Sipariş Ön Eki
        lbl_prefix = QLabel("Sipariş Ön Eki:")
        lbl_prefix.setStyleSheet(label_style)
        self.inp_prefix = QLineEdit()
        self.inp_prefix.setPlaceholderText("Örn: YLK (Yalıkavak)")
        self.inp_prefix.setMaxLength(10)
        self.inp_prefix.setStyleSheet(input_style)
        form_layout.addRow(lbl_prefix, self.inp_prefix)

        # Notlar
        lbl_notes = QLabel("Notlar:")
        lbl_notes.setStyleSheet(label_style)
        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(80)
        self.inp_notes.setPlaceholderText("Proje hakkında notlar...")
        self.inp_notes.setStyleSheet(input_style)
        form_layout.addRow(lbl_notes, self.inp_notes)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("İptal")
        btn_cancel.setFixedHeight(36)
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
        btn_save.setFixedHeight(36)
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
        btn_save.clicked.connect(self.save_project)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def load_project_data(self):
        """Mevcut proje verilerini yükle"""
        if not db or not self.project_id:
            return

        project = db.get_project_by_id(self.project_id)
        if not project:
            return

        self.inp_name.setText(project['project_name'])
        self.inp_customer.setText(project.get('customer_name', ''))
        self.inp_delivery.setText(project.get('delivery_date', ''))
        self.combo_priority.setCurrentText(project.get('priority', 'Normal'))
        self.inp_prefix.setText(project.get('order_prefix', ''))
        self.inp_notes.setPlainText(project.get('notes', ''))

    def save_project(self):
        """Projeyi kaydet"""
        if not db:
            QMessageBox.critical(self, "Hata", "Veritabanı bağlantısı yok!")
            return

        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Proje adı boş olamaz!")
            return

        customer = self.inp_customer.text().strip()
        delivery = self.inp_delivery.text().strip() or None
        priority = self.combo_priority.currentText()
        notes = self.inp_notes.toPlainText().strip()
        order_prefix = self.inp_prefix.text().strip().upper()  # Büyük harf

        try:
            if self.mode == "add":
                # Otomatik renk seçimi
                try:
                    existing_projects = db.get_all_projects()
                    used_colors = [p.get('color', '') for p in existing_projects if p.get('color')]
                except:
                    used_colors = []

                available_colors = [
                    "#6B46C1", "#0066CC", "#107C41", "#C65911",
                    "#C00000", "#E83E8C", "#17A2B8", "#FFC107",
                    "#795548", "#9C27B0", "#FF5722", "#00BCD4"
                ]

                color = available_colors[0]
                for c in available_colors:
                    if c not in used_colors:
                        color = c
                        break

                project_data = {
                    'project_name': name,
                    'customer_name': customer,
                    'delivery_date': delivery,
                    'priority': priority,
                    'notes': notes,
                    'status': 'Aktif',
                    'color': color,
                    'order_prefix': order_prefix
                }
                db.add_project(project_data)
                QMessageBox.information(self, "Başarılı", "Proje oluşturuldu!")
            else:
                # Güncelleme - mevcut rengi koru
                db.update_project(
                    self.project_id,
                    project_name=name,
                    customer_name=customer,
                    delivery_date=delivery,
                    priority=priority,
                    notes=notes,
                    order_prefix=order_prefix
                )
                QMessageBox.information(self, "Başarılı", "Proje güncellendi!")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")


# =============================================================================
# PROJE DETAY DIALOGU
# =============================================================================
class ProjectDetailDialog(QDialog):
    def __init__(self, parent=None, project_id=None):
        super().__init__(parent)
        self.project_id = project_id

        self.setWindowTitle("Proje Detayı")
        self.setFixedSize(900, 600)
        self.setStyleSheet(f"background-color: {Colors.BG};")

        self.setup_ui()
        self.load_project_info()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Proje bilgileri
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(8)

        self.lbl_project_name = QLabel()
        self.lbl_project_name.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.TEXT};")
        info_layout.addWidget(self.lbl_project_name)

        self.lbl_customer = QLabel()
        self.lbl_customer.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
        info_layout.addWidget(self.lbl_customer)

        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% Tamamlandı")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.SUCCESS};
            }}
        """)
        info_layout.addWidget(self.progress_bar)

        self.lbl_stats = QLabel()
        self.lbl_stats.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_SECONDARY};")
        info_layout.addWidget(self.lbl_stats)

        layout.addWidget(info_frame)

        # Siparişler listesi
        orders_label = QLabel("Projeye Ait Siparişler")
        orders_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(orders_label)

        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "Sipariş Kodu", "Ürün", "Kalınlık", "Adet", "m²", "Durum"
        ])

        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                gridline-color: {Colors.GRID};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:alternate {{
                background-color: {Colors.ROW_ALT};
            }}
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)

        layout.addWidget(self.orders_table)

        # Kapat butonu
        btn_close = QPushButton("Kapat")
        btn_close.setFixedHeight(36)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(f"""
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
        layout.addWidget(btn_close)

    def load_project_info(self):
        """Proje bilgilerini yükle"""
        if not db or not self.project_id:
            return

        # Proje bilgileri
        project = db.get_project_by_id(self.project_id)
        if not project:
            return

        self.lbl_project_name.setText(project['project_name'])
        self.lbl_customer.setText(f"Müşteri: {project.get('customer_name', '-')} | Teslimat: {project.get('delivery_date', '-')}")

        # İlerleme
        summary = db.get_project_summary(self.project_id)
        if summary:
            progress_percent = summary.get('progress_percent') or 0
            completed_orders = summary.get('completed_orders') or 0
            total_orders = summary.get('total_orders') or 0
            completed_m2 = summary.get('completed_m2') or 0
            total_m2 = summary.get('total_m2') or 0

            self.progress_bar.setValue(progress_percent)
            self.lbl_stats.setText(
                f"{completed_orders}/{total_orders} sipariş tamamlandı | "
                f"{completed_m2:.1f}/{total_m2:.1f} m²"
            )
        else:
            self.progress_bar.setValue(0)
            self.lbl_stats.setText("Henüz sipariş eklenmemiş")

        # Siparişler
        orders = db.get_project_orders(self.project_id)
        self.orders_table.setRowCount(len(orders))

        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(order['order_code']))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.get('product_type', '-')))
            self.orders_table.setItem(row, 2, QTableWidgetItem(f"{order.get('thickness', 0)}mm"))
            self.orders_table.setItem(row, 3, QTableWidgetItem(str(order.get('quantity', 0))))
            self.orders_table.setItem(row, 4, QTableWidgetItem(f"{order.get('declared_total_m2', 0):.1f}"))

            status_item = QTableWidgetItem(order.get('status', '-'))
            if order.get('status') == 'Tamamlandı':
                status_item.setForeground(QColor(Colors.SUCCESS))
            elif order.get('status') == 'Üretimde':
                status_item.setForeground(QColor(Colors.INFO))
            else:
                status_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self.orders_table.setItem(row, 5, status_item)
