"""
EFES ROTA X - Merkezi Logging Sistemi
Uygulama genelinde tutarlı log yönetimi sağlar.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class AppLogger:
    """
    Merkezi log yöneticisi
    
    Kullanım:
        from core.logger import logger
        
        logger.info("Sipariş oluşturuldu", order_id=12345)
        logger.error("Veritabanı hatası", exc_info=True)
        logger.warning("Kapasite aşıldı", station="TEMPER A1", load=120)
    """
    
    _instance: Optional['AppLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if AppLogger._initialized:
            return
        
        self._setup_logging()
        AppLogger._initialized = True
    
    def _setup_logging(self):
        """Logging sistemini kur"""
        # Log dizini
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Ana logger
        self.logger = logging.getLogger('EFES_ROTA_X')
        self.logger.setLevel(logging.DEBUG)
        
        # Formatter
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Dosya handler (Rotating - 5MB, 5 yedek)
        log_file = os.path.join(self.log_dir, 'app.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Hata log dosyası (sadece ERROR ve üstü)
        error_file = os.path.join(self.log_dir, 'error.log')
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=2*1024*1024,  # 2 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Console handler (INFO ve üstü)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Üretim log dosyası (özel)
        self.production_logger = logging.getLogger('EFES_PRODUCTION')
        self.production_logger.setLevel(logging.INFO)
        
        prod_file = os.path.join(self.log_dir, 'production.log')
        prod_handler = RotatingFileHandler(
            prod_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=10,
            encoding='utf-8'
        )
        prod_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.production_logger.addHandler(prod_handler)
    
    def _format_extra(self, **kwargs) -> str:
        """Ekstra parametreleri formatla"""
        if not kwargs:
            return ""
        parts = [f"{k}={v}" for k, v in kwargs.items()]
        return " | " + " | ".join(parts)
    
    # === STANDART LOG METODLARI ===
    
    def debug(self, message: str, **kwargs):
        """Debug seviyesi log"""
        self.logger.debug(message + self._format_extra(**kwargs))
    
    def info(self, message: str, **kwargs):
        """Info seviyesi log"""
        self.logger.info(message + self._format_extra(**kwargs))
    
    def warning(self, message: str, **kwargs):
        """Warning seviyesi log"""
        self.logger.warning(message + self._format_extra(**kwargs))
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Error seviyesi log"""
        self.logger.error(message + self._format_extra(**kwargs), exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Critical seviyesi log"""
        self.logger.critical(message + self._format_extra(**kwargs), exc_info=exc_info)
    
    # === ÖZEL LOG METODLARI ===
    
    def order_created(self, order_id: int, customer: str, total_area: float):
        """Sipariş oluşturma logu"""
        self.info(
            "Yeni sipariş oluşturuldu",
            order_id=order_id,
            customer=customer,
            total_area=f"{total_area:.2f}m²"
        )
        self.production_logger.info(
            f"SİPARİŞ_OLUŞTURULDU | ID:{order_id} | Müşteri:{customer} | Alan:{total_area:.2f}m²"
        )
    
    def order_updated(self, order_id: int, changes: str):
        """Sipariş güncelleme logu"""
        self.info("Sipariş güncellendi", order_id=order_id, changes=changes)
        self.production_logger.info(f"SİPARİŞ_GÜNCELLENDİ | ID:{order_id} | {changes}")
    
    def order_completed(self, order_id: int):
        """Sipariş tamamlama logu"""
        self.info("Sipariş tamamlandı", order_id=order_id)
        self.production_logger.info(f"SİPARİŞ_TAMAMLANDI | ID:{order_id}")
    
    def production_started(self, order_id: int, station: str, operator: str = None):
        """Üretim başlama logu"""
        self.info(
            "Üretim başladı",
            order_id=order_id,
            station=station,
            operator=operator or "Bilinmiyor"
        )
        self.production_logger.info(
            f"ÜRETİM_BAŞLADI | ID:{order_id} | İstasyon:{station} | Operatör:{operator or '-'}"
        )
    
    def production_completed(self, order_id: int, station: str, duration_minutes: float = None):
        """Üretim tamamlama logu"""
        self.info(
            "Üretim tamamlandı",
            order_id=order_id,
            station=station,
            duration=f"{duration_minutes:.1f}dk" if duration_minutes else "?"
        )
        self.production_logger.info(
            f"ÜRETİM_TAMAMLANDI | ID:{order_id} | İstasyon:{station} | Süre:{duration_minutes or '-'}dk"
        )
    
    def station_overload(self, station: str, load_percent: float, queue_count: int):
        """İstasyon aşırı yük uyarısı"""
        self.warning(
            "İstasyon kapasitesi aşıldı",
            station=station,
            load=f"{load_percent:.1f}%",
            queue=queue_count
        )
    
    def deadline_warning(self, order_id: int, days_remaining: float):
        """Termin uyarısı"""
        if days_remaining < 0:
            self.warning(
                "Sipariş gecikti!",
                order_id=order_id,
                days_late=f"{abs(days_remaining):.1f}"
            )
        elif days_remaining < 2:
            self.warning(
                "Sipariş termini yaklaşıyor",
                order_id=order_id,
                days_remaining=f"{days_remaining:.1f}"
            )
    
    def db_operation(self, operation: str, table: str, duration_ms: float = None):
        """Veritabanı işlem logu"""
        self.debug(
            f"DB {operation}",
            table=table,
            duration=f"{duration_ms:.2f}ms" if duration_ms else None
        )
    
    def user_login(self, username: str, role: str, success: bool):
        """Kullanıcı giriş logu"""
        if success:
            self.info("Kullanıcı girişi başarılı", user=username, role=role)
        else:
            self.warning("Kullanıcı girişi başarısız", user=username)
    
    def user_logout(self, username: str):
        """Kullanıcı çıkış logu"""
        self.info("Kullanıcı çıkış yaptı", user=username)
    
    def export_created(self, export_type: str, filename: str, record_count: int):
        """Dışa aktarma logu"""
        self.info(
            "Dışa aktarma oluşturuldu",
            type=export_type,
            file=filename,
            records=record_count
        )
    
    def import_completed(self, import_type: str, filename: str, success_count: int, error_count: int):
        """İçe aktarma logu"""
        self.info(
            "İçe aktarma tamamlandı",
            type=import_type,
            file=filename,
            success=success_count,
            errors=error_count
        )
    
    def performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Performans metriği logu"""
        self.debug(f"Performans: {metric_name} = {value}{unit}")
    
    # === YARDIMCI METODLAR ===
    
    def get_log_files(self) -> list:
        """Log dosyalarını listele"""
        if not os.path.exists(self.log_dir):
            return []
        
        files = []
        for f in os.listdir(self.log_dir):
            if f.endswith('.log'):
                path = os.path.join(self.log_dir, f)
                files.append({
                    'name': f,
                    'path': path,
                    'size': os.path.getsize(path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(path))
                })
        return sorted(files, key=lambda x: x['modified'], reverse=True)
    
    def get_recent_errors(self, count: int = 50) -> list:
        """Son hataları getir"""
        error_file = os.path.join(self.log_dir, 'error.log')
        if not os.path.exists(error_file):
            return []
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return lines[-count:] if len(lines) > count else lines
        except Exception:
            return []
    
    def clear_old_logs(self, days: int = 30):
        """Eski logları temizle"""
        if not os.path.exists(self.log_dir):
            return
        
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for f in os.listdir(self.log_dir):
            if f.endswith('.log'):
                path = os.path.join(self.log_dir, f)
                if os.path.getmtime(path) < cutoff:
                    try:
                        os.remove(path)
                        self.info(f"Eski log dosyası silindi: {f}")
                    except Exception as e:
                        self.error(f"Log silme hatası: {f}", exc_info=True)


# Singleton instance
logger = AppLogger()


# === DEKORATÖRLER ===

def log_function_call(func):
    """Fonksiyon çağrılarını logla"""
    def wrapper(*args, **kwargs):
        logger.debug(f"Fonksiyon çağrıldı: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Fonksiyon hatası: {func.__name__} - {str(e)}", exc_info=True)
            raise
    return wrapper


def log_db_operation(operation_name: str):
    """Veritabanı işlemlerini logla"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.db_operation(operation_name, func.__name__, duration)
                return result
            except Exception as e:
                logger.error(f"DB Hatası ({operation_name}): {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator