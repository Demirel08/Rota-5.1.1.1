"""
EFES ROTA X - Thread-Safe Veritabanı İşlemleri
QThread ile arka planda veritabanı sorguları çalıştırır.
UI donmasını önler.
"""

from PySide6.QtCore import QThread, Signal, QObject, QMutex, QMutexLocker
from typing import Any, Callable, Optional, List, Dict
from dataclasses import dataclass
from enum import Enum
import traceback


class TaskPriority(Enum):
    """Görev önceliği"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class DBTask:
    """Veritabanı görevi"""
    task_id: str
    query: str
    params: tuple = None
    callback: Callable = None
    error_callback: Callable = None
    priority: TaskPriority = TaskPriority.NORMAL
    fetch_type: str = "all"  # "all", "one", "execute"


class DatabaseWorker(QThread):
    """
    Arka planda veritabanı işlemleri yapan worker
    
    Sinyaller:
        result_ready: Sorgu sonucu hazır (task_id, result)
        error_occurred: Hata oluştu (task_id, error_message)
        progress_updated: İlerleme güncellemesi (task_id, percent)
    """
    
    result_ready = Signal(str, object)     # task_id, result
    error_occurred = Signal(str, str)       # task_id, error_message
    progress_updated = Signal(str, int)     # task_id, percent
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._tasks: List[DBTask] = []
        self._mutex = QMutex()
        self._running = True
    
    def add_task(self, task: DBTask):
        """Göreve ekle"""
        with QMutexLocker(self._mutex):
            # Önceliğe göre sırala
            self._tasks.append(task)
            self._tasks.sort(key=lambda x: x.priority.value, reverse=True)
    
    def run(self):
        """Thread ana döngüsü"""
        while self._running:
            task = None
            
            with QMutexLocker(self._mutex):
                if self._tasks:
                    task = self._tasks.pop(0)
            
            if task:
                self._execute_task(task)
            else:
                self.msleep(50)  # CPU kullanımını azalt
    
    def _execute_task(self, task: DBTask):
        """Görevi çalıştır"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(task.query, task.params or ())
                
                if task.fetch_type == "all":
                    result = cursor.fetchall()
                elif task.fetch_type == "one":
                    result = cursor.fetchone()
                else:
                    result = cursor.lastrowid
                
                self.result_ready.emit(task.task_id, result)
                
                if task.callback:
                    task.callback(result)
                    
        except Exception as e:
            error_msg = str(e)
            self.error_occurred.emit(task.task_id, error_msg)
            
            if task.error_callback:
                task.error_callback(error_msg)
    
    def stop(self):
        """Worker'ı durdur"""
        self._running = False
        self.wait()


