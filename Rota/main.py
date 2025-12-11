import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtGui import QFont, QIcon

# Kendi modüllerimiz
try:
    from ui.theme import Theme
    from views.login_view import LoginView
    from views.dashboard_view import DashboardView
    from views.operator_view import OperatorView
    from views.daily_summary_dialog import DailySummaryDialog

    # === YENİ IMPORT'LAR ===
    from core.db_manager import db
    from core.factory_config import factory_config
    from core.logger import logger

except ImportError as e:
    print(f"UYARI: Modul yukleme hatasi: {e}")

class EfesRotaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # === YENİ: Factory Config'i Veritabanına Bağla ===
        try:
            factory_config.set_database(db)
            logger.info("Factory config veritabanına bağlandı")
        except Exception as e:
            print(f"Factory config hatası: {e}")
        
        # Pencere Ayarları
        self.setWindowTitle("REFLEKS 360 ROTA - Üretim Yönetim Sistemi")
        self.resize(1280, 800) 
        self.setMinimumSize(1024, 768)
        
        # Ana Stack (Sayfalar arası geçiş yöneticisi)
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        
        # Başlangıçta Login Ekranını Yükle
        self.show_login()

    def show_login(self):
        """Login ekranını göster"""
        # Eğer daha önce açılmış ekran varsa temizle
        if self.central_stack.count() > 0:
            widget = self.central_stack.widget(0)
            self.central_stack.removeWidget(widget)
            widget.deleteLater()

        self.login_view = LoginView()
        self.login_view.login_successful.connect(self.handle_login_success)
        self.central_stack.addWidget(self.login_view)
        self.central_stack.setCurrentWidget(self.login_view)

    def handle_login_success(self, user_data):
        """Giriş başarılı olduğunda çalışır"""
        
        username = user_data.get('username', 'Kullanıcı')
        role = user_data.get('role', 'admin')
        
        # === YENİ: Giriş logla ===
        logger.user_login(username, role, success=True)
        
        print(f">> Sisteme giris yapildi: {username} ({role})")
        
        if role == 'admin' or role == 'planlama':
            self.show_admin_dashboard(user_data)
        elif role == 'operator':
            self.show_operator_panel(user_data)
        else:
            print(f"UYARI: Bilinmeyen rol '{role}', Admin paneli aciliyor...")
            self.show_admin_dashboard(user_data)

    def show_admin_dashboard(self, user_data):
        """Patron ekranını yükle"""
        try:
            self.dashboard = DashboardView(user_data)
            self.dashboard.logout_signal.connect(self.show_login)

            self.central_stack.addWidget(self.dashboard)
            self.central_stack.setCurrentWidget(self.dashboard)

            # Günlük özet popup'ını göster
            try:
                summary_dialog = DailySummaryDialog(db, self)
                summary_dialog.exec()
            except Exception as summary_error:
                logger.error(f"Günlük özet gösterilirken hata: {summary_error}", exc_info=True)

        except Exception as e:
            logger.error(f"Dashboard açılırken hata: {e}", exc_info=True)
            QMessageBox.critical(self, "Hata", f"Ana ekran yüklenemedi:\n{str(e)}")

    def show_operator_panel(self, user_data):
        """Operatör ekranını yükle"""
        try:
            self.operator_view = OperatorView(user_data)
            self.operator_view.logout_signal.connect(self.show_login)

            self.central_stack.addWidget(self.operator_view)
            self.central_stack.setCurrentWidget(self.operator_view)

            # Günlük özet popup'ını göster
            try:
                summary_dialog = DailySummaryDialog(db, self)
                summary_dialog.exec()
            except Exception as summary_error:
                logger.error(f"Günlük özet gösterilirken hata: {summary_error}", exc_info=True)

        except Exception as e:
            logger.error(f"Operator paneli hatası: {e}", exc_info=True)
            self.show_admin_dashboard(user_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Temayı Uygula
    Theme.apply_app_style(app)
    
    # === YENİ: Başlangıç logu ===
    logger.info("REFLEKS 360 R başlatıldı")
    
    window = EfesRotaApp()
    window.show()
    
    sys.exit(app.exec())