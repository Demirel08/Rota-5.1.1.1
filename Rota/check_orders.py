"""
Siparis durumlarini kontrol et
"""

from core.db_manager import db

print("=== SIPARIS DURUMLARI ===\n")

orders = db.get_all_orders()

for order in orders:
    print(f"ID: {order['id']}")
    print(f"Kod: {order['order_code']}")
    print(f"Musteri: {order['customer_name']}")
    print(f"Durum: {order['status']}")
    print(f"Rota: {order['route']}")

    # Tamamlanan istasyonlar
    completed = db.get_completed_stations_list(order['id'])
    print(f"Tamamlanan istasyonlar: {', '.join(completed) if completed else 'Yok'}")
    print("-" * 50)
