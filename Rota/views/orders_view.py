"""
EFES ROTA X - Siparis Listesi
Excel temali, Anlik Konum sutunu ile
"""

import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLineEdit, QAbstractItemView,
    QMessageBox, QApplication, QProgressBar, QToolTip,
    QDialog, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QBrush

try:
    from core.db_manager import db
except ImportError:
    db = None

try:
    from views.add_order_dialog import AddOrderDialog
except ImportError:
    AddOrderDialog = None

try:
    from views.label_dialog import LabelDialog
except ImportError:
    LabelDialog = None

try:
    from views.order_detail_dialog import OrderDetailDialog
except ImportError:
    OrderDetailDialog = None


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
    CRITICAL_BG = "#FDE8E8"
    WARNING = "#C65911"
    WARNING_BG = "#FFF3E0"
    SUCCESS = "#107C41"
    SUCCESS_BG = "#E6F4EA"
    INFO = "#0066CC"
    INFO_BG = "#E3F2FD"


# =============================================================================
# FABRIKA AYARLARI
# =============================================================================
class FactoryConfig:
    """Istasyon sirasi"""
    
    STATION_ORDER = [
        "INTERMAC", "LIVA KESIM", "LAMINE KESIM",
        "CNC RODAJ", "DOUBLEDGER", "ZIMPARA",
        "TESIR A1", "TESIR B1", "TESIR B1-1", "TESIR B1-2", "DELIK", "OYGU",
        "TEMPER A1", "TEMPER B1", "TEMPER BOMBE",
        "LAMINE A1", "ISICAM B1", "KUMLAMA",
        "SEVKIYAT"
    ]
    
    @classmethod
    def get_station_index(cls, station_name):
        try:
            return cls.STATION_ORDER.index(station_name)
        except ValueError:
            return 999


