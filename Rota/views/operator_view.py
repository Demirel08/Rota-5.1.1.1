import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QFrame, QMessageBox, QLineEdit, 
                               QAbstractItemView, QInputDialog, QComboBox)
from PySide6.QtCore import Qt, QTimer, QTime, Signal
from PySide6.QtGui import QFont, QColor, QIcon

try:
    from core.db_manager import db
    from ui.theme import Theme
except ImportError:
    pass

class OperatorView(QWidget):
    logout_signal = Signal() 

    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.current_order = None 
        self.barcode_buffer = ""
        
        self.setup_ui()
        self.setup_timer() 
        self.refresh_list() 
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            if self.barcode_buffer:
                self.process_scanned_barcode(self.barcode_buffer)
                self.barcode_buffer = ""
        else:
            if text.isalnum() or text in ["-", "_"]: 
                self.barcode_buffer += text
        super().keyPressEvent(event)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- ÜST BAR ---
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {Theme.TEXT_DARK}; border-bottom: 1px solid #000;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        # --- İSTASYON SEÇİCİ ---
        user_station = self.user.get('station_name')
        
        self.combo_station = QComboBox()
        self.combo_station.addItems(["KESİM", "RODAJ", "DELİK", "TEMPER", "LAMİNE", "ISICAM", "KUMLAMA", "SEVKİYAT"])
        self.combo_station.setFixedWidth(150)
        self.combo_station.setStyleSheet("font-weight: bold; padding: 5px;")
        
        if user_station and user_station in ["KESİM", "RODAJ", "DELİK", "TEMPER", "LAMİNE", "ISICAM", "KUMLAMA", "SEVKİYAT"]:
            self.combo_station.setCurrentText(user_station)
        
        lbl_station_title = QLabel("İSTASYON:")
        lbl_station_title.setStyleSheet("color: white; font-weight: bold;")
        
        header_layout.addWidget(lbl_station_title)
        header_layout.addWidget(self.combo_station)

        header_layout.addStretch()

        self.lbl_clock = QLabel("00:00:00")
        self.lbl_clock.setStyleSheet("color: #BDC3C7; font-size: 24px; font-family: 'Consolas'; font-weight: bold;")
        header_layout.addWidget(self.lbl_clock)

        lbl_user = QLabel(f"👤 {self.user.get('full_name', 'Operatör')}")
        lbl_user.setStyleSheet("color: white; font-size: 14px; font-weight: 600; margin-left: 20px;")
        header_layout.addWidget(lbl_user)
        
        btn_exit = QPushButton("ÇIKIŞ")
        btn_exit.setCursor(Qt.PointingHandCursor)
        btn_exit.clicked.connect(self.handle_logout)
        btn_exit.setFixedSize(80, 35)
        btn_exit.setStyleSheet("QPushButton { background-color: #c0392b; color: white; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #e74c3c; }")
        header_layout.addWidget(btn_exit)

        main_layout.addWidget(header)

        # --- İÇERİK ---
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # SOL PANEL
        left_panel = QVBoxLayout()
        lbl_queue = QLabel("BEKLEYEN İŞLER")
        lbl_queue.setStyleSheet(f"color: {Theme.TEXT_DARK}; font-size: 16px; font-weight: 700; margin-bottom: 5px;")
        left_panel.addWidget(lbl_queue)

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("Barkod Okutun veya Elle Girin...")
        self.txt_barcode.setFixedHeight(50)
        self.txt_barcode.setStyleSheet("QLineEdit { border: 2px solid #3498DB; border-radius: 8px; padding: 0 15px; font-size: 16px; background-color: #FDFEFE; } QLineEdit:focus { background-color: #FFFFFF; border-color: #2980B9; }")
        self.txt_barcode.returnPressed.connect(self.handle_manual_barcode)
        left_panel.addWidget(self.txt_barcode)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["SİPARİŞ", "CAM TİPİ", "ÖLÇÜ (cm)", "ADET"])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60) 
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Stretch)
        header_view.setStyleSheet("QHeaderView::section { background-color: #ECF0F1; padding: 10px; font-weight: bold; border: none; }")
        
        self.table.setStyleSheet(f"QTableWidget {{ border: 1px solid #BDC3C7; font-size: 16px; }} QTableWidget::item {{ padding-left: 15px; }} QTableWidget::item:selected {{ background-color: {Theme.TEXT_DARK}; color: white; }}")
        self.table.itemSelectionChanged.connect(self.load_selected_job)
        left_panel.addWidget(self.table)

        btn_refresh = QPushButton("LİSTEYİ YENİLE")
        btn_refresh.setFixedHeight(50)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_list)
        btn_refresh.setStyleSheet(f"QPushButton {{ background-color: white; border: 2px solid {Theme.TEXT_DARK}; font-weight: bold; font-size: 14px; color: {Theme.TEXT_DARK}; }} QPushButton:hover {{ background-color: #F0F0F0; }}")
        left_panel.addWidget(btn_refresh)

        # SAĞ PANEL
        right_panel = QVBoxLayout()
        
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #BDC3C7; border-radius: 0px;")
        self.info_card.setMinimumWidth(400)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(30, 30, 30, 30)
        
        self.lbl_job_code = QLabel("İŞ SEÇİNİZ")
        self.lbl_job_code.setAlignment(Qt.AlignCenter)
        self.lbl_job_code.setStyleSheet(f"font-size: 36px; font-weight: 900; color: {Theme.TEXT_DARK};")
        info_layout.addWidget(self.lbl_job_code)
        
        self.lbl_job_desc = QLabel("---")
        self.lbl_job_desc.setAlignment(Qt.AlignCenter)
        self.lbl_job_desc.setStyleSheet("font-size: 22px; color: #7F8C8D; margin-top: 10px;")
        info_layout.addWidget(self.lbl_job_desc)
        
        self.lbl_job_dims = QLabel("---")
        self.lbl_job_dims.setAlignment(Qt.AlignCenter)
        self.lbl_job_dims.setStyleSheet("font-size: 28px; font-weight: bold; color: #333; margin-top: 20px;")
        info_layout.addWidget(self.lbl_job_dims)
        
        info_layout.addStretch()
        self.lbl_status = QLabel("DURUM: BEKLİYOR")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("background-color: #ECF0F1; color: #7F8C8D; font-size: 16px; font-weight: bold; padding: 10px;")
        info_layout.addWidget(self.lbl_status)
        right_panel.addWidget(self.info_card)

        action_layout = QVBoxLayout()
        action_layout.setSpacing(15)
        
        self.btn_start = QPushButton("▶  İŞİ BAŞLAT")
        self.btn_start.setFixedHeight(80)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_job)
        self.btn_start.setStyleSheet(f"QPushButton {{ background-color: {Theme.TEXT_DARK}; color: white; font-size: 24px; font-weight: bold; border: none; }} QPushButton:disabled {{ background-color: #BDC3C7; color: #ECF0F1; }}")
        action_layout.addWidget(self.btn_start)
        
        self.btn_finish = QPushButton("✔  TAMAMLA")
        self.btn_finish.setFixedHeight(80)
        self.btn_finish.setCursor(Qt.PointingHandCursor)
        self.btn_finish.setEnabled(False)
        self.btn_finish.clicked.connect(self.finish_job)
        self.btn_finish.setStyleSheet(f"QPushButton {{ background-color: {Theme.SUCCESS}; color: white; font-size: 24px; font-weight: bold; border: none; }} QPushButton:disabled {{ background-color: #BDC3C7; color: #ECF0F1; }} QPushButton:hover {{ background-color: #4CA66E; }}")
        action_layout.addWidget(self.btn_finish)
        
        self.btn_fire = QPushButton("🔥  FİRE / KIRIK BİLDİR")
        self.btn_fire.setFixedHeight(50)
        self.btn_fire.setCursor(Qt.PointingHandCursor)
        self.btn_fire.setEnabled(False)
        self.btn_fire.clicked.connect(self.report_breakage)
        self.btn_fire.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {Theme.DANGER}; font-size: 16px; font-weight: bold; border: 2px solid {Theme.DANGER}; }} QPushButton:hover {{ background-color: {Theme.DANGER}; color: white; }} QPushButton:disabled {{ border-color: #BDC3C7; color: #BDC3C7; }}")
        action_layout.addWidget(self.btn_fire)

        right_panel.addLayout(action_layout)
        content_layout.addLayout(left_panel, 60)
        content_layout.addLayout(right_panel, 40)
        main_layout.addWidget(content_widget)
        self.txt_barcode.setFocus()

    def handle_manual_barcode(self):
        code = self.txt_barcode.text().strip()
        if code:
            self.process_scanned_barcode(code)
            self.txt_barcode.clear()

    def process_scanned_barcode(self, code):
        found = False
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == code:
                self.table.selectRow(row)
                self.load_selected_job()
                found = True
                break
        if not found:
            QMessageBox.warning(self, "Bulunamadı", f"'{code}' kodlu sipariş bu istasyonun listesinde yok!")

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def update_clock(self):
        self.lbl_clock.setText(QTime.currentTime().toString("HH:mm:ss"))

    def refresh_list(self):
        self.table.setRowCount(0)
        self.current_order = None
        self.reset_controls()
        orders = db.get_orders_by_status(["Beklemede", "Üretimde"])
        self.table.setRowCount(len(orders))
        for row, data in enumerate(orders):
            item_code = QTableWidgetItem(str(data['order_code']))
            item_desc = QTableWidgetItem(f"{data['thickness']}mm {data['product_type']}")
            item_dims = QTableWidgetItem(f"{data['width']} x {data['height']}")
            item_qty = QTableWidgetItem(str(data['quantity']))
            
            priority = data.get('priority', 'Normal')
            bg_color = QColor("white")
            text_color = QColor("black")
            
            if priority == "Kritik":
                bg_color = QColor("#C0392B")
                text_color = QColor("white")
                item_code.setText(f"🚨 {data['order_code']}")
            elif priority == "Acil":
                bg_color = QColor("#F39C12")
                text_color = QColor("white")
                item_code.setText(f"⚡ {data['order_code']}")
            
            for item in [item_code, item_desc, item_dims, item_qty]:
                item.setBackground(bg_color)
                item.setForeground(text_color)
                item.setFont(QFont("Segoe UI", 12, QFont.Bold if priority != "Normal" else QFont.Normal))

            self.table.setItem(row, 0, item_code)
            self.table.setItem(row, 1, item_desc)
            self.table.setItem(row, 2, item_dims)
            self.table.setItem(row, 3, item_qty)
            self.table.item(row, 0).setData(Qt.UserRole, data)

    def load_selected_job(self):
        selected = self.table.selectedItems()
        if not selected: return
        data = selected[0].data(Qt.UserRole)
        self.current_order = data
        
        self.lbl_job_code.setText(data['order_code'])
        self.lbl_job_desc.setText(f"{data['customer_name']}\n{data['thickness']}mm {data['product_type']}")
        self.lbl_job_dims.setText(f"{data['width']} x {data['height']} cm  |  {data['quantity']} Adet")
        
        status = data['status']
        self.btn_fire.setEnabled(True)
        if status == 'Beklemede':
            self.lbl_status.setText("DURUM: BAŞLAMAYA HAZIR")
            self.lbl_status.setStyleSheet("background-color: #F39C12; color: white; font-weight: bold; padding: 10px;")
            self.btn_start.setEnabled(True)
            self.btn_finish.setEnabled(False)
        elif status == 'Üretimde':
            self.lbl_status.setText("DURUM: İŞLENİYOR...")
            self.lbl_status.setStyleSheet("background-color: #3498DB; color: white; font-weight: bold; padding: 10px;")
            self.btn_start.setEnabled(False)
            self.btn_finish.setEnabled(True)

    def start_job(self):
        if not self.current_order: return
        db.update_order_status(self.current_order['id'], "Üretimde")
        self.refresh_list()

    def finish_job(self):
        if not self.current_order: return
        
        # --- SEÇİLİ OLAN İSTASYONU AL ---
        selected_station = self.combo_station.currentText()
        
        reply = QMessageBox.question(self, "Onay", f"Bu iş {selected_station} istasyonunda tamamlandı mı?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.complete_station_process(self.current_order['id'], selected_station)
            QMessageBox.information(self, "Başarılı", f"{selected_station} işlemi kaydedildi.")
            self.refresh_list()

    def report_breakage(self):
        if not self.current_order: return
        
        # --- DÜZELTME: İSTASYON VE OPERATÖR BİLGİSİNİ ALIP GÖNDERİYORUZ ---
        current_station = self.combo_station.currentText()
        operator_name = self.user.get('full_name', 'Operatör')
        
        qty, ok = QInputDialog.getInt(self, "Fire Girişi", "Kaç adet cam kırıldı?", 1, 1, self.current_order['quantity'])
        if ok:
            # Artık istasyon adını ve operatörü de gönderiyoruz
            db.report_fire(self.current_order['id'], qty, current_station, operator_name)
            
            QMessageBox.critical(self, "FİRE KAYDEDİLDİ", f"{qty} adet cam için fire kaydı oluşturuldu.\nOtomatik rework siparişi açıldı.")
            self.refresh_list()

    def reset_controls(self):
        self.lbl_job_code.setText("İŞ SEÇİNİZ")
        self.lbl_job_desc.setText("---")
        self.lbl_job_dims.setText("---")
        self.lbl_status.setText("---")
        self.lbl_status.setStyleSheet("background-color: #ECF0F1; color: #7F8C8D; padding: 10px;")
        self.btn_start.setEnabled(False)
        self.btn_finish.setEnabled(False)
        self.btn_fire.setEnabled(False)

    def handle_logout(self):
        self.logout_signal.emit()