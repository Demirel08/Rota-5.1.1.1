"""
EFES ROTA - Tema Uyumluluk Kontrol Script'i
Tüm Python dosyalarında eski tema değişkenlerini bulur
"""

import os
import re

# Aranacak eski değişkenler
OLD_VARS = [
    'TEXT_DARK',
    'TEXT_GREY',
]

# Kontrol edilecek klasörler
FOLDERS = ['views', 'ui']

def check_file(filepath):
    """Bir dosyada eski tema değişkenlerini kontrol et"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for old_var in OLD_VARS:
                if f'Theme.{old_var}' in line and 'Theme.TEXT_DARK' not in line.replace(' ', ''):
                    # Yorum satırı değilse
                    if not line.strip().startswith('#'):
                        issues.append({
                            'line': line_num,
                            'var': old_var,
                            'content': line.strip()
                        })
    except Exception as e:
        print(f"❌ Dosya okunamadı {filepath}: {e}")
    
    return issues

def scan_directory(base_path='.'):
    """Tüm klasörleri tara"""
    
    print("🔍 EFES ROTA - Tema Uyumluluk Kontrolü")
    print("=" * 60)
    print()
    
    total_issues = 0
    files_with_issues = []
    
    for folder in FOLDERS:
        folder_path = os.path.join(base_path, folder)
        
        if not os.path.exists(folder_path):
            print(f"⚠️  Klasör bulunamadı: {folder}")
            continue
        
        print(f"📂 {folder}/ klasörü kontrol ediliyor...")
        
        for filename in os.listdir(folder_path):
            if filename.endswith('.py'):
                filepath = os.path.join(folder_path, filename)
                issues = check_file(filepath)
                
                if issues:
                    files_with_issues.append(filename)
                    print(f"\n  ❌ {filename}")
                    for issue in issues:
                        print(f"     Satır {issue['line']}: Theme.{issue['var']}")
                        print(f"     → {issue['content'][:80]}")
                    total_issues += len(issues)
        
        print()
    
    print("=" * 60)
    
    if total_issues == 0:
        print("✅ Harika! Hiçbir dosyada eski tema değişkeni bulunamadı!")
        print("✅ Tüm dosyalar yeni tema ile uyumlu.")
    else:
        print(f"⚠️  Toplam {total_issues} adet eski tema kullanımı bulundu!")
        print(f"⚠️  {len(files_with_issues)} dosya güncellenmeli:")
        print()
        for filename in files_with_issues:
            print(f"   • {filename}")
        print()
        print("💡 Bu dosyaları VIEW_GUNCELLEME_REHBERI.md'ye göre güncelleyin.")
        print()
        print("🔄 Hızlı düzeltme:")
        print("   1. TEXT_DARK → TEXT_PRIMARY")
        print("   2. TEXT_GREY → TEXT_SECONDARY")
    
    print()
    return total_issues

if __name__ == "__main__":
    import sys
    
    # Çalıştırma dizinini al
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = '.'
    
    issues = scan_directory(base_path)
    
    if issues > 0:
        sys.exit(1)  # Hata kodu döndür
    else:
        sys.exit(0)  # Başarı