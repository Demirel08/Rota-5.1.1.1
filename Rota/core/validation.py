"""
EFES ROTA X - Merkezi Doğrulama (Validation) Modülü
Tüm form ve veri doğrulamaları burada tanımlanır.
"""

from typing import Tuple, Optional, List, Any, Dict
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum


class ValidationResult:
    """Doğrulama sonucu"""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, message: str):
        """Hata ekle"""
        self.errors.append(message)
        self.is_valid = False
    
    def merge(self, other: 'ValidationResult'):
        """Başka bir sonuçla birleştir"""
        if not other.is_valid:
            self.is_valid = False
            self.errors.extend(other.errors)
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        if self.is_valid:
            return "Geçerli"
        return "Hatalar: " + "; ".join(self.errors)


@dataclass
class ValidationRule:
    """Doğrulama kuralı"""
    field_name: str
    display_name: str
    required: bool = True
    min_value: float = None
    max_value: float = None
    min_length: int = None
    max_length: int = None
    pattern: str = None
    custom_validator: callable = None
    error_message: str = None


class Validator:
    """
    Merkezi doğrulayıcı
    
    Kullanım:
        from core.validation import validator, ValidationResult
        
        # Tek alan doğrula
        result = validator.validate_required("müşteri adı", customer_name)
        
        # Form doğrula
        result = validator.validate_order_form(form_data)
        
        # Özel doğrulama
        result = validator.validate_custom(data, rules)
    """
    
    # === TEMEL DOĞRULAMA METODLARI ===
    
    @staticmethod
    def validate_required(field_name: str, value: Any) -> ValidationResult:
        """Zorunlu alan kontrolü"""
        result = ValidationResult()
        
        if value is None or (isinstance(value, str) and not value.strip()):
            result.add_error(f"{field_name} boş olamaz")
        
        return result
    
    @staticmethod
    def validate_numeric(field_name: str, value: Any, 
                        min_val: float = None, max_val: float = None,
                        allow_zero: bool = True, allow_negative: bool = False) -> ValidationResult:
        """Sayısal değer doğrulama"""
        result = ValidationResult()
        
        if value is None or value == "":
            result.add_error(f"{field_name} boş olamaz")
            return result
        
        try:
            num = float(value)
            
            if not allow_negative and num < 0:
                result.add_error(f"{field_name} negatif olamaz")
            
            if not allow_zero and num == 0:
                result.add_error(f"{field_name} sıfır olamaz")
            
            if min_val is not None and num < min_val:
                result.add_error(f"{field_name} en az {min_val} olmalı")
            
            if max_val is not None and num > max_val:
                result.add_error(f"{field_name} en fazla {max_val} olabilir")
                
        except (ValueError, TypeError):
            result.add_error(f"{field_name} geçerli bir sayı değil")
        
        return result
    
    @staticmethod
    def validate_positive(field_name: str, value: Any) -> ValidationResult:
        """Pozitif sayı doğrulama"""
        return Validator.validate_numeric(
            field_name, value, 
            min_val=0.001, 
            allow_zero=False, 
            allow_negative=False
        )
    
    @staticmethod
    def validate_integer(field_name: str, value: Any, 
                        min_val: int = None, max_val: int = None) -> ValidationResult:
        """Tam sayı doğrulama"""
        result = ValidationResult()
        
        if value is None or value == "":
            result.add_error(f"{field_name} boş olamaz")
            return result
        
        try:
            num = int(float(value))
            
            if float(value) != num:
                result.add_error(f"{field_name} tam sayı olmalı")
            
            if min_val is not None and num < min_val:
                result.add_error(f"{field_name} en az {min_val} olmalı")
            
            if max_val is not None and num > max_val:
                result.add_error(f"{field_name} en fazla {max_val} olabilir")
                
        except (ValueError, TypeError):
            result.add_error(f"{field_name} geçerli bir tam sayı değil")
        
        return result
    
    @staticmethod
    def validate_string(field_name: str, value: str,
                       min_length: int = None, max_length: int = None,
                       allowed_chars: str = None) -> ValidationResult:
        """String doğrulama"""
        result = ValidationResult()
        
        if not isinstance(value, str):
            result.add_error(f"{field_name} metin olmalı")
            return result
        
        value = value.strip()
        
        if min_length is not None and len(value) < min_length:
            result.add_error(f"{field_name} en az {min_length} karakter olmalı")
        
        if max_length is not None and len(value) > max_length:
            result.add_error(f"{field_name} en fazla {max_length} karakter olabilir")
        
        if allowed_chars:
            invalid = set(value) - set(allowed_chars)
            if invalid:
                result.add_error(f"{field_name} geçersiz karakter içeriyor: {', '.join(invalid)}")
        
        return result
    
    @staticmethod
    def validate_date(field_name: str, value: Any,
                     min_date: date = None, max_date: date = None,
                     format: str = "%Y-%m-%d") -> ValidationResult:
        """Tarih doğrulama"""
        result = ValidationResult()
        
        if value is None or value == "":
            result.add_error(f"{field_name} boş olamaz")
            return result
        
        try:
            if isinstance(value, str):
                parsed_date = datetime.strptime(value, format).date()
            elif isinstance(value, datetime):
                parsed_date = value.date()
            elif isinstance(value, date):
                parsed_date = value
            else:
                result.add_error(f"{field_name} geçerli bir tarih değil")
                return result
            
            if min_date and parsed_date < min_date:
                result.add_error(f"{field_name} {min_date.strftime(format)} tarihinden önce olamaz")
            
            if max_date and parsed_date > max_date:
                result.add_error(f"{field_name} {max_date.strftime(format)} tarihinden sonra olamaz")
                
        except ValueError:
            result.add_error(f"{field_name} geçerli bir tarih formatında değil")
        
        return result
    
    @staticmethod
    def validate_future_date(field_name: str, value: Any) -> ValidationResult:
        """Gelecek tarih doğrulama"""
        return Validator.validate_date(field_name, value, min_date=date.today())
    
    @staticmethod
    def validate_choice(field_name: str, value: Any, 
                       choices: List[Any], case_sensitive: bool = True) -> ValidationResult:
        """Seçenek listesi doğrulama"""
        result = ValidationResult()
        
        if not case_sensitive and isinstance(value, str):
            value_lower = value.lower()
            choices_lower = [c.lower() if isinstance(c, str) else c for c in choices]
            if value_lower not in choices_lower:
                result.add_error(f"{field_name} geçerli bir seçenek değil")
        else:
            if value not in choices:
                result.add_error(f"{field_name} geçerli bir seçenek değil")
        
        return result
    
    # === CAM FABRİKASI ÖZEL DOĞRULAMALARI ===
    
    @staticmethod
    def validate_glass_dimensions(width: float, height: float,
                                 min_size: float = 50, max_size: float = 6000) -> ValidationResult:
        """Cam boyutları doğrulama"""
        result = ValidationResult()
        
        # En doğrulama
        width_result = Validator.validate_numeric(
            "En", width, 
            min_val=min_size, max_val=max_size,
            allow_zero=False, allow_negative=False
        )
        result.merge(width_result)
        
        # Boy doğrulama
        height_result = Validator.validate_numeric(
            "Boy", height, 
            min_val=min_size, max_val=max_size,
            allow_zero=False, allow_negative=False
        )
        result.merge(height_result)
        
        return result
    
    @staticmethod
    def validate_piece_count(count: Any) -> ValidationResult:
        """Parça adedi doğrulama"""
        return Validator.validate_integer("Adet", count, min_val=1, max_val=10000)
    
    @staticmethod
    def validate_route(route_str: str, available_stations: List[str] = None) -> ValidationResult:
        """Rota doğrulama"""
        result = ValidationResult()
        
        if not route_str or not route_str.strip():
            result.add_error("Rota boş olamaz")
            return result
        
        stations = [s.strip() for s in route_str.split(',')]
        
        if not stations:
            result.add_error("En az bir istasyon seçilmeli")
            return result
        
        # Kesim istasyonu kontrolü
        try:
            from core.factory_config import factory_config, StationGroup
            cutting_stations = factory_config.get_stations_by_group(StationGroup.KESIM)
            cutting_names = [s.name for s in cutting_stations]
            
            first_station = stations[0]
            if cutting_names and first_station not in cutting_names:
                result.add_error(f"İlk istasyon kesim istasyonu olmalı ({', '.join(cutting_names[:3])})")
        except ImportError:
            pass
        
        # Geçerli istasyon kontrolü
        if available_stations:
            invalid = [s for s in stations if s not in available_stations]
            if invalid:
                result.add_error(f"Geçersiz istasyonlar: {', '.join(invalid)}")
        
        # Tekrar kontrolü
        seen = set()
        duplicates = []
        for s in stations:
            if s in seen:
                duplicates.append(s)
            seen.add(s)
        
        if duplicates:
            result.add_error(f"Tekrarlanan istasyonlar: {', '.join(duplicates)}")
        
        return result
    
    @staticmethod
    def validate_capacity(capacity: Any, station_name: str = "") -> ValidationResult:
        """Kapasite doğrulama"""
        result = Validator.validate_numeric(
            f"{station_name} Kapasitesi" if station_name else "Kapasite",
            capacity,
            min_val=1, max_val=50000,
            allow_zero=False, allow_negative=False
        )
        return result
    
    # === FORM DOĞRULAMA ===
    
    @staticmethod
    def validate_order_form(data: Dict) -> ValidationResult:
        """Sipariş formu doğrulama"""
        result = ValidationResult()
        
        # Zorunlu alanlar
        required_fields = [
            ('customer', 'Müşteri'),
            ('deadline', 'Termin Tarihi'),
            ('route', 'Rota')
        ]
        
        for field, name in required_fields:
            if field not in data or not data[field]:
                result.add_error(f"{name} zorunludur")
        
        # Tarih doğrulama
        if 'deadline' in data and data['deadline']:
            date_result = Validator.validate_future_date("Termin Tarihi", data['deadline'])
            result.merge(date_result)
        
        # Rota doğrulama
        if 'route' in data and data['route']:
            route_result = Validator.validate_route(data['route'])
            result.merge(route_result)
        
        return result
    
    @staticmethod
    def validate_glass_item(data: Dict) -> ValidationResult:
        """Cam kalemi doğrulama"""
        result = ValidationResult()
        
        # Boyutlar
        width = data.get('width') or data.get('en')
        height = data.get('height') or data.get('boy')
        
        if width is not None and height is not None:
            dim_result = Validator.validate_glass_dimensions(
                float(width) if width else 0,
                float(height) if height else 0
            )
            result.merge(dim_result)
        
        # Adet
        count = data.get('count') or data.get('adet')
        if count is not None:
            count_result = Validator.validate_piece_count(count)
            result.merge(count_result)
        
        return result
    
    @staticmethod
    def validate_user_form(data: Dict, is_new: bool = True) -> ValidationResult:
        """Kullanıcı formu doğrulama"""
        result = ValidationResult()
        
        # Kullanıcı adı
        if 'username' in data:
            username_result = Validator.validate_string(
                "Kullanıcı Adı", data['username'],
                min_length=3, max_length=50,
                allowed_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
            )
            result.merge(username_result)
        
        # Şifre (yeni kullanıcı için zorunlu)
        if is_new:
            if 'password' not in data or not data['password']:
                result.add_error("Şifre zorunludur")
            elif len(data['password']) < 6:
                result.add_error("Şifre en az 6 karakter olmalı")
        
        # Rol
        if 'role' in data:
            role_result = Validator.validate_choice(
                "Rol", data['role'],
                ['admin', 'operator', 'viewer', 'manager']
            )
            result.merge(role_result)
        
        return result
    
    # === ÖZEL DOĞRULAMA ===
    
    @staticmethod
    def validate_custom(data: Dict, rules: List[ValidationRule]) -> ValidationResult:
        """Özel kurallarla doğrulama"""
        result = ValidationResult()
        
        for rule in rules:
            value = data.get(rule.field_name)
            
            # Zorunlu alan kontrolü
            if rule.required:
                if value is None or (isinstance(value, str) and not value.strip()):
                    result.add_error(rule.error_message or f"{rule.display_name} zorunludur")
                    continue
            elif value is None or value == "":
                continue
            
            # Min/Max değer kontrolü
            if rule.min_value is not None or rule.max_value is not None:
                num_result = Validator.validate_numeric(
                    rule.display_name, value,
                    min_val=rule.min_value, max_val=rule.max_value
                )
                result.merge(num_result)
            
            # Min/Max uzunluk kontrolü
            if rule.min_length is not None or rule.max_length is not None:
                str_result = Validator.validate_string(
                    rule.display_name, str(value),
                    min_length=rule.min_length, max_length=rule.max_length
                )
                result.merge(str_result)
            
            # Özel doğrulayıcı
            if rule.custom_validator:
                try:
                    custom_result = rule.custom_validator(value)
                    if isinstance(custom_result, ValidationResult):
                        result.merge(custom_result)
                    elif isinstance(custom_result, bool) and not custom_result:
                        result.add_error(rule.error_message or f"{rule.display_name} geçersiz")
                except Exception as e:
                    result.add_error(f"{rule.display_name} doğrulama hatası: {str(e)}")
        
        return result


# Singleton instance
validator = Validator()


# === YARDIMCI FONKSİYONLAR ===

def is_valid_number(value: Any, min_val: float = None, max_val: float = None) -> bool:
    """Hızlı sayı kontrolü"""
    return bool(validator.validate_numeric("", value, min_val, max_val))

def is_valid_date(value: Any) -> bool:
    """Hızlı tarih kontrolü"""
    return bool(validator.validate_date("", value))

def is_positive(value: Any) -> bool:
    """Pozitif mi?"""
    try:
        return float(value) > 0
    except:
        return False