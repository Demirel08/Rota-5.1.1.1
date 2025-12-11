import math
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from core.db_manager import db
except ImportError:
    pass

class SmartPlanner:
    """
    AKILLI PLANLAMA MOTORU v16 (VADE PENCERELİ HİBRİT OPTİMİZASYON) 🧠
    
    Yenilikler:
    - Look-ahead Window (Planlama Ufku): Sadece yakın tarihli işler batch yapılır.
    - Uzak tarihli işler, aynı cam türünde olsa bile öne çekilmez.
    """
    
    def __init__(self):
        self.FORECAST_DAYS = 30
        self.BATCH_BONUS_SCORE = 5  # Batch katkı puanı
        self.LOOKAHEAD_WINDOW = 30   # Gün: Sadece önümüzdeki 30 günün işlerini grupla (Batch yap)
        
        try:
            self.capacities = db.get_all_capacities()
            if not self.capacities: raise ValueError
        except:
            self.capacities = {} 
        
        self.station_order = [
            "INTERMAC", "LIVA KESIM", "LAMINE KESIM",
            "CNC RODAJ", "DOUBLEDGER", "ZIMPARA",
            "TESIR A1", "TESIR B1", "TESIR B1-1", "TESIR B1-2",
            "DELİK", "OYGU",
            "TEMPER A1", "TEMPER B1", "TEMPER BOMBE",
            "LAMINE A1", "ISICAM B1",
            "SEVKİYAT"
        ]

    def _parse_date(self, date_str):
        if not date_str: return datetime.max.date()
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return datetime.max.date()

    def optimize_production_sequence(self, orders):
        """
        Gelişmiş Fabrika Sıralama Algoritması
        """
        red_orders = []      # Acil / Gecikmiş (Dokunulmaz)
        green_orders = []    # Yakın tarihli Normal (Batch yapılacak)
        grey_orders = []     # Uzak tarihli Normal (Batch yapılmayacak, sona atılacak)
        
        today = datetime.now().date()
        window_limit = today + timedelta(days=self.LOOKAHEAD_WINDOW)
        
        # 1. AYRIŞTIRMA
        for order in orders:
            due_date = self._parse_date(order.get('delivery_date'))
            days_left = (due_date - today).days
            priority = order.get('priority', 'Normal')
            
            # Kriter 1: KIRMIZI HAT (Gecikmiş veya Çok Acil)
            if (days_left < 2) or (priority in ['Kritik', 'Çok Acil']):
                red_orders.append(order)
            
            # Kriter 2: YEŞİL HAT (Normal ama Vade Penceresi İçinde)
            elif due_date <= window_limit:
                green_orders.append(order)
                
            # Kriter 3: GRİ HAT (Çok İleri Tarihli)
            else:
                grey_orders.append(order)
                
        # --- KIRMIZI HAT SIRALAMASI ---
        # Kritik > Çok Acil > Tarih
        priority_map = {"Kritik": 0, "Çok Acil": 1, "Acil": 2, "Normal": 3}
        red_orders.sort(key=lambda x: (
            priority_map.get(x.get('priority', 'Normal'), 3),
            x.get('delivery_date', '9999-12-31')
        ))
        
        # --- YEŞİL HAT GRUPLAMASI (BATCHING) ---
        # Sadece yakın tarihli işleri grupluyoruz
        batches = defaultdict(list)
        for order in green_orders:
            key = (order.get('thickness'), order.get('product_type'))
            batches[key].append(order)
            
        scored_batches = []
        for key, batch_list in batches.items():
            # Batch Puanlama
            avg_days = sum([(self._parse_date(o.get('delivery_date')) - today).days for o in batch_list]) / len(batch_list)
            # Kalabalık gruplar öne, tarihi çok uzak olan gruplar biraz geriye
            batch_score = (len(batch_list) * self.BATCH_BONUS_SCORE) - (avg_days * 2)
            
            # Batch içi sıralama (Tarihe göre)
            batch_list.sort(key=lambda x: x.get('delivery_date', '9999-12-31'))
            
            scored_batches.append({
                'score': batch_score,
                'orders': batch_list
            })
            
        # Puanı yüksek olan batch en üste
        scored_batches.sort(key=lambda x: x['score'], reverse=True)
        
        # --- GRİ HAT SIRALAMASI ---
        # Uzak tarihli işleri sadece tarihe göre sırala
        grey_orders.sort(key=lambda x: x.get('delivery_date', '9999-12-31'))
        
        # 4. LİSTELERİ BİRLEŞTİR
        final_sequence = []
        
        # 1. Kırmızılar (Hemen yapılacaklar)
        final_sequence.extend(red_orders)
        
        # 2. Yeşiller (Verimli gruplanmış yakın işler)
        for batch in scored_batches:
            final_sequence.extend(batch['orders'])
            
        # 3. Griler (Zamanı gelince yapılacaklar)
        final_sequence.extend(grey_orders)
            
        return final_sequence

    def _run_simulation(self, new_order=None):
        # 1. Mevcut İşleri Çek
        active_orders = db.get_orders_by_status(["Beklemede", "Üretimde"])
        
        # 2. Yeni Siparişi Ekle
        if new_order:
            simulated_order = {
                'id': -1,
                'order_code': '>>> HESAPLANAN <<<',
                'customer_name': 'YENİ',
                'width': new_order.get('width', 0),
                'height': new_order.get('height', 0),
                'quantity': new_order.get('quantity', 0),
                'declared_total_m2': new_order.get('total_m2', 0),
                'thickness': new_order.get('thickness', 0),
                'product_type': new_order.get('product', ''),
                'route': new_order.get('route', ''),
                'priority': new_order.get('priority', 'Normal'),
                'delivery_date': new_order.get('date', '9999-12-31'),
                'is_new': True 
            }
            active_orders.append(simulated_order)

        # 3. YENİ OPTİMİZE SIRALAMA
        active_orders = self.optimize_production_sequence(active_orders)

        # 4. SİMÜLASYON DEĞİŞKENLERİ
        forecast_grid = {k: [0.0]*self.FORECAST_DAYS for k in self.capacities.keys()}
        loads_grid = {k: [0.0]*self.FORECAST_DAYS for k in self.capacities.keys()}
        details_grid = {k: [[] for _ in range(self.FORECAST_DAYS)] for k in self.capacities.keys()}
        machine_free_time = {k: 0.0 for k in self.capacities.keys()}
        
        order_finish_times = {} 
        target_finish_day = 0

        # 5. MOTOR ÇALIŞIYOR
        for order in active_orders:
            m2 = order.get('declared_total_m2', 0)
            if not m2 or m2 <= 0:
                w = order.get('width', 0)
                h = order.get('height', 0)
                q = order.get('quantity', 0)
                if w and h and q: m2 = (w * h * q) / 10000.0
            
            if m2 <= 0: continue
            
            total_qty = order.get('quantity', 1)
            route_str = order.get('route', '')
            route_steps = route_str.split(',')
            
            completed_stops = []
            if not order.get('is_new'):
                completed_stops = db.get_completed_stations_list(order['id'])
            
            current_order_ready_time = 0.0 
            
            for station in route_steps:
                station = station.strip()
                if station not in self.capacities: continue
                if station in completed_stops: continue 

                daily_cap = self.capacities[station]
                if daily_cap <= 0: daily_cap = 1
                
                done_qty = 0
                if not order.get('is_new'):
                    done_qty = db.get_station_progress(order['id'], station)
                
                remaining_ratio = 1.0 - (done_qty / total_qty)
                if remaining_ratio <= 0: continue

                remaining_m2 = m2 * remaining_ratio
                duration_days = remaining_m2 / daily_cap
                
                start_day = max(current_order_ready_time, machine_free_time[station])
                end_day = start_day + duration_days
                
                temp_start = start_day
                while temp_start < end_day:
                    day_idx = int(temp_start)
                    if day_idx >= self.FORECAST_DAYS: break 
                    
                    chunk_end = min(end_day, day_idx + 1)
                    work_amount = chunk_end - temp_start
                    
                    forecast_grid[station][day_idx] += (work_amount * 100)
                    loads_grid[station][day_idx] += (work_amount * daily_cap)
                    
                    info = {
                        "code": order['order_code'],
                        "customer": order.get('customer_name', 'Tahmini'),
                        "m2": remaining_m2,
                        "batch": f"{order.get('thickness')}mm",
                        "notes": order.get('notes', '')
                    }
                    exists = any(x['code'] == info['code'] for x in details_grid[station][day_idx])
                    if not exists:
                        details_grid[station][day_idx].append(info)
                    
                    temp_start = chunk_end
                
                machine_free_time[station] = end_day
                current_order_ready_time = end_day
            
            order_finish_times[order.get('order_code')] = current_order_ready_time
            if order.get('is_new'):
                target_finish_day = current_order_ready_time

        return forecast_grid, details_grid, loads_grid, target_finish_day, order_finish_times

    def calculate_forecast(self):
        try: self.capacities = db.get_all_capacities()
        except: pass
        grid, details, loads, _, _ = self._run_simulation(new_order=None)
        return grid, details, loads

    def calculate_impact(self, new_order_data):
        try: self.capacities = db.get_all_capacities()
        except: pass
        _, _, _, _, base_finish_times = self._run_simulation(new_order=None)
        _, _, _, target_day, new_finish_times = self._run_simulation(new_order=new_order_data)
        
        delayed_orders = []
        for code, base_time in base_finish_times.items():
            if code in new_finish_times:
                new_time = new_finish_times[code]
                if (new_time - base_time) > 0.1:
                    delayed_orders.append({
                        "code": code,
                        "delay": math.ceil(new_time - base_time),
                        "old_day": math.ceil(base_time),
                        "new_day": math.ceil(new_time)
                    })
        
        today = datetime.now()
        delivery_date = today + timedelta(days=math.ceil(target_day))
        return delivery_date, math.ceil(target_day), delayed_orders

    def fix_route_order(self, user_route_str):
        if not user_route_str: return ""
        selected = [s.strip() for s in user_route_str.split(',')]
        sorted_route = []
        for station in self.station_order:
            if station in selected:
                sorted_route.append(station)
        return ",".join(sorted_route)

planner = SmartPlanner()