import sqlite3
import hashlib
import os
from contextlib import contextmanager
from datetime import datetime

# === GÜVENLİK VE LOGLAMA ===
try:
    from core.security import password_manager
    from core.logger import logger
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False


class DatabaseManager:
    """
    EFES ROTA X - Merkezi Veritabanı Yöneticisi
    FİNAL SÜRÜM (Tamir Modlu):
    - Eksik kolonları otomatik onarır (Migrasyon).
    - Fire/Rework ve Loglama tam fonksiyonludur.
    """
    
    def __init__(self, db_name="efes_factory.db"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_name)
        
        self.init_database()
        self._migrate_tables() # Otomatik onarım
        self.create_default_users() 
        self.init_default_stocks()
        self.init_machine_capacities()
        self.init_default_prices()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"❌ Veritabanı Hatası: {e}")
            if SECURITY_AVAILABLE:
                logger.error(f"Veritabanı Hatası: {e}")
            raise e
        finally:
            conn.close()

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tablolar
            cursor.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, role TEXT, full_name TEXT, station_name TEXT)""")

            # Projeler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    customer_name TEXT,
                    delivery_date TEXT,
                    status TEXT DEFAULT 'Devam Ediyor',
                    priority TEXT DEFAULT 'Normal',
                    notes TEXT,
                    color TEXT DEFAULT '#6B46C1',
                    order_prefix TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_code TEXT NOT NULL, 
                    barcode TEXT,
                    customer_name TEXT,
                    product_type TEXT,
                    thickness INTEGER,
                    width REAL,
                    height REAL,
                    quantity INTEGER NOT NULL,
                    declared_total_m2 REAL DEFAULT 0,
                    route TEXT, 
                    sale_price REAL DEFAULT 0,
                    total_price REAL DEFAULT 0,
                    calculated_cost REAL DEFAULT 0,
                    profit REAL DEFAULT 0,
                    currency TEXT DEFAULT 'TL',
                    status TEXT DEFAULT 'Beklemede',
                    priority TEXT DEFAULT 'Normal',
                    has_breakage INTEGER DEFAULT 0,
                    rework_count INTEGER DEFAULT 0,
                    pallet_id INTEGER,
                    delivery_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    queue_position INTEGER DEFAULT 9999
                )
            """)

            cursor.execute("""CREATE TABLE IF NOT EXISTS production_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, station_name TEXT, action TEXT, quantity INTEGER, operator_name TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(order_id) REFERENCES orders(id))""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS stocks (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT UNIQUE, quantity_m2 REAL DEFAULT 0, min_limit REAL DEFAULT 100, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS factory_settings (setting_key TEXT UNIQUE, setting_value REAL DEFAULT 0)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS unit_prices (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT UNIQUE, price_per_m2 REAL DEFAULT 0, category TEXT)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS shipments (id INTEGER PRIMARY KEY AUTOINCREMENT, pallet_name TEXT NOT NULL, customer_name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'Hazırlanıyor')""")

            # Plaka stok tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thickness INTEGER NOT NULL,
                    glass_type TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # İndeksler
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_order_id ON production_logs(order_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_station ON production_logs(station_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_plates_thickness_type ON plates(thickness, glass_type)")
            except: pass

    def _migrate_tables(self):
        """Eski veritabanı dosyalarını yeni yapıya uygun hale getirir (Eksik kolonları ekler)"""
        with self.get_connection() as conn:
            # Orders tablosu için kritik kolonlar
            columns = {
                'sale_price': 'REAL DEFAULT 0',
                'total_price': 'REAL DEFAULT 0',
                'currency': "TEXT DEFAULT 'TL'",
                'has_breakage': 'INTEGER DEFAULT 0',
                'rework_count': 'INTEGER DEFAULT 0',
                'pallet_id': 'INTEGER',
                'queue_position': 'INTEGER DEFAULT 9999',
                'notes': 'TEXT DEFAULT ""',
                'project_id': 'INTEGER'
            }

            # Mevcut kolonları al
            try:
                cursor = conn.execute("PRAGMA table_info(orders)")
                existing_cols = [row['name'] for row in cursor.fetchall()]

                for col, type_def in columns.items():
                    if col not in existing_cols:
                        try:
                            conn.execute(f"ALTER TABLE orders ADD COLUMN {col} {type_def}")
                            print(f"Onarım: '{col}' kolonu eklendi.")
                        except: pass
            except: pass

            # Proje status güncellemesi: 'Devam Ediyor' -> 'Aktif'
            try:
                conn.execute("UPDATE projects SET status = 'Aktif' WHERE status = 'Devam Ediyor'")
                print("Proje statusleri güncellendi: 'Devam Ediyor' -> 'Aktif'")
            except:
                pass

            # Projects tablosuna yeni kolonları ekle
            try:
                cursor = conn.execute("PRAGMA table_info(projects)")
                project_cols = [row['name'] for row in cursor.fetchall()]

                if 'color' not in project_cols:
                    conn.execute("ALTER TABLE projects ADD COLUMN color TEXT DEFAULT '#6B46C1'")
                    print("Projects tablosuna 'color' kolonu eklendi")

                if 'order_prefix' not in project_cols:
                    conn.execute("ALTER TABLE projects ADD COLUMN order_prefix TEXT")
                    print("Projects tablosuna 'order_prefix' kolonu eklendi")
            except Exception as e:
                print(f"Proje kolonları eklenirken hata: {e}")

    # --- BAŞLANGIÇ VERİLERİ ---
    def init_machine_capacities(self):
        defaults = {"INTERMAC": 800, "LIVA KESIM": 800, "LAMINE KESIM": 600, "CNC RODAJ": 100, "DOUBLEDGER": 400, "ZIMPARA": 300, "TESIR A1": 400, "TESIR B1": 400, "DELİK": 200, "OYGU": 200, "TEMPER A1": 550, "TEMPER B1": 750, "LAMINE A1": 250, "ISICAM B1": 500, "SEVKİYAT": 5000}
        with self.get_connection() as conn:
            for name, cap in defaults.items():
                try: conn.execute("INSERT INTO factory_settings (setting_key, setting_value) VALUES (?, ?)", (name, cap))
                except: pass

    def init_default_stocks(self):
        defaults = [("4mm Düz Cam", 1000, 200), ("6mm Düz Cam", 1000, 200)]
        with self.get_connection() as conn:
            for n, q, l in defaults:
                try: conn.execute("INSERT INTO stocks (product_name, quantity_m2, min_limit) VALUES (?, ?, ?)", (n, q, l))
                except: pass

    def init_default_prices(self):
        defaults = [("4mm Düz Cam", 100, "HAMMADDE"), ("KESİM İŞÇİLİK", 10, "İŞLEM")]
        with self.get_connection() as conn:
            for n, p, c in defaults:
                try: conn.execute("INSERT INTO unit_prices (item_name, price_per_m2, category) VALUES (?, ?, ?)", (n, p, c))
                except: pass

    def create_default_users(self):
        with self.get_connection() as conn:
            try:
                ph = "1234"
                if SECURITY_AVAILABLE: ph = password_manager.hash_password("1234")
                conn.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)", ("admin", ph, "admin", "Admin"))
            except: pass

    # --- KULLANICI İŞLEMLERİ ---
    def check_login(self, username, password):
        with self.get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if not user: return None
            
            stored = user['password_hash']
            if SECURITY_AVAILABLE:
                if password_manager.verify_password(password, stored):
                    if password_manager.is_legacy_hash(stored):
                        new_hash = password_manager.hash_password(password)
                        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user['id']))
                    logger.user_login(username, user['role'], success=True)
                    return dict(user)
            elif stored == hashlib.sha256(password.encode()).hexdigest() or stored == password:
                return dict(user)
            return None

    def get_all_users(self):
        with self.get_connection() as conn: return [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]

    def add_new_user(self, u, p, r, f, s):
        ph = password_manager.hash_password(p) if SECURITY_AVAILABLE else p
        with self.get_connection() as conn:
            try:
                conn.execute("INSERT INTO users (username, password_hash, role, full_name, station_name) VALUES (?, ?, ?, ?, ?)", (u, ph, r, f, s))
                return True, "Ok"
            except Exception as e: return False, str(e)

    def delete_user(self, uid):
        with self.get_connection() as conn: conn.execute("DELETE FROM users WHERE id=?", (uid,))
        return True

    # --- STOK İŞLEMLERİ ---
    def get_all_stocks(self):
        with self.get_connection() as conn: return [dict(r) for r in conn.execute("SELECT * FROM stocks ORDER BY product_name").fetchall()]

    def add_stock(self, p_name, amount):
        with self.get_connection() as conn:
            if conn.execute("SELECT id FROM stocks WHERE product_name=?", (p_name,)).fetchone():
                conn.execute("UPDATE stocks SET quantity_m2 = quantity_m2 + ? WHERE product_name=?", (amount, p_name))
            else:
                conn.execute("INSERT INTO stocks (product_name, quantity_m2, min_limit) VALUES (?, ?, 100)", (p_name, amount))

    def get_stock_quantity(self, p_name):
        with self.get_connection() as conn:
            r = conn.execute("SELECT quantity_m2 FROM stocks WHERE product_name=?", (p_name,)).fetchone()
            return r[0] if r else 0

    def update_stock(self, product_name, quantity):
        with self.get_connection() as conn:
            conn.execute("UPDATE stocks SET quantity_m2 = ?, last_updated = CURRENT_TIMESTAMP WHERE product_name = ?", (quantity, product_name))

    def delete_stock(self, stock_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))

    def get_low_stocks(self):
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM stocks WHERE quantity_m2 < min_limit ORDER BY product_name").fetchall()]

    # --- SİPARİŞ İŞLEMLERİ ---
    def add_new_order(self, data):
        total_m2 = data.get('total_m2') or 0
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO orders (order_code, customer_name, product_type, thickness, quantity,
                                       delivery_date, priority, status, route, declared_total_m2, width, height, sale_price, total_price, notes, project_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Beklemede', ?, ?, ?, ?, ?, ?, ?, ?)
                """, (data['code'], data['customer'], data['product'], data['thickness'], data['quantity'],
                      data['date'], data['priority'], data.get('route', ''), total_m2, data.get('width',0), data.get('height',0), 0, 0, data.get('notes', ''), data.get('project_id')))

                # Stok düş
                p_name = f"{data['thickness']}mm {data['product']}"
                conn.execute("UPDATE stocks SET quantity_m2 = quantity_m2 - ? WHERE product_name = ?", (total_m2, p_name))
                return True
            except Exception as e:
                print(e)
                return False

    def get_orders_by_status(self, status):
        with self.get_connection() as conn:
            if isinstance(status, list):
                p = ','.join(['?']*len(status))
                return [dict(r) for r in conn.execute(f"SELECT * FROM orders WHERE status IN ({p}) ORDER BY CASE priority WHEN 'Kritik' THEN 1 ELSE 2 END, queue_position ASC, delivery_date ASC", tuple(status)).fetchall()]
            return [dict(r) for r in conn.execute("SELECT * FROM orders WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()]

    def get_all_orders(self):
        with self.get_connection() as conn: return [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()]

    def update_order_status(self, oid, st):
        with self.get_connection() as conn: conn.execute("UPDATE orders SET status=? WHERE id=?", (st, oid))

    def get_order_by_code(self, code):
        """Hata korumalı sipariş getirme (Sütun eksik olsa bile çalışır)"""
        with self.get_connection() as conn:
            r = conn.execute("SELECT * FROM orders WHERE order_code=?", (code,)).fetchone()
            if not r: return None
            d = dict(r)
            return {
                'id': d['id'], 'code': d['order_code'], 'customer': d['customer_name'],
                'product': d['product_type'], 'thickness': d['thickness'], 'width': d.get('width', 0),
                'height': d.get('height', 0), 'quantity': d['quantity'], 'total_m2': d['declared_total_m2'],
                'priority': d['priority'], 'date': d['delivery_date'], 'route': d.get('route', ''),
                'status': d['status'], 'sale_price': d.get('sale_price', 0)
            }

    # --- ÜRETİM VE FİRE (CRITICAL) ---
    def report_fire(self, oid, qty, station_name="Bilinmiyor", operator_name="Sistem"):
        """Fire bildiriminde Adet Düşürme ve Rework"""
        with self.get_connection() as conn: 
            # 1. Logla
            conn.execute("""
                INSERT INTO production_logs (order_id, station_name, action, quantity, operator_name)
                VALUES (?, ?, 'Fire/Kırık', ?, ?)
            """, (oid, station_name, qty, operator_name))
            
            # 2. ASIL SİPARİŞİ GÜNCELLE: Adedi düşür
            orig = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
            if not orig: return
            
            current_qty = orig['quantity']
            new_qty = max(0, current_qty - qty)
            current_m2 = orig['declared_total_m2']
            unit_m2 = current_m2 / current_qty if current_qty > 0 else 0
            new_m2 = unit_m2 * new_qty
            
            conn.execute("UPDATE orders SET quantity=?, declared_total_m2=?, rework_count=rework_count+?, has_breakage=1 WHERE id=?", (new_qty, new_m2, qty, oid))
            
            # 3. YENİ REWORK SİPARİŞİ
            base_code = orig['order_code']
            if "-R" in base_code:
                try:
                    parts = base_code.split("-R")
                    new_ver = int(parts[1]) + 1
                    new_code = f"{parts[0]}-R{new_ver}"
                except: new_code = f"{base_code}-R1"
            else:
                new_code = f"{base_code}-R1"
            
            rework_m2 = unit_m2 * qty
            
            conn.execute("""
                INSERT INTO orders (
                    order_code, customer_name, product_type, thickness, width, height,
                    quantity, declared_total_m2, route, priority, status, delivery_date,
                    sale_price, total_price, currency, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Kritik', 'Beklemede', ?, 0, 0, ?, CURRENT_TIMESTAMP)
            """, (
                new_code, orig['customer_name'], orig['product_type'], orig['thickness'],
                orig['width'], orig['height'], qty, rework_m2, orig['route'],
                orig['delivery_date'], orig['currency']
            ))
        
        if SECURITY_AVAILABLE: logger.warning(f"Fire: {orig['order_code']} ({qty} adet) - Rework açıldı.")

    def get_station_progress(self, order_id, station_name):
        with self.get_connection() as conn:
            # Sadece 'Tamamlandi' olanlar sayılır (Hedef zaten düştü)
            r = conn.execute("SELECT SUM(quantity) FROM production_logs WHERE order_id = ? AND station_name = ? AND action = 'Tamamlandi'", (order_id, station_name)).fetchone()
            return r[0] if r[0] else 0

    def get_completed_stations_list(self, order_id):
        with self.get_connection() as conn:
            res = conn.execute("SELECT quantity FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not res: return []
            target = res[0]
            
            rows = conn.execute("SELECT station_name, SUM(quantity) FROM production_logs WHERE order_id = ? AND action = 'Tamamlandi' GROUP BY station_name", (order_id,)).fetchall()
            completed = []
            for row in rows:
                if row[1] >= target: completed.append(row[0])
            return completed

    def register_production(self, order_id, station_name, qty_done, operator_name="Sistem"):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO production_logs (order_id, station_name, action, quantity, operator_name) VALUES (?, ?, 'Tamamlandi', ?, ?)", 
                       (order_id, station_name, qty_done, operator_name))
            
            if self._check_all_stations_completed(order_id):
                conn.execute("UPDATE orders SET status='Tamamlandı' WHERE id=?", (order_id,))
            else:
                conn.execute("UPDATE orders SET status='Üretimde' WHERE id=? AND status!='Tamamlandı'", (order_id,))

    def complete_station_process(self, order_id, station_name):
        with self.get_connection() as conn:
            done = self.get_station_progress(order_id, station_name)
            target = conn.execute("SELECT quantity FROM orders WHERE id=?", (order_id,)).fetchone()[0]
            rem = target - done
            if rem > 0:
                conn.execute("INSERT INTO production_logs (order_id, station_name, action, quantity, operator_name) VALUES (?, ?, 'Tamamlandi', ?, 'Sistem')", (order_id, station_name, rem))
            
            if self._check_all_stations_completed(order_id):
                conn.execute("UPDATE orders SET status='Tamamlandı' WHERE id=?", (order_id,))
            else:
                conn.execute("UPDATE orders SET status='Üretimde' WHERE id=? AND status!='Tamamlandı'", (order_id,))

    def _check_all_stations_completed(self, order_id):
        with self.get_connection() as conn:
            o = conn.execute("SELECT route FROM orders WHERE id=?", (order_id,)).fetchone()
            if not o or not o['route']: return False
            stations = [s.strip() for s in o['route'].split(',')]
            completed = self.get_completed_stations_list(order_id)
            for s in stations:
                if s not in completed: return False
            return True

    # --- DASHBOARD & MATRİS ---
    def get_production_matrix_advanced(self):
        with self.get_connection() as conn:
            orders = conn.execute("SELECT * FROM orders WHERE status NOT IN ('Sevk Edildi', 'Hatalı/Fire') ORDER BY queue_position ASC").fetchall()
            data = []
            for r in orders:
                oid = r['id']
                qty = r['quantity']
                route = r['route'] or ""
                status_map = {}
                stations = [s.strip() for s in route.split(',')]
                
                for st in stations:
                    done = self.get_station_progress(oid, st)
                    if done >= qty: st_stat = "Bitti"
                    elif done > 0: st_stat = "Kısmi"
                    else: st_stat = "Bekliyor"
                    status_map[st] = {"status": st_stat, "done": done, "total": qty}
                
                data.append({
                    "id": oid, "code": r['order_code'], "customer": r['customer_name'],
                    "quantity": qty, "route": route, "priority": r['priority'],
                    "delivery_date": r['delivery_date'], "m2": r['declared_total_m2'],
                    "status": r['status'], "status_map": status_map, "queue_position": r['queue_position'],
                    "thickness": r['thickness'], "product_type": r['product_type']
                })
            return data

    def get_dashboard_stats(self):
        with self.get_connection() as conn:
            active = conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Beklemede', 'Üretimde')").fetchone()[0]
            urgent = conn.execute("SELECT COUNT(*) FROM orders WHERE priority IN ('Kritik', 'Acil') AND status!='Tamamlandı'").fetchone()[0]
            fire = conn.execute("SELECT SUM(rework_count) FROM orders").fetchone()[0] or 0
            return {"active": active, "urgent": urgent, "fire": fire}

    def get_station_loads(self):
        CAPACITIES = self.get_all_capacities()
        loads = {k: 0.0 for k in CAPACITIES.keys()}
        with self.get_connection() as conn:
            orders = conn.execute("SELECT id, quantity, route, declared_total_m2 FROM orders WHERE status != 'Tamamlandı'").fetchall()
            for r in orders:
                m2 = r['declared_total_m2'] or 0
                completed = self.get_completed_stations_list(r['id'])
                route = r['route'] or ""
                for st in CAPACITIES.keys():
                    if st in route and st not in completed:
                        loads[st] += m2
        res = []
        for station, cap in CAPACITIES.items():
            if cap <= 0: cap = 1
            percent = int((loads[station] / cap) * 100)
            status = "Normal"
            if percent > 90: status = "Kritik"
            elif percent > 70: status = "Yogun"
            res.append({"name": station, "percent": min(percent, 100), "status": status})
        return res

    # --- LOGLAMA ve RAPORLAMA (EKSİK OLANLAR EKLENDİ) ---
    def get_system_logs(self, limit=50):
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT pl.timestamp, pl.operator_name, pl.station_name, pl.action, o.order_code, o.customer_name
                FROM production_logs pl
                LEFT JOIN orders o ON pl.order_id = o.id
                ORDER BY pl.timestamp DESC LIMIT ?
            """, (limit,)).fetchall()]

    def search_logs(self, k):
        s = f"%{k}%"
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT pl.timestamp, pl.operator_name, pl.station_name, pl.action, o.order_code, o.customer_name
                FROM production_logs pl
                LEFT JOIN orders o ON pl.order_id = o.id
                WHERE o.order_code LIKE ? OR pl.operator_name LIKE ?
                ORDER BY pl.timestamp DESC
            """, (s, s)).fetchall()]

    def get_production_report_data(self, d1, d2):
        with self.get_connection() as conn: 
            return [dict(r) for r in conn.execute("""
                SELECT pl.timestamp as islem_tarihi, o.order_code as siparis_no, 
                       o.customer_name as musteri, pl.station_name as istasyon, 
                       pl.action as islem, pl.operator_name as operator 
                FROM production_logs pl 
                JOIN orders o ON pl.order_id = o.id 
                WHERE date(pl.timestamp) BETWEEN ? AND ? 
                ORDER BY pl.timestamp DESC
            """, (d1, d2)).fetchall()]

    def get_operator_performance(self, days=30):
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT operator_name, COUNT(*) as islem_sayisi, SUM(quantity) as toplam_adet
                FROM production_logs 
                WHERE timestamp >= date('now', '-' || ? || ' days')
                AND operator_name IS NOT NULL AND operator_name != 'Sistem'
                GROUP BY operator_name 
                ORDER BY toplam_adet DESC
            """, (days,)).fetchall()]

    def get_fire_analysis_data(self):
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT station_name, SUM(quantity) as fire_adedi
                FROM production_logs 
                WHERE action LIKE '%Fire%' OR action LIKE '%Kırık%'
                GROUP BY station_name 
                ORDER BY fire_adedi DESC
            """).fetchall()]

    # --- KAPASİTE & AYARLAR ---
    def get_all_capacities(self):
        """Kapasiteleri factory_config'den al (merkezi sistem)"""
        try:
            from core.factory_config import factory_config
            return factory_config.get_capacities()
        except:
            # Fallback: Eski sistem
            with self.get_connection() as conn:
                d = {r[0]: r[1] for r in conn.execute("SELECT setting_key, setting_value FROM factory_settings").fetchall()}
                if not d:
                    self.init_machine_capacities()
                    return self.get_all_capacities()
                return d

    def update_capacity(self, m, v):
        """Kapasiteyi hem factory_config hem eski tabloya yaz (uyumluluk için)"""
        # Yeni sistem
        try:
            from core.factory_config import factory_config
            factory_config.update_capacity(m, v)
        except:
            pass

        # Eski sistem (geriye uyumluluk)
        with self.get_connection() as conn:
            conn.execute("UPDATE factory_settings SET setting_value=? WHERE setting_key=?", (v, m))

    def get_all_prices(self):
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM unit_prices ORDER BY category, item_name").fetchall()]

    def update_price(self, item_name, new_price):
        with self.get_connection() as conn:
            conn.execute("UPDATE unit_prices SET price_per_m2 = ? WHERE item_name = ?", (new_price, item_name))

    def add_price(self, item_name, price, category):
        with self.get_connection() as conn:
            try:
                conn.execute("INSERT INTO unit_prices (item_name, price_per_m2, category) VALUES (?, ?, ?)", (item_name, price, category))
                return True
            except:
                return False

    # --- SEVKİYAT ---
    def get_ready_to_ship_orders(self):
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM orders WHERE status = 'Tamamlandı' AND (pallet_id IS NULL OR pallet_id = 0) ORDER BY order_code").fetchall()]

    def get_active_pallets(self):
        with self.get_connection() as conn: return [dict(r) for r in conn.execute("SELECT * FROM shipments WHERE status = 'Hazırlanıyor'").fetchall()]
    
    def create_pallet(self, n, c):
        with self.get_connection() as conn: conn.execute("INSERT INTO shipments (pallet_name, customer_name) VALUES (?, ?)", (n, c))

    def add_order_to_pallet(self, oid, pid):
        with self.get_connection() as conn: conn.execute("UPDATE orders SET pallet_id=? WHERE id=?", (pid, oid))

    def ship_pallet(self, pid):
        with self.get_connection() as conn:
            conn.execute("UPDATE shipments SET status='Sevk Edildi' WHERE id=?", (pid,))
            conn.execute("UPDATE orders SET status='Sevk Edildi' WHERE pallet_id=?", (pid,))

    def get_shipped_pallets(self):
        with self.get_connection() as conn: return [dict(r) for r in conn.execute("SELECT * FROM shipments WHERE status='Sevk Edildi' ORDER BY created_at DESC").fetchall()]

    def get_shipped_orders(self):
        with self.get_connection() as conn: return [dict(r) for r in conn.execute("SELECT * FROM orders WHERE status = 'Sevk Edildi' ORDER BY order_code DESC").fetchall()]

    def update_all_order_statuses(self):
        with self.get_connection() as conn:
            orders = conn.execute("SELECT id, status FROM orders WHERE status NOT IN ('Sevk Edildi', 'Hatalı/Fire')").fetchall()
            count = 0
            for order in orders:
                if self._check_all_stations_completed(order['id']):
                    if order['status'] != 'Tamamlandı':
                        conn.execute("UPDATE orders SET status = 'Tamamlandı' WHERE id = ?", (order['id'],))
                        count += 1
            return count
    def get_today_completed_count(self):
        """Bugün tamamlanan (statüsü 'Tamamlandı' olan) sipariş sayısını üretim loglarından bulur"""
        with self.get_connection() as conn:
            # Bugünün tarihi (YYYY-MM-DD)
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            # production_logs tablosundan, bugün 'Tamamlandi' action'ı alan benzersiz siparişleri say
            # Ancak burada dikkat: Bir siparişin birden fazla istasyonu bugün bitebilir.
            # Bizim için önemli olan siparişin statüsünün 'Tamamlandı'ya dönmesi.
            # En garantisi: Statüsü 'Tamamlandı' olan ve son işlem tarihi bugün olan siparişler.
            
            # Basitleştirilmiş Yöntem: Log tablosunda bugün 'Tamamlandi' kaydı olan siparişler
            # (Bu tam doğru olmayabilir ama %90 yeterlidir. Tam doğrusu orders tablosuna completed_at eklemektir)
            
            # ÖNERİLEN YÖNTEM: orders tablosuna completed_at ekleyene kadar şu anki en iyi tahmin:
            # Bugün bir istasyonu biten ve şu an statüsü 'Tamamlandı' olanlar.
            query = """
                SELECT COUNT(DISTINCT o.id)
                FROM orders o
                JOIN production_logs pl ON o.id = pl.order_id
                WHERE o.status = 'Tamamlandı' 
                AND pl.action = 'Tamamlandi'
                AND date(pl.timestamp) = date('now', 'localtime')
            """
            result = conn.execute(query).fetchone()
            return result[0] if result else 0

    # --- PLAKA YÖNETİMİ ---
    def add_plate(self, thickness, glass_type, width, height, quantity, location=""):
        """Depoya yeni plaka ekle"""
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO plates (thickness, glass_type, width, height, quantity, location)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (thickness, glass_type, width, height, quantity, location))
                return True
            except Exception as e:
                print(f"Plaka ekleme hatası: {e}")
                return False

    def get_all_plates(self):
        """Tüm plakaları getir"""
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT * FROM plates
                WHERE quantity > 0
                ORDER BY thickness, glass_type, width, height
            """).fetchall()]

    def get_plates_by_thickness_type(self, thickness, glass_type):
        """Belirli kalınlık ve tipte plakaları getir"""
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT * FROM plates
                WHERE thickness = ? AND glass_type = ? AND quantity > 0
                ORDER BY width DESC, height DESC
            """, (thickness, glass_type)).fetchall()]

    def update_plate_quantity(self, plate_id, quantity_change):
        """Plaka miktarını güncelle (+ veya -)"""
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    UPDATE plates
                    SET quantity = quantity + ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (quantity_change, plate_id))
                return True
            except Exception as e:
                print(f"Plaka güncelleme hatası: {e}")
                return False

    def decrease_plate_stock(self, plate_id, amount=1):
        """Plaka stoğunu azalt"""
        return self.update_plate_quantity(plate_id, -amount)

    def increase_plate_stock(self, plate_id, amount=1):
        """Plaka stoğunu artır"""
        return self.update_plate_quantity(plate_id, amount)

    def get_plate_summary(self):
        """Plaka stok özeti (kalınlık ve tipe göre gruplu)"""
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT
                    thickness,
                    glass_type,
                    COUNT(*) as variant_count,
                    SUM(quantity) as total_quantity
                FROM plates
                WHERE quantity > 0
                GROUP BY thickness, glass_type
                ORDER BY thickness, glass_type
            """).fetchall()]

    # --- PROJE YÖNETİMİ ---
    def add_project(self, data):
        """Yeni proje ekle - data dictionary veya dict-like object alır"""
        with self.get_connection() as conn:
            try:
                # Dictionary veya dict-like object kontrolü
                if hasattr(data, 'get'):
                    project_name = data.get('project_name')
                    customer_name = data.get('customer_name')
                    delivery_date = data.get('delivery_date')
                    priority = data.get('priority', 'Normal')
                    notes = data.get('notes', '')
                    status = data.get('status', 'Aktif')
                    color = data.get('color', '#6B46C1')
                    order_prefix = data.get('order_prefix', '')
                else:
                    # Eski kullanım için geriye dönük uyumluluk
                    project_name = data
                    customer_name = None
                    delivery_date = None
                    priority = 'Normal'
                    notes = ''
                    status = 'Aktif'
                    color = '#6B46C1'
                    order_prefix = ''

                cursor = conn.execute("""
                    INSERT INTO projects (project_name, customer_name, delivery_date, priority, notes, status, color, order_prefix)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (project_name, customer_name, delivery_date, priority, notes, status, color, order_prefix))
                return cursor.lastrowid
            except Exception as e:
                print(f"Proje ekleme hatası: {e}")
                return None

    def get_all_projects(self, status_filter=None):
        """Tüm projeleri getir"""
        with self.get_connection() as conn:
            if status_filter:
                return [dict(r) for r in conn.execute("""
                    SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC
                """, (status_filter,)).fetchall()]
            else:
                return [dict(r) for r in conn.execute("""
                    SELECT * FROM projects ORDER BY created_at DESC
                """).fetchall()]

    def get_project_by_id(self, project_id):
        """Belirli bir projeyi getir"""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return dict(row) if row else None

    def get_project_orders(self, project_id):
        """Projeye ait tüm siparişleri getir"""
        with self.get_connection() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT * FROM orders WHERE project_id = ? ORDER BY created_at
            """, (project_id,)).fetchall()]

    def get_project_summary(self, project_id):
        """Proje özeti (toplam sipariş, m², ilerleme)"""
        with self.get_connection() as conn:
            # Toplam sipariş sayısı ve m²
            summary = conn.execute("""
                SELECT
                    COUNT(*) as total_orders,
                    COALESCE(SUM(declared_total_m2), 0) as total_m2,
                    SUM(CASE WHEN status = 'Tamamlandı' THEN 1 ELSE 0 END) as completed_orders,
                    COALESCE(SUM(CASE WHEN status = 'Tamamlandı' THEN declared_total_m2 ELSE 0 END), 0) as completed_m2
                FROM orders
                WHERE project_id = ?
            """, (project_id,)).fetchone()

            if summary:
                result = dict(summary)
                # İlerleme yüzdesi hesapla
                total_orders = result.get('total_orders') or 0
                completed_orders = result.get('completed_orders') or 0
                if total_orders > 0:
                    result['progress_percent'] = int((completed_orders / total_orders) * 100)
                else:
                    result['progress_percent'] = 0
                return result
            return None

    def update_project(self, project_id, **kwargs):
        """Proje bilgilerini güncelle"""
        with self.get_connection() as conn:
            # Güncellenecek alanları hazırla
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['project_name', 'customer_name', 'delivery_date', 'status', 'priority', 'notes', 'color', 'order_prefix']:
                    fields.append(f"{key} = ?")
                    values.append(value)

            if not fields:
                return False

            values.append(project_id)
            query = f"UPDATE projects SET {', '.join(fields)} WHERE id = ?"

            try:
                conn.execute(query, values)
                return True
            except Exception as e:
                print(f"Proje güncelleme hatası: {e}")
                return False

    def delete_project(self, project_id):
        """Projeyi sil (siparişlerin project_id'sini NULL yap)"""
        with self.get_connection() as conn:
            # Önce siparişlerin project_id'sini NULL yap
            conn.execute("UPDATE orders SET project_id = NULL WHERE project_id = ?", (project_id,))
            # Sonra projeyi sil
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return True

    def complete_project(self, project_id):
        """Projeyi tamamla"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE projects
                SET status = 'Tamamlandı', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (project_id,))
            return True

    def get_active_projects_count(self):
        """Aktif proje sayısı"""
        with self.get_connection() as conn:
            result = conn.execute("""
                SELECT COUNT(*) FROM projects WHERE status = 'Devam Ediyor'
            """).fetchone()
            return result[0] if result else 0

# Global instance
db = DatabaseManager()