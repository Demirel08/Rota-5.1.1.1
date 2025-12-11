"""
Veritabanı Bakım Scripti
Tüm siparişlerin durumlarını kontrol edip günceller
"""

from core.db_manager import db

print("=== SİPARİŞ DURUM GÜNCELLEMESİ ===")
print("Tüm siparişlerin durumları kontrol ediliyor...")

updated = db.update_all_order_statuses()

print(f"\n✅ Güncelleme tamamlandı!")
print(f"📊 {updated} sipariş güncellendi.")

# Kontrol için durumları göster
print("\n📋 Sipariş Durumları:")
orders = db.get_all_orders()
status_counts = {}
for order in orders:
    status = order['status']
    status_counts[status] = status_counts.get(status, 0) + 1

for status, count in status_counts.items():
    print(f"   {status}: {count} adet")

print("\n✨ İşlem tamamlandı!")