class AsyncDatabaseManager(QObject):
    """
    Asenkron veritabanı yöneticisi
    
    Kullanım:
        from core.db_async import async_db
        
        # Basit sorgu
        async_db.fetch_all(
            "SELECT * FROM orders WHERE status = ?",
            ("Bekliyor",),
            callback=self.on_orders_loaded
        )
        
        # Hata yönetimiyle
        async_db.fetch_one(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
            callback=self.on_order_loaded,
            error_callback=self.on_error
        )
    """
    
    # Sinyaller
    data_loaded = Signal(str, object)      # query_name, data
    operation_completed = Signal(str)       # operation_name
    error_occurred = Signal(str, str)       # operation_name, error
    
    def __init__(self, db_manager=None):
        super().__init__()
        self._db_manager = db_manager
        self._worker: Optional[DatabaseWorker] = None
        self._task_counter = 0
        self._callbacks: Dict[str, tuple] = {}
    
    def set_database(self, db_manager):
        """Veritabanı bağlantısını ayarla"""
        self._db_manager = db_manager
        self._start_worker()
    
    def _start_worker(self):
        """Worker'ı başlat"""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
        
        self._worker = DatabaseWorker(self._db_manager)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
    
    def _generate_task_id(self) -> str:
        """Benzersiz görev ID'si oluştur"""
        self._task_counter += 1
        return f"task_{self._task_counter}"
    
    def _on_result(self, task_id: str, result):
        """Sonuç geldiğinde"""
        if task_id in self._callbacks:
            callback, _ = self._callbacks.pop(task_id)
            if callback:
                callback(result)
    
    def _on_error(self, task_id: str, error_msg: str):
        """Hata olduğunda"""
        if task_id in self._callbacks:
            _, error_callback = self._callbacks.pop(task_id)
            if error_callback:
                error_callback(error_msg)
        
        self.error_occurred.emit(task_id, error_msg)
    
    # === ANA METODLAR ===
    
    def fetch_all(self, query: str, params: tuple = None,
                  callback: Callable = None, error_callback: Callable = None,
                  priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Tüm sonuçları getir"""
        task_id = self._generate_task_id()
        
        self._callbacks[task_id] = (callback, error_callback)
        
        task = DBTask(
            task_id=task_id,
            query=query,
            params=params,
            priority=priority,
            fetch_type="all"
        )
        
        self._worker.add_task(task)
        return task_id
    
    def fetch_one(self, query: str, params: tuple = None,
                  callback: Callable = None, error_callback: Callable = None,
                  priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Tek sonuç getir"""
        task_id = self._generate_task_id()
        
        self._callbacks[task_id] = (callback, error_callback)
        
        task = DBTask(
            task_id=task_id,
            query=query,
            params=params,
            priority=priority,
            fetch_type="one"
        )
        
        self._worker.add_task(task)
        return task_id
    
    def execute(self, query: str, params: tuple = None,
                callback: Callable = None, error_callback: Callable = None,
                priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Sorgu çalıştır (INSERT, UPDATE, DELETE)"""
        task_id = self._generate_task_id()
        
        self._callbacks[task_id] = (callback, error_callback)
        
        task = DBTask(
            task_id=task_id,
            query=query,
            params=params,
            priority=priority,
            fetch_type="execute"
        )
        
        self._worker.add_task(task)
        return task_id
    
    def execute_many(self, query: str, params_list: List[tuple],
                     callback: Callable = None, error_callback: Callable = None) -> str:
        """Toplu sorgu çalıştır"""
        task_id = self._generate_task_id()
        
        def batch_execute():
            try:
                with self._db_manager.get_connection() as conn:
                    conn.executemany(query, params_list)
                if callback:
                    callback(len(params_list))
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        # Ayrı thread'de çalıştır
        from threading import Thread
        thread = Thread(target=batch_execute)
        thread.start()
        
        return task_id
    
    # === HAZIR SORGULAR ===
    
    def load_orders(self, status: str = None, callback: Callable = None):
        """Siparişleri yükle"""
        if status:
            query = "SELECT * FROM orders WHERE status = ? ORDER BY deadline"
            params = (status,)
        else:
            query = "SELECT * FROM orders ORDER BY deadline"
            params = None
        
        return self.fetch_all(query, params, callback, priority=TaskPriority.HIGH)
    
    def load_order_items(self, order_id: int, callback: Callable = None):
        """Sipariş kalemlerini yükle"""
        query = "SELECT * FROM order_items WHERE order_id = ?"
        return self.fetch_all(query, (order_id,), callback)
    
    def load_production_logs(self, order_id: int = None, 
                            station: str = None, callback: Callable = None):
        """Üretim loglarını yükle"""
        conditions = []
        params = []
        
        if order_id:
            conditions.append("order_id = ?")
            params.append(order_id)
        
        if station:
            conditions.append("station = ?")
            params.append(station)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM production_logs WHERE {where_clause} ORDER BY created_at DESC"
        
        return self.fetch_all(query, tuple(params) if params else None, callback)
    
    def load_dashboard_stats(self, callback: Callable = None):
        """Dashboard istatistiklerini yükle"""
        query = """
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'Bekliyor' THEN 1 ELSE 0 END) as waiting,
                SUM(CASE WHEN status = 'Üretimde' THEN 1 ELSE 0 END) as in_production,
                SUM(CASE WHEN status = 'Tamamlandı' THEN 1 ELSE 0 END) as completed,
                SUM(total_area) as total_area
            FROM orders
            WHERE created_at >= date('now', '-30 days')
        """
        return self.fetch_one(query, callback=callback, priority=TaskPriority.HIGH)
    
    def search_orders(self, search_term: str, callback: Callable = None):
        """Sipariş ara"""
        query = """
            SELECT * FROM orders 
            WHERE customer LIKE ? OR notes LIKE ? OR id = ?
            ORDER BY deadline
            LIMIT 100
        """
        term = f"%{search_term}%"
        
        try:
            order_id = int(search_term)
        except:
            order_id = -1
        
        return self.fetch_all(query, (term, term, order_id), callback, priority=TaskPriority.HIGH)
    
    def shutdown(self):
        """Temiz kapanış"""
        if self._worker:
            self._worker.stop()


class DataLoader(QObject):
    """
    Kullanışlı veri yükleyici
    
    Kullanım:
        loader = DataLoader(db_manager)
        
        # Callback ile
        loader.load_orders(callback=self.display_orders)
        
        # Sinyal ile
        loader.orders_loaded.connect(self.display_orders)
        loader.load_orders()
    """
    
    # Sinyaller
    orders_loaded = Signal(list)
    order_loaded = Signal(dict)
    items_loaded = Signal(list)
    stats_loaded = Signal(dict)
    error = Signal(str)
    loading_started = Signal()
    loading_finished = Signal()
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._loading_count = 0
    
    def _start_loading(self):
        """Yükleme başladı"""
        self._loading_count += 1
        if self._loading_count == 1:
            self.loading_started.emit()
    
    def _finish_loading(self):
        """Yükleme bitti"""
        self._loading_count = max(0, self._loading_count - 1)
        if self._loading_count == 0:
            self.loading_finished.emit()
    
    def load_orders(self, status: str = None, callback: Callable = None):
        """Siparişleri yükle"""
        self._start_loading()
        
        def on_loaded(data):
            self._finish_loading()
            orders = [dict(row) for row in data] if data else []
            self.orders_loaded.emit(orders)
            if callback:
                callback(orders)
        
        def on_error(msg):
            self._finish_loading()
            self.error.emit(f"Sipariş yükleme hatası: {msg}")
        
        # Senkron çalıştır (basit kullanım için)
        try:
            with self.db.get_connection() as conn:
                if status:
                    cursor = conn.execute(
                        "SELECT * FROM orders WHERE status = ? ORDER BY deadline",
                        (status,)
                    )
                else:
                    cursor = conn.execute("SELECT * FROM orders ORDER BY deadline")
                
                data = cursor.fetchall()
                on_loaded(data)
        except Exception as e:
            on_error(str(e))
    
    def load_order(self, order_id: int, callback: Callable = None):
        """Tek sipariş yükle"""
        self._start_loading()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM orders WHERE id = ?",
                    (order_id,)
                )
                row = cursor.fetchone()
                
                self._finish_loading()
                
                if row:
                    order = dict(row)
                    self.order_loaded.emit(order)
                    if callback:
                        callback(order)
                else:
                    self.error.emit(f"Sipariş bulunamadı: {order_id}")
                    
        except Exception as e:
            self._finish_loading()
            self.error.emit(str(e))


# Global instance (db_manager sonra set edilecek)
async_db = AsyncDatabaseManager()