# =============================================================================
# ANA WIDGET
# =============================================================================
class OrdersView(QWidget):
    def __init__(self):
        super().__init__()
        self.all_orders = []
        self.setup_ui()
        
        # Canli yenileme (3 saniye)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data_silent)
        self.timer.start(3000)
        
        self.selected_code = ""  # Secili siparis kodu
        self.refresh_data()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BG};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # === HEADER ===
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(12)
        
        # Baslik
        title = QLabel("Siparisler")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {Colors.TEXT};
        """)
        header_layout.addWidget(title)
        
        # Siparis sayisi
        self.lbl_count = QLabel("0 siparis")
        self.lbl_count.setStyleSheet(f"""
            font-size: 11px;
            color: {Colors.TEXT_MUTED};
            padding: 4px 8px;
            background-color: {Colors.BG};
            border: 1px solid {Colors.BORDER};
            border-radius: 3px;
        """)
        header_layout.addWidget(self.lbl_count)
        
        header_layout.addStretch()
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (kod, musteri)")
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_table)
        header_layout.addWidget(self.search_input)
        
        # Not Duzenle butonu
        btn_notes = QPushButton("📝 Not Duzenle")
        btn_notes.setFixedHeight(30)
        btn_notes.setCursor(Qt.PointingHandCursor)
        btn_notes.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 0 12px;
                font-size: 11px;
                color: {Colors.TEXT};
            }}
            QPushButton:hover {{
                background-color: {Colors.HEADER_BG};
            }}
        """)
        btn_notes.clicked.connect(self.edit_order_note)
        header_layout.addWidget(btn_notes)

        # Etiket butonu
        btn_label = QPushButton("Etiket Bas")
        btn_label.setFixedHeight(30)
        btn_label.setCursor(Qt.PointingHandCursor)
        btn_label.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 0 12px;
                font-size: 11px;
                color: {Colors.TEXT};
            }}
            QPushButton:hover {{
                background-color: {Colors.HEADER_BG};
            }}
        """)
        btn_label.clicked.connect(self.open_label_printer)
        header_layout.addWidget(btn_label)
        
        # Yeni siparis butonu
        btn_add = QPushButton("+ Yeni Siparis")
        btn_add.setFixedHeight(30)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 3px;
                padding: 0 16px;
                font-size: 11px;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_add.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(btn_add)
        
        layout.addWidget(header)
        
        # === TABLO ===
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Siparis Kodu", "Musteri", "Urun", "Adet", "Durum", "Anlik Konum", "Teslim", "📝"
        ])
        self.table.cellClicked.connect(self.on_cell_clicked)
        
        # Tablo ayarlari
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        
        # Cift tiklama
        self.table.doubleClicked.connect(self.open_order_detail)
        
        # Sutun genislikleri
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)  # Musteri genislesin
        header_view.setSectionResizeMode(5, QHeaderView.Stretch)  # Anlik Konum genislesin
        
        self.table.setColumnWidth(0, 120)  # Kod
        self.table.setColumnWidth(2, 120)  # Urun
        self.table.setColumnWidth(3, 60)   # Adet
        self.table.setColumnWidth(4, 90)   # Durum
        self.table.setColumnWidth(6, 90)   # Teslim
        
        # Tablo stili
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG};
                alternate-background-color: {Colors.ROW_ALT};
                border: none;
                gridline-color: {Colors.GRID};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {Colors.GRID};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.SELECTION};
                color: {Colors.TEXT};
            }}
            QHeaderView::section {{
                background-color: {Colors.HEADER_BG};
                color: {Colors.TEXT};
                font-weight: bold;
                font-size: 11px;
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid {Colors.BORDER};
                border-right: 1px solid {Colors.GRID};
            }}
        """)
        
        layout.addWidget(self.table)
        
        # === ALT BAR ===
        footer = QFrame()
        footer.setFixedHeight(36)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.HEADER_BG};
                border-top: 1px solid {Colors.BORDER};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 0, 16, 0)
        
        # Durum ozeti
        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_SECONDARY};")
        footer_layout.addWidget(self.lbl_summary)
        
        footer_layout.addStretch()
        
        # Yenile butonu
        btn_refresh = QPushButton("Yenile")
        btn_refresh.setFixedSize(70, 24)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                font-size: 10px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background-color: {Colors.BG};
            }}
        """)
        btn_refresh.clicked.connect(self.refresh_data)
        footer_layout.addWidget(btn_refresh)
        
        layout.addWidget(footer)

    # =========================================================================
    # ANLIK KONUM HESAPLAMA
    # =========================================================================
    def get_current_location(self, order):
        """Siparişin anlık konumunu hesapla"""
        order_id = order.get('id')
        route = order.get('route', '')
        quantity = order.get('quantity', 0)
        status = order.get('status', '')
        
        if not route or not db:
            return {"text": "-", "icon": "○", "color": Colors.TEXT_MUTED, "progress": 0}
        
        # Sevk edilmis
        if status == "Sevk Edildi":
            return {"text": "Sevk edildi", "icon": "✓", "color": Colors.SUCCESS, "progress": 100}
        
        # Tamamlanmis
        if status == "Tamamlandı":
            return {"text": "Sevke hazır", "icon": "●", "color": Colors.SUCCESS, "progress": 100}
        
        # Fire/Hatali
        if "Hata" in status or "Fire" in status:
            return {"text": "Fire/Hatalı", "icon": "✗", "color": Colors.CRITICAL, "progress": 0}
        
        # Rota istasyonlari
        route_stations = [s.strip() for s in route.split(',') if s.strip()]
        
        # Her istasyonun durumunu kontrol et
        current_station = None
        current_done = 0
        waiting_station = None
        total_stations = len(route_stations)
        completed_count = 0
        
        for station in route_stations:
            if station in ["SEVKIYAT", "SEVKİYAT"]:
                continue
            
            done = db.get_station_progress(order_id, station)
            
            if done >= quantity:
                # Bu istasyon tamamlandi
                completed_count += 1
            elif done > 0:
                # Bu istasyonda uretim var ama bitmemis (KISMI)
                current_station = station
                current_done = done
                break
            else:
                # Henuz baslanmamis - ilk beklenen istasyon
                if waiting_station is None:
                    waiting_station = station
                break
        
        # Sonuc
        if current_station:
            # Uretimde - kismi tamamlanmis
            progress = int((current_done / quantity) * 100) if quantity > 0 else 0
            return {
                "text": f"{current_station} ({current_done}/{quantity})",
                "icon": "◐",
                "color": Colors.INFO,
                "progress": progress,
                "station": current_station,
                "done": current_done,
                "total": quantity
            }
        elif waiting_station:
            # Bekliyor
            return {
                "text": f"{waiting_station} bekliyor",
                "icon": "○",
                "color": Colors.WARNING,
                "progress": 0,
                "station": waiting_station
            }
        else:
            # Tum istasyonlar tamamlanmis
            return {
                "text": "Tamamlandı",
                "icon": "●",
                "color": Colors.SUCCESS,
                "progress": 100
            }

    # =========================================================================
    # VERI ISLEMLERI
    # =========================================================================
    def refresh_data(self):
        """Verileri yenile"""
        if not db:
            return
        
        v_scroll = self.table.verticalScrollBar().value()
        
        try:
            # Her seferinde taze veri cek
            self.all_orders = db.get_all_orders()
            
            # Siparis durumlarini guncelle (uretim girisi yapilmissa)
            for order in self.all_orders:
                order_id = order.get('id')
                if order_id and order.get('status') not in ['Sevk Edildi', 'Hatalı/Fire']:
                    # Anlık durumu kontrol et
                    location = self.get_current_location(order)
                    # Eger tum istasyonlar bitmisse ve durum "Tamamlandı" degilse guncelle
                    if location.get('progress') == 100 and location.get('text') == 'Tamamlandı':
                        if order.get('status') != 'Tamamlandı':
                            try:
                                db.update_order_status(order_id, 'Tamamlandı')
                                order['status'] = 'Tamamlandı'
                            except:
                                pass
                    # Eger uretim baslamissa ve durum "Beklemede" ise "Uretimde" yap
                    elif location.get('progress', 0) > 0 or '(' in location.get('text', ''):
                        if order.get('status') == 'Beklemede':
                            try:
                                db.update_order_status(order_id, 'Üretimde')
                                order['status'] = 'Üretimde'
                            except:
                                pass
        except Exception as e:
            print(f"Veri cekme hatasi: {e}")
            self.all_orders = []
        
        self.populate_table(self.all_orders)
        self.update_summary()
        
        self.table.verticalScrollBar().setValue(v_scroll)

    def refresh_data_silent(self):
        """Sessiz yenileme - secimi ve scroll'u koruyarak"""
        # Mevcut secimi kaydet
        selected_row = -1
        selected_items = self.table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            # Secili satirın kodunu kaydet (satir numarasi degisebilir)
            code_item = self.table.item(selected_row, 0)
            if code_item:
                self.selected_code = code_item.text().replace("⚠ ", "").replace("⚡ ", "").strip()
        
        # Veriyi yenile
        self.refresh_data()
        
        # Eger arama aktifse filtreyi tekrar uygula
        if self.search_input.text():
            self.filter_table(self.search_input.text())
        
        # Secimi geri yukle (kod ile esleseni bul)
        if hasattr(self, 'selected_code') and self.selected_code:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    code = item.text().replace("⚠ ", "").replace("⚡ ", "").strip()
                    if code == self.selected_code:
                        self.table.selectRow(row)
                        break

    def populate_table(self, orders):
        """Tabloyu doldur"""
        self.table.setRowCount(len(orders))
        self.lbl_count.setText(f"{len(orders)} siparis")
        
        for row, order in enumerate(orders):
            self.populate_row(row, order)

    def populate_row(self, row, order):
        """Tek satir doldur"""
        priority = order.get('priority', 'Normal')
        status = order.get('status', 'Beklemede')
        
        # Renk ve stil
        text_color = Colors.TEXT
        bg_color = Colors.BG if row % 2 == 0 else Colors.ROW_ALT
        is_bold = False
        prefix = ""
        
        if status == "Sevk Edildi":
            text_color = Colors.TEXT_MUTED
        elif priority == "Kritik":
            prefix = "⚠ "
            text_color = Colors.CRITICAL
            is_bold = True
        elif priority == "Acil":
            prefix = "⚡ "
            text_color = Colors.WARNING
            is_bold = True
        
        # 1. Siparis Kodu
        code_text = prefix + str(order.get('order_code', ''))
        item_code = QTableWidgetItem(code_text)
        item_code.setForeground(QColor(text_color))
        if is_bold:
            font = item_code.font()
            font.setBold(True)
            item_code.setFont(font)
        self.table.setItem(row, 0, item_code)
        
        # 2. Musteri
        item_customer = QTableWidgetItem(str(order.get('customer_name', '')))
        item_customer.setForeground(QColor(text_color))
        self.table.setItem(row, 1, item_customer)
        
        # 3. Urun
        product = f"{order.get('thickness', '')}mm {order.get('product_type', '')}"
        item_product = QTableWidgetItem(product)
        item_product.setForeground(QColor(Colors.TEXT_SECONDARY))
        self.table.setItem(row, 2, item_product)
        
        # 4. Adet
        item_qty = QTableWidgetItem(str(order.get('quantity', 0)))
        item_qty.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, item_qty)
        
        # 5. Durum
        item_status = QTableWidgetItem(status)
        item_status.setTextAlignment(Qt.AlignCenter)
        
        status_color = Colors.TEXT_MUTED
        if "Beklemede" in status:
            status_color = Colors.WARNING
        elif "Üretimde" in status:
            status_color = Colors.INFO
        elif "Tamamlandı" in status:
            status_color = Colors.SUCCESS
        elif "Sevk" in status:
            status_color = Colors.TEXT_MUTED
        elif "Hata" in status or "Fire" in status:
            status_color = Colors.CRITICAL
        
        item_status.setForeground(QColor(status_color))
        font = item_status.font()
        font.setBold(True)
        item_status.setFont(font)
        self.table.setItem(row, 4, item_status)
        
        # 6. Anlik Konum
        location = self.get_current_location(order)
        location_text = f"{location['icon']} {location['text']}"
        item_location = QTableWidgetItem(location_text)
        item_location.setForeground(QColor(location['color']))
        self.table.setItem(row, 5, item_location)
        
        # 7. Teslim Tarihi
        delivery = order.get('delivery_date', '')
        item_date = QTableWidgetItem(str(delivery) if delivery else "-")
        item_date.setTextAlignment(Qt.AlignCenter)
        item_date.setForeground(QColor(Colors.TEXT_SECONDARY))
        self.table.setItem(row, 6, item_date)

        # 8. Not ikonu
        notes = order.get('notes', '').strip()
        if notes:
            item_note = QTableWidgetItem("📝")
            item_note.setTextAlignment(Qt.AlignCenter)
            item_note.setToolTip(notes)
            item_note.setForeground(QColor(Colors.ACCENT))
            font_note = item_note.font()
            font_note.setPointSize(14)
            item_note.setFont(font_note)
            # Not verisi olduğunu belirtmek için data ekle
            item_note.setData(Qt.UserRole, notes)
        else:
            item_note = QTableWidgetItem("")
            item_note.setData(Qt.UserRole, "")
        self.table.setItem(row, 7, item_note)

    def update_summary(self):
        """Alt bar ozetini guncelle"""
        if not self.all_orders:
            self.lbl_summary.setText("")
            return
        
        beklemede = sum(1 for o in self.all_orders if o.get('status') == 'Beklemede')
        uretimde = sum(1 for o in self.all_orders if o.get('status') == 'Üretimde')
        tamamlandi = sum(1 for o in self.all_orders if o.get('status') == 'Tamamlandı')
        
        self.lbl_summary.setText(
            f"Beklemede: {beklemede}  |  Uretimde: {uretimde}  |  Tamamlandi: {tamamlandi}"
        )

    def filter_table(self, text):
        """Tablo filtrele"""
        for i in range(self.table.rowCount()):
            match = False
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def on_cell_clicked(self, row, column):
        """Hücreye tıklandığında - Not sütununa tıklanırsa mesaj kutusu göster"""
        if column == 7:  # Not sütunu
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
    # DIALOG ISLEMLERI
    # =========================================================================
    def open_add_dialog(self):
        """Yeni siparis dialogu"""
        if AddOrderDialog is None:
            QMessageBox.warning(self, "Hata", "Siparis ekleme modulu yuklenemedi.")
            return
        
        try:
            dialog = AddOrderDialog(self)
            if dialog.exec():
                self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dialog hatasi:\n{str(e)}")

    def open_label_printer(self):
        """Etiket basma dialogu"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Secim Yok", "Lutfen etiket basilacak siparisi secin!")
            return
        
        if LabelDialog is None:
            QMessageBox.warning(self, "Hata", "Etiket modulu yuklenemedi.")
            return
        
        row = selected[0].row()
        raw_code = self.table.item(row, 0).text()
        code = raw_code.replace("⚠ ", "").replace("⚡ ", "").strip()
        
        # Siparisi bul
        target_order = None
        for o in self.all_orders:
            if o.get('order_code') == code:
                target_order = o
                break
        
        if target_order:
            try:
                dialog = LabelDialog({
                    "code": target_order.get('order_code', ''),
                    "customer": target_order.get('customer_name', ''),
                    "product": target_order.get('product_type', ''),
                    "thickness": target_order.get('thickness', ''),
                    "width": target_order.get('width', 0),
                    "height": target_order.get('height', 0),
                    "date": target_order.get('delivery_date', ''),
                    "route": target_order.get('route', '')
                })
                dialog.exec()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Etiket hatasi:\n{str(e)}")

    def open_order_detail(self):
        """Siparis detay dialogu"""
        selected = self.table.selectedItems()
        if not selected:
            return
        
        if OrderDetailDialog is None:
            QMessageBox.warning(self, "Hata", "Siparis detay modulu yuklenemedi.")
            return
        
        row = selected[0].row()
        raw_code = self.table.item(row, 0).text()
        code = raw_code.replace("⚠ ", "").replace("⚡ ", "").strip()
        
        try:
            dialog = OrderDetailDialog(code)
            dialog.exec()
            self.refresh_data()  # Detaydan cikinca yenile
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Detay hatasi:\n{str(e)}")

    def edit_order_note(self):
        """Secili siparisin notunu duzenle"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Secim Yok", "Lutfen not eklenecek/duzenlenecek siparisi secin!")
            return

        row = selected[0].row()
        raw_code = self.table.item(row, 0).text()
        code = raw_code.replace("⚠ ", "").replace("⚡ ", "").strip()

        # Siparisi bul
        target_order = None
        for o in self.all_orders:
            if o.get('order_code') == code:
                target_order = o
                break

        if not target_order:
            QMessageBox.warning(self, "Hata", "Siparis bulunamadi!")
            return

        # Not duzenleme dialogu
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Not Duzenle - {code}")
        dialog.setMinimumSize(500, 300)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel(f"Siparis: {code} - {target_order.get('customer_name', '')}")
        lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {Colors.TEXT};")
        layout.addWidget(lbl)

        txt_note = QTextEdit()
        txt_note.setPlainText(target_order.get('notes', ''))
        txt_note.setPlaceholderText("Bu siparise ait notlar, uyarilar veya hatirlatmalar...")
        txt_note.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                padding: 8px;
                font-size: 11px;
                color: {Colors.TEXT};
            }}
            QTextEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        layout.addWidget(txt_note)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Iptal")
        btn_cancel.setFixedSize(100, 32)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 3px;
                color: {Colors.TEXT};
            }}
            QPushButton:hover {{
                background-color: {Colors.HEADER_BG};
            }}
        """)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Kaydet")
        btn_save.setFixedSize(100, 32)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 3px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1D6640;
            }}
        """)
        btn_save.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

        if dialog.exec():
            # Notu kaydet
            new_note = txt_note.toPlainText().strip()
            if db:
                try:
                    with db.get_connection() as conn:
                        conn.execute(
                            "UPDATE orders SET notes = ? WHERE order_code = ?",
                            (new_note, code)
                        )
                    QMessageBox.information(self, "Basarili", f"Not kaydedildi.")
                    self.refresh_data()
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Not kaydedilemedi:\n{str(e)}")


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 9))
    
    window = OrdersView()
    window.setWindowTitle("EFES ROTA X - Siparisler")
    window.resize(1100, 600)
    window.show()
    
    sys.exit(app.exec())