"""
EFES ROTA X - Akıllı Asistan Motoru (Rule-Based Chatbot)
Yapay zeka kullanmadan, anahtar kelime ve veri analizi ile akıllı cevaplar üretir.
"""

import re
from datetime import datetime
try:
    from core.db_manager import db
except ImportError:
    db = None

class RotaBot:
    def __init__(self):
        self.bot_name = "Rota Asistan"
        
    def get_greeting(self):
        """Açılış mesajı ve hızlı butonlar"""
        return {
            "text": "Merhaba! Fabrika verilerine erişimim var. Size nasıl yardımcı olabilirim?",
            "buttons": [
                "📦 Sipariş Durumu Sorgula",
                "🏭 Makine Dolulukları",
                "⚠️ Geciken İşler",
                "📉 Kritik Stoklar",
                "🔥 Bugünün Fire Raporu"
            ]
        }

    def process_message(self, user_message):
        """Kullanıcı mesajını analiz eder ve cevap üretir"""
        msg = user_message.lower().strip()
        
        # 1. SİPARİŞ SORGULAMA (İçinde sipariş kodu veya 'nerede' geçiyorsa)
        # Örn: "S-2023 nerede?", "sipariş durumu"
        if "sipariş" in msg or "nerede" in msg or "durum" in msg or any(char.isdigit() for char in msg):
            return self._handle_order_query(msg)

        # 2. MAKİNE / İSTASYON DURUMU
        if "makine" in msg or "istasyon" in msg or "doluluk" in msg or "yoğunluk" in msg:
            return self._handle_machine_query()

        # 3. STOK SORGUSU
        if "stok" in msg or "depo" in msg or "cam var mı" in msg or "kritik" in msg:
            return self._handle_stock_query()

        # 4. FİRE / HATA RAPORU
        if "fire" in msg or "kırık" in msg or "hata" in msg:
            return self._handle_fire_query()
            
        # 5. GECİKEN İŞLER
        if "geciken" in msg or "yetişmeyen" in msg or "acil" in msg:
            return self._handle_overdue_query()

        # ANLAŞILAMADI
        return {
            "text": "Bunu tam anlayamadım. Sipariş numarası yazabilir veya aşağıdaki butonları kullanabilirsiniz.",
            "buttons": ["📦 Sipariş Sorgula", "🏭 Makineler", "📉 Stoklar"]
        }

    # =========================================================================
    # ALT MANTIKLAR (CEVAP ÜRETİCİLER)
    # =========================================================================

    def _handle_order_query(self, msg):
        """Sipariş durumu hakkında detaylı bilgi verir"""
        if not db: return {"text": "Veritabanı bağlantısı yok."}
        
        # Mesajın içindeki olası sipariş kodunu bul (Basit regex: kelimelerden biri kod olabilir)
        words = msg.upper().split()
        found_order = None
        
        # 1. Kelime kelime veritabanında ara
        for word in words:
            # Temizlik (noktalama işaretlerini kaldır)
            clean_word = re.sub(r'[^\w\s-]', '', word)
            if len(clean_word) > 2: # En az 3 karakterli kodlar
                order = db.get_order_by_code(clean_word)
                if order:
                    found_order = order
                    break
        
        if found_order:
            status = found_order.get('status', 'Bilinmiyor')
            customer = found_order.get('customer', 'Müşteri')
            date = found_order.get('date', 'Belirsiz')
            
            # Tarih analizi
            try:
                d_date = datetime.strptime(date, '%Y-%m-%d').date()
                today = datetime.now().date()
                days_left = (d_date - today).days
                
                if days_left < 0:
                    time_msg = f"⚠️ Sipariş {abs(days_left)} gün GECİKMİŞ!"
                elif days_left == 0:
                    time_msg = "🚨 Teslim tarihi BUGÜN."
                else:
                    time_msg = f"Teslime {days_left} gün var ({d_date.strftime('%d.%m.%Y')})."
            except:
                time_msg = f"Termin: {date}"

            # İstasyon ilerlemesi
            progress_msg = ""
            if status == "Üretimde":
                # db_manager'dan o anki istasyonu bulmaya çalışabiliriz
                # Şimdilik genel durum:
                progress_msg = "Şu an üretim hattında işlem görüyor."
            elif status == "Beklemede":
                progress_msg = "Henüz üretime başlanmadı."
            elif status == "Tamamlandı":
                progress_msg = "✅ Üretim bitti, sevkiyata hazır."
            elif status == "Sevk Edildi":
                progress_msg = "🚚 Müşteriye sevk edildi."

            response_text = (
                f"📄 **Sipariş:** {found_order['code']} ({customer})\n"
                f"📊 **Durum:** {status}\n"
                f"📅 **Zaman:** {time_msg}\n"
                f"ℹ️ {progress_msg}"
            )
            return {"text": response_text}
        
        else:
            return {
                "text": "Hangi siparişten bahsettiğinizi bulamadım. Lütfen sipariş kodunu (Örn: S-1234) yazın.",
                "buttons": ["Tüm Siparişleri Listele"]
            }

    def _handle_machine_query(self):
        """Makine doluluklarını yorumlar"""
        if not db: return {"text": "Veritabanı hatası."}
        
        loads = db.get_station_loads() # [{'name': 'TEMPER', 'percent': 80, 'status': 'Yoğun'}, ...]
        
        # En yoğun ve en boş makineleri bul
        busy_machines = [m for m in loads if m['percent'] > 80]
        free_machines = [m for m in loads if m['percent'] < 20]
        
        msg = "🏭 **Fabrika Durum Özeti:**\n\n"
        
        if busy_machines:
            msg += "🚨 **Yoğun İstasyonlar:**\n"
            for m in busy_machines:
                msg += f"- {m['name']}: %{m['percent']} Dolu\n"
        else:
            msg += "✅ Şu an kritik yoğunlukta makine yok.\n"
            
        if free_machines:
            msg += "\n🟢 **Boş İstasyonlar (Müsait):**\n"
            for m in free_machines[:3]: # İlk 3 tanesi
                msg += f"- {m['name']}\n"
                
        return {
            "text": msg,
            "buttons": ["Detaylı İş Yükü Tablosu"]
        }

    def _handle_stock_query(self):
        """Kritik stokları söyler"""
        if not db: return {"text": "Veri yok."}
        
        low_stocks = db.get_low_stocks()
        
        if not low_stocks:
            return {
                "text": "✅ Depo durumu iyi. Kritik seviyenin altında ürün görünmüyor.",
                "buttons": ["Stok Listesi"]
            }
        
        msg = f"⚠️ **Dikkat! {len(low_stocks)} ürün kritik seviyenin altında:**\n\n"
        for s in low_stocks[:5]:
            msg += f"- **{s['product_name']}**: {s['quantity_m2']:.0f} m² kaldı (Min: {s['min_limit']})\n"
            
        if len(low_stocks) > 5:
            msg += f"\n...ve {len(low_stocks)-5} ürün daha."
            
        return {
            "text": msg,
            "buttons": ["Stok Listesini Aç", "Stok Girişi Yap"]
        }

    def _handle_fire_query(self):
        """Fire durumunu raporlar"""
        if not db: return {"text": "Veri yok."}
        
        stats = db.get_dashboard_stats()
        fire_count = stats.get('fire', 0)
        
        # Detaylı fire analizi (Hangi istasyonda?)
        fire_data = db.get_fire_analysis_data()
        
        msg = f"🔥 **Toplam Fire:** {fire_count} adet parça.\n\n"
        
        if fire_data:
            msg += "**En Çok Fire Veren İstasyonlar:**\n"
            for f in fire_data[:3]:
                msg += f"- {f['station_name']}: {f['fire_adedi']} adet\n"
        else:
            msg += "Henüz istasyon bazlı fire kaydı yok."
            
        return {"text": msg}

    def _handle_overdue_query(self):
        """Geciken siparişleri listeler"""
        if not db: return {"text": "Veri yok."}
        
        all_orders = db.get_all_orders()
        today = datetime.now().date()
        overdue = []
        
        for o in all_orders:
            if o['status'] in ['Sevk Edildi', 'Tamamlandı']: continue
            if o['delivery_date']:
                try:
                    d_date = datetime.strptime(o['delivery_date'], '%Y-%m-%d').date()
                    if d_date < today:
                        overdue.append(o)
                except: pass
        
        if not overdue:
            return {"text": "🎉 Harika! Şu an geciken aktif sipariş yok."}
            
        msg = f"🚨 **{len(overdue)} adet geciken sipariş var:**\n\n"
        for o in overdue[:5]:
            days = (today - datetime.strptime(o['delivery_date'], '%Y-%m-%d').date()).days
            msg += f"- **{o['order_code']}** ({o['customer_name']}): {days} gün gecikme\n"
            
        return {
            "text": msg,
            "buttons": ["Karar Destek Ekranını Aç"]
        }

# Global nesne
bot = RotaBot()