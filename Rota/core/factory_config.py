"""
EFES ROTA X - Merkezi Fabrika Konfigürasyonu
Tüm istasyon isimleri, grupları ve varsayılan kapasiteler burada tanımlanır.
Ayarlar ekranından değiştirilebilir, veritabanında saklanır.

Bu dosya sayesinde:
- Farklı fabrikalar kendi istasyon isimlerini kullanabilir
- Yeni istasyon eklemek/silmek tek yerden yapılır
- Tüm modüller tutarlı veri kullanır
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class StationGroup(Enum):
    """İstasyon grupları"""
    KESIM = "Kesim"
    ISLEME = "İşleme"
    YUZEY = "Yüzey İşleme"
    TEMPER = "Temperleme"
    BIRLESTIRME = "Birleştirme"
    SEVKIYAT = "Sevkiyat"


@dataclass
class StationInfo:
    """Tek bir istasyon bilgisi"""
    name: str                           # İstasyon adı
    group: StationGroup                 # Hangi gruba ait
    default_capacity: int               # Varsayılan günlük kapasite (m²)
    order_index: int                    # Sıralama indeksi
    is_active: bool = True              # Aktif mi?
    alternatives: List[str] = field(default_factory=list)  # Alternatif istasyonlar
    is_batch_station: bool = False      # Batch işlem yapılan istasyon mu?
    show_in_shipping: bool = False      # Sevkiyat ekranında gösterilsin mi?
    color_code: str = "#3498DB"         # Renk kodu (Gantt için)


class FactoryConfig:
    """
    Merkezi Fabrika Konfigürasyonu
    
    Kullanım:
        from core.factory_config import factory_config
        
        # Tüm istasyonları al
        stations = factory_config.get_all_stations()
        
        # Belirli bir grubun istasyonlarını al
        kesim = factory_config.get_stations_by_group(StationGroup.KESIM)
        
        # İstasyon sırasını al
        order = factory_config.get_station_order()
    """
    
    # Varsayılan istasyon tanımları
    DEFAULT_STATIONS: Dict[str, StationInfo] = {
        # KESIM GRUBU
        "INTERMAC": StationInfo(
            name="INTERMAC",
            group=StationGroup.KESIM,
            default_capacity=800,
            order_index=1,
            alternatives=["LIVA KESIM"],
            color_code="#2ECC71"
        ),
        "LIVA KESIM": StationInfo(
            name="LIVA KESIM",
            group=StationGroup.KESIM,
            default_capacity=800,
            order_index=2,
            alternatives=["INTERMAC"],
            color_code="#27AE60"
        ),
        "LAMINE KESIM": StationInfo(
            name="LAMINE KESIM",
            group=StationGroup.KESIM,
            default_capacity=600,
            order_index=3,
            color_code="#1ABC9C"
        ),
        
        # İŞLEME GRUBU
        "CNC RODAJ": StationInfo(
            name="CNC RODAJ",
            group=StationGroup.ISLEME,
            default_capacity=100,
            order_index=10,
            color_code="#3498DB"
        ),
        "DOUBLEDGER": StationInfo(
            name="DOUBLEDGER",
            group=StationGroup.ISLEME,
            default_capacity=400,
            order_index=11,
            color_code="#2980B9"
        ),
        "ZIMPARA": StationInfo(
            name="ZIMPARA",
            group=StationGroup.ISLEME,
            default_capacity=300,
            order_index=12,
            color_code="#1F618D"
        ),
        
        # YÜZEY İŞLEME GRUBU
        "TESIR A1": StationInfo(
            name="TESIR A1",
            group=StationGroup.YUZEY,
            default_capacity=400,
            order_index=20,
            alternatives=["TESIR B1", "TESIR B1-1", "TESIR B1-2"],
            color_code="#9B59B6"
        ),
        "TESIR B1": StationInfo(
            name="TESIR B1",
            group=StationGroup.YUZEY,
            default_capacity=400,
            order_index=21,
            alternatives=["TESIR A1", "TESIR B1-1", "TESIR B1-2"],
            color_code="#8E44AD"
        ),
        "TESIR B1-1": StationInfo(
            name="TESIR B1-1",
            group=StationGroup.YUZEY,
            default_capacity=400,
            order_index=22,
            alternatives=["TESIR A1", "TESIR B1", "TESIR B1-2"],
            color_code="#7D3C98"
        ),
        "TESIR B1-2": StationInfo(
            name="TESIR B1-2",
            group=StationGroup.YUZEY,
            default_capacity=400,
            order_index=23,
            alternatives=["TESIR A1", "TESIR B1", "TESIR B1-1"],
            color_code="#6C3483"
        ),
        "DELIK": StationInfo(
            name="DELIK",
            group=StationGroup.YUZEY,
            default_capacity=200,
            order_index=24,
            color_code="#A569BD"
        ),
        "OYGU": StationInfo(
            name="OYGU",
            group=StationGroup.YUZEY,
            default_capacity=200,
            order_index=25,
            color_code="#BB8FCE"
        ),
        
        # TEMPERLEME GRUBU
        "TEMPER A1": StationInfo(
            name="TEMPER A1",
            group=StationGroup.TEMPER,
            default_capacity=550,
            order_index=30,
            alternatives=["TEMPER B1"],
            is_batch_station=True,
            color_code="#E74C3C"
        ),
        "TEMPER B1": StationInfo(
            name="TEMPER B1",
            group=StationGroup.TEMPER,
            default_capacity=750,
            order_index=31,
            alternatives=["TEMPER A1"],
            is_batch_station=True,
            color_code="#C0392B"
        ),
        "TEMPER BOMBE": StationInfo(
            name="TEMPER BOMBE",
            group=StationGroup.TEMPER,
            default_capacity=300,
            order_index=32,
            is_batch_station=True,
            color_code="#A93226"
        ),
        
        # BİRLEŞTİRME GRUBU
        "LAMINE A1": StationInfo(
            name="LAMINE A1",
            group=StationGroup.BIRLESTIRME,
            default_capacity=250,
            order_index=40,
            color_code="#F39C12"
        ),
        "ISICAM B1": StationInfo(
            name="ISICAM B1",
            group=StationGroup.BIRLESTIRME,
            default_capacity=500,
            order_index=41,
            color_code="#E67E22"
        ),
        "KUMLAMA": StationInfo(
            name="KUMLAMA",
            group=StationGroup.BIRLESTIRME,
            default_capacity=300,
            order_index=42,
            color_code="#D35400"
        ),
        
        # SEVKİYAT
        "SEVKIYAT": StationInfo(
            name="SEVKIYAT",
            group=StationGroup.SEVKIYAT,
            default_capacity=5000,
            order_index=99,
            show_in_shipping=True,
            color_code="#34495E"
        ),
    }
    
    def __init__(self):
        self._stations: Dict[str, StationInfo] = {}
        self._db = None
        self._load_defaults()
    
    def _load_defaults(self):
        """Varsayılan istasyonları yükle"""
        self._stations = self.DEFAULT_STATIONS.copy()
    
    def set_database(self, db_manager):
        """Veritabanı bağlantısını ayarla ve özelleştirilmiş ayarları yükle"""
        self._db = db_manager
        self._load_from_database()
    
    def _load_from_database(self):
        """Veritabanından özelleştirilmiş istasyon ayarlarını yükle"""
        if not self._db:
            return
        
        try:
            with self._db.get_connection() as conn:
                # stations tablosu var mı kontrol et
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='stations'
                """)
                if not cursor.fetchone():
                    self._create_stations_table(conn)
                    return
                
                # Özelleştirilmiş istasyonları yükle
                rows = conn.execute("""
                    SELECT name, display_name, group_name, capacity, 
                           order_index, is_active, alternatives, color_code
                    FROM stations
                """).fetchall()
                
                for row in rows:
                    name = row['name']
                    if name in self._stations:
                        # Mevcut istasyonu güncelle
                        station = self._stations[name]
                        station.default_capacity = row['capacity']
                        station.order_index = row['order_index']
                        station.is_active = bool(row['is_active'])
                        station.color_code = row['color_code'] or station.color_code
                        if row['alternatives']:
                            station.alternatives = json.loads(row['alternatives'])
                    else:
                        # Yeni istasyon ekle (kullanıcı tanımlı)
                        group = StationGroup[row['group_name']] if row['group_name'] else StationGroup.ISLEME
                        self._stations[name] = StationInfo(
                            name=name,
                            group=group,
                            default_capacity=row['capacity'],
                            order_index=row['order_index'],
                            is_active=bool(row['is_active']),
                            alternatives=json.loads(row['alternatives']) if row['alternatives'] else [],
                            color_code=row['color_code'] or "#3498DB"
                        )
                        
        except Exception as e:
            print(f"İstasyon yükleme hatası: {e}")
    
    def _create_stations_table(self, conn):
        """stations tablosunu oluştur ve varsayılan değerleri ekle"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT,
                group_name TEXT,
                capacity INTEGER DEFAULT 500,
                order_index INTEGER DEFAULT 50,
                is_active INTEGER DEFAULT 1,
                alternatives TEXT,
                color_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Varsayılan istasyonları ekle
        for name, info in self.DEFAULT_STATIONS.items():
            conn.execute("""
                INSERT OR IGNORE INTO stations 
                (name, display_name, group_name, capacity, order_index, is_active, alternatives, color_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, 
                info.name,
                info.group.name,
                info.default_capacity,
                info.order_index,
                1 if info.is_active else 0,
                json.dumps(info.alternatives),
                info.color_code
            ))
    
    # === GETTER METODLARI ===
    
    def get_all_stations(self, active_only: bool = True) -> Dict[str, StationInfo]:
        """Tüm istasyonları döndür"""
        if active_only:
            return {k: v for k, v in self._stations.items() if v.is_active}
        return self._stations.copy()
    
    def get_station(self, name: str) -> Optional[StationInfo]:
        """Belirli bir istasyonu döndür"""
        return self._stations.get(name)
    
    def get_stations_by_group(self, group: StationGroup, active_only: bool = True) -> List[StationInfo]:
        """Belirli bir grubun istasyonlarını döndür"""
        stations = [s for s in self._stations.values() if s.group == group]
        if active_only:
            stations = [s for s in stations if s.is_active]
        return sorted(stations, key=lambda x: x.order_index)
    
    def get_station_order(self, include_shipping: bool = False) -> List[str]:
        """Sıralı istasyon listesi döndür"""
        stations = [s for s in self._stations.values() if s.is_active]
        if not include_shipping:
            stations = [s for s in stations if s.group != StationGroup.SEVKIYAT]
        return [s.name for s in sorted(stations, key=lambda x: x.order_index)]
    
    def get_station_groups(self) -> Dict[str, List[str]]:
        """Grup bazlı istasyon listesi döndür"""
        result = {}
        for group in StationGroup:
            stations = self.get_stations_by_group(group)
            if stations:
                result[group.value] = [s.name for s in stations]
        return result
    
    def get_alternatives(self, station_name: str) -> List[str]:
        """Bir istasyonun alternatiflerini döndür"""
        station = self._stations.get(station_name)
        if station:
            return [alt for alt in station.alternatives if alt in self._stations and self._stations[alt].is_active]
        return []
    
    def get_batch_stations(self) -> List[str]:
        """Batch işlem yapılan istasyonları döndür"""
        return [s.name for s in self._stations.values() if s.is_batch_station and s.is_active]
    
    def get_capacities(self) -> Dict[str, int]:
        """Tüm kapasiteleri döndür (eski kod ile uyumluluk için)"""
        return {name: info.default_capacity for name, info in self._stations.items() if info.is_active}
    
    def get_capacity(self, station_name: str) -> int:
        """Belirli bir istasyonun kapasitesini döndür"""
        station = self._stations.get(station_name)
        return station.default_capacity if station else 500
    
    def get_station_index(self, station_name: str) -> int:
        """İstasyonun sıra indeksini döndür"""
        station = self._stations.get(station_name)
        return station.order_index if station else 999
    
    def is_cutting_station(self, station_name: str) -> bool:
        """Kesim istasyonu mu?"""
        station = self._stations.get(station_name)
        return station.group == StationGroup.KESIM if station else False
    
    def should_show_station(self, station_name: str) -> bool:
        """Bu istasyon üretim takipte gösterilmeli mi?"""
        station = self._stations.get(station_name)
        if not station:
            return False
        return station.is_active and station.group != StationGroup.SEVKIYAT
    
    # === SETTER METODLARI ===
    
    def update_capacity(self, station_name: str, new_capacity: int) -> bool:
        """İstasyon kapasitesini güncelle"""
        if station_name not in self._stations:
            return False
        
        self._stations[station_name].default_capacity = new_capacity
        
        if self._db:
            try:
                with self._db.get_connection() as conn:
                    conn.execute("""
                        UPDATE stations SET capacity = ? WHERE name = ?
                    """, (new_capacity, station_name))
                return True
            except Exception as e:
                print(f"Kapasite güncelleme hatası: {e}")
                return False
        return True
    
    def update_station(self, station_name: str, **kwargs) -> bool:
        """İstasyon bilgilerini güncelle"""
        if station_name not in self._stations:
            return False
        
        station = self._stations[station_name]
        
        # Güncelle
        for key, value in kwargs.items():
            if hasattr(station, key):
                setattr(station, key, value)
        
        # Veritabanına kaydet
        if self._db:
            try:
                with self._db.get_connection() as conn:
                    conn.execute("""
                        UPDATE stations SET 
                            capacity = ?,
                            order_index = ?,
                            is_active = ?,
                            alternatives = ?,
                            color_code = ?
                        WHERE name = ?
                    """, (
                        station.default_capacity,
                        station.order_index,
                        1 if station.is_active else 0,
                        json.dumps(station.alternatives),
                        station.color_code,
                        station_name
                    ))
                return True
            except Exception as e:
                print(f"İstasyon güncelleme hatası: {e}")
                return False
        return True
    
    def add_station(self, name: str, group: StationGroup, capacity: int = 500, 
                    order_index: int = 50, **kwargs) -> bool:
        """Yeni istasyon ekle"""
        if name in self._stations:
            return False
        
        station = StationInfo(
            name=name,
            group=group,
            default_capacity=capacity,
            order_index=order_index,
            **kwargs
        )
        
        self._stations[name] = station
        
        if self._db:
            try:
                with self._db.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO stations 
                        (name, display_name, group_name, capacity, order_index, is_active, alternatives, color_code)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name, name, group.name, capacity, order_index, 
                        1, json.dumps(station.alternatives), station.color_code
                    ))
                return True
            except Exception as e:
                print(f"İstasyon ekleme hatası: {e}")
                return False
        return True
    
    def remove_station(self, station_name: str) -> bool:
        """İstasyonu deaktif et (silme yerine)"""
        return self.update_station(station_name, is_active=False)
    
    def fix_route_order(self, route_str: str) -> str:
        """Rotayı fabrika sırasına göre düzelt"""
        if not route_str:
            return ""
        
        selected = [s.strip() for s in route_str.split(',') if s.strip()]
        station_order = self.get_station_order(include_shipping=True)
        
        sorted_route = []
        for station in station_order:
            if station in selected:
                sorted_route.append(station)
        
        # Bilinmeyen istasyonları sona ekle
        for station in selected:
            if station not in sorted_route:
                sorted_route.append(station)
        
        return ",".join(sorted_route)
    
    def refresh(self):
        """Konfigürasyonu yeniden yükle"""
        self._load_defaults()
        if self._db:
            self._load_from_database()


# Singleton instance
factory_config = FactoryConfig()


# === GERİYE UYUMLULUK İÇİN YARDIMCI FONKSİYONLAR ===

def get_station_order() -> List[str]:
    """Eski kod ile uyumluluk için"""
    return factory_config.get_station_order()

def get_all_capacities() -> Dict[str, int]:
    """Eski kod ile uyumluluk için"""
    return factory_config.get_capacities()

def get_station_groups() -> Dict[str, List[str]]:
    """Eski kod ile uyumluluk için"""
    return factory_config.get_station_groups()

def is_cutting_station(station_name: str) -> bool:
    """Eski kod ile uyumluluk için"""
    return factory_config.is_cutting_station(station_name)