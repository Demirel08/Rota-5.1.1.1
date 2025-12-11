"""
EFES ROTA X - Güvenlik Modülü
Şifre hashleme, doğrulama ve güvenlik yardımcıları
"""

import hashlib
import secrets
import os
from typing import Tuple, Optional
from datetime import datetime, timedelta

# PBKDF2 için parametreler
PBKDF2_ITERATIONS = 100000  # Yüksek iterasyon = daha güvenli
SALT_LENGTH = 32
HASH_LENGTH = 64


class PasswordManager:
    """
    Güvenli şifre yönetimi
    
    Kullanım:
        from core.security import password_manager
        
        # Şifre hash'le
        hashed = password_manager.hash_password("gizli123")
        
        # Şifre doğrula
        is_valid = password_manager.verify_password("gizli123", hashed)
        
        # Eski SHA256 hash'i kontrol et ve güncelle
        if password_manager.is_legacy_hash(stored_hash):
            new_hash = password_manager.upgrade_legacy_hash(password, stored_hash)
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Şifreyi PBKDF2 ile hash'le
        
        Returns:
            "pbkdf2$iterations$salt$hash" formatında string
        """
        salt = secrets.token_hex(SALT_LENGTH)
        
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            PBKDF2_ITERATIONS,
            dklen=HASH_LENGTH
        )
        
        hash_hex = hash_bytes.hex()
        
        return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${hash_hex}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """
        Şifreyi doğrula
        
        Args:
            password: Kullanıcının girdiği şifre
            stored_hash: Veritabanındaki hash
            
        Returns:
            Şifre doğru ise True
        """
        if not stored_hash or not password:
            return False
        
        # PBKDF2 hash mi kontrol et
        if stored_hash.startswith('pbkdf2$'):
            return PasswordManager._verify_pbkdf2(password, stored_hash)
        
        # Eski SHA256 hash (geriye uyumluluk)
        return PasswordManager._verify_legacy(password, stored_hash)
    
    @staticmethod
    def _verify_pbkdf2(password: str, stored_hash: str) -> bool:
        """PBKDF2 hash doğrula"""
        try:
            parts = stored_hash.split('$')
            if len(parts) != 4:
                return False
            
            _, iterations, salt, hash_hex = parts
            iterations = int(iterations)
            
            # Aynı parametrelerle hash oluştur
            test_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations,
                dklen=HASH_LENGTH
            )
            
            # Timing attack'a karşı güvenli karşılaştırma
            return secrets.compare_digest(test_hash.hex(), hash_hex)
            
        except Exception:
            return False
    
    @staticmethod
    def _verify_legacy(password: str, stored_hash: str) -> bool:
        """Eski SHA256 hash doğrula (geriye uyumluluk)"""
        try:
            test_hash = hashlib.sha256(password.encode()).hexdigest()
            return secrets.compare_digest(test_hash, stored_hash)
        except Exception:
            return False
    
    @staticmethod
    def is_legacy_hash(stored_hash: str) -> bool:
        """Hash eski format mı?"""
        if not stored_hash:
            return False
        return not stored_hash.startswith('pbkdf2$')
    
    @staticmethod
    def upgrade_legacy_hash(password: str, legacy_hash: str) -> Optional[str]:
        """
        Eski hash'i yeni formata güncelle
        
        Şifre doğruysa yeni PBKDF2 hash döner
        """
        if PasswordManager._verify_legacy(password, legacy_hash):
            return PasswordManager.hash_password(password)
        return None
    
    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """Geçici şifre oluştur"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def check_password_strength(password: str) -> Tuple[bool, list]:
        """
        Şifre güçlülüğünü kontrol et
        
        Returns:
            (is_strong, list_of_issues)
        """
        issues = []
        
        if len(password) < 8:
            issues.append("En az 8 karakter olmalı")
        
        if not any(c.isupper() for c in password):
            issues.append("En az 1 büyük harf içermeli")
        
        if not any(c.islower() for c in password):
            issues.append("En az 1 küçük harf içermeli")
        
        if not any(c.isdigit() for c in password):
            issues.append("En az 1 rakam içermeli")
        
        return (len(issues) == 0, issues)


class SessionManager:
    """
    Oturum yönetimi
    
    Kullanım:
        from core.security import session_manager
        
        # Oturum oluştur
        token = session_manager.create_session(user_id, username, role)
        
        # Oturum doğrula
        session = session_manager.validate_session(token)
        
        # Oturum sonlandır
        session_manager.end_session(token)
    """
    
    def __init__(self):
        self._sessions = {}
        self._session_timeout = timedelta(hours=8)  # 8 saat
    
    def create_session(self, user_id: int, username: str, role: str) -> str:
        """Yeni oturum oluştur"""
        # Token oluştur
        token = secrets.token_urlsafe(32)
        
        # Oturumu kaydet
        self._sessions[token] = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        
        # Eski oturumları temizle
        self._cleanup_expired()
        
        return token
    
    def validate_session(self, token: str) -> Optional[dict]:
        """Oturumu doğrula"""
        if not token or token not in self._sessions:
            return None
        
        session = self._sessions[token]
        
        # Zaman aşımı kontrolü
        if datetime.now() - session['last_activity'] > self._session_timeout:
            del self._sessions[token]
            return None
        
        # Son aktiviteyi güncelle
        session['last_activity'] = datetime.now()
        
        return session
    
    def end_session(self, token: str) -> bool:
        """Oturumu sonlandır"""
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False
    
    def end_all_sessions(self, user_id: int):
        """Kullanıcının tüm oturumlarını sonlandır"""
        tokens_to_remove = [
            token for token, session in self._sessions.items()
            if session['user_id'] == user_id
        ]
        for token in tokens_to_remove:
            del self._sessions[token]
    
    def _cleanup_expired(self):
        """Süresi dolmuş oturumları temizle"""
        now = datetime.now()
        expired = [
            token for token, session in self._sessions.items()
            if now - session['last_activity'] > self._session_timeout
        ]
        for token in expired:
            del self._sessions[token]
    
    def get_active_sessions_count(self) -> int:
        """Aktif oturum sayısı"""
        self._cleanup_expired()
        return len(self._sessions)


class InputValidator:
    """
    Girdi doğrulama yardımcıları
    
    SQL injection ve XSS önleme için
    """
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        """String'i temizle"""
        if not value:
            return ""
        
        # Uzunluk sınırla
        value = value[:max_length]
        
        # Tehlikeli karakterleri escape et
        value = value.replace("'", "''")  # SQL için
        value = value.replace("<", "&lt;")  # XSS için
        value = value.replace(">", "&gt;")
        
        return value.strip()
    
    @staticmethod
    def validate_numeric(value, min_val: float = None, max_val: float = None) -> Tuple[bool, Optional[float]]:
        """Sayısal değer doğrula"""
        try:
            num = float(value)
            
            if min_val is not None and num < min_val:
                return False, None
            if max_val is not None and num > max_val:
                return False, None
            
            return True, num
        except (ValueError, TypeError):
            return False, None
    
    @staticmethod
    def validate_date(value: str, format: str = "%Y-%m-%d") -> Tuple[bool, Optional[datetime]]:
        """Tarih doğrula"""
        try:
            date = datetime.strptime(value, format)
            return True, date
        except (ValueError, TypeError):
            return False, None
    
    @staticmethod
    def validate_email(value: str) -> bool:
        """E-posta formatı doğrula"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value or ""))
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """Dosya adı güvenli mi?"""
        if not filename:
            return False
        
        # Tehlikeli karakterler
        dangerous = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        return not any(d in filename for d in dangerous)


# Singleton instances
password_manager = PasswordManager()
session_manager = SessionManager()
input_validator = InputValidator()


# === YARDIMCI FONKSİYONLAR ===

def hash_password(password: str) -> str:
    """Geriye uyumluluk için"""
    return password_manager.hash_password(password)

def verify_password(password: str, stored_hash: str) -> bool:
    """Geriye uyumluluk için"""
    return password_manager.verify_password(password, stored_hash)

def sanitize(value: str) -> str:
    """Geriye uyumluluk için"""
    return input_validator.sanitize_string(value)