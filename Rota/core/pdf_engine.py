from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime, timedelta

class PDFEngine:
    """
    EFES ROTA - Raporlama Motoru
    DÜZELTİLMİŞ VERSİYON: Dinamik Makine Listesi ✅
    """
    
    def __init__(self, filename="Rapor.pdf"):
        self.filename = filename
        self.register_fonts()
        
    def register_fonts(self):
        """Türkçe karakterler için font ayarı"""
        try:
            # Windows Arial fontunu dene
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                pdfmetrics.registerFont(TTFont('Arial-Bold', "C:\\Windows\\Fonts\\arialbd.ttf"))
                self.font_normal = "Arial"
                self.font_bold = "Arial-Bold"
            else:
                self.font_normal = "Helvetica"
                self.font_bold = "Helvetica-Bold"
        except:
            self.font_normal = "Helvetica"
            self.font_bold = "Helvetica-Bold"

    def generate_weekly_schedule_pdf(self, schedule_data, station_list=None):
        """
        Haftalık planı PDF'e döker.
        schedule_data: { 'INTERMAC': [ [Gun0], [Gun1]... ] }
        station_list: ['INTERMAC', 'TEMPER A1'...] (Sıralı makine listesi)
        """
        doc = SimpleDocTemplate(self.filename, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Özel Stiller
        style_h1 = ParagraphStyle('H1', parent=styles['Title'], fontName=self.font_bold, fontSize=16, spaceAfter=10, textColor=colors.darkblue)
        style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName=self.font_bold, fontSize=12, spaceBefore=12, spaceAfter=6, textColor=colors.black, backColor=colors.lightgrey, borderPadding=5)
        style_cell_normal = ParagraphStyle('CellN', parent=styles['Normal'], fontName=self.font_normal, fontSize=8, leading=10)
        style_cell_bold = ParagraphStyle('CellB', parent=styles['Normal'], fontName=self.font_bold, fontSize=9, leading=10)

        # Başlık
        elements.append(Paragraph("HAFTALIK ÜRETİM İŞ EMRİ LİSTESİ", style_h1))
        elements.append(Paragraph(f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", style_cell_normal))
        elements.append(Spacer(1, 10))

        today = datetime.now()
        tr_days = ["PAZARTESİ", "SALI", "ÇARŞAMBA", "PERŞEMBE", "CUMA", "CUMARTESİ", "PAZAR"]
        
        # Eğer makine listesi gelmediyse, veriden çıkar ve sırala
        if not station_list:
            station_list = sorted(list(schedule_data.keys()))

        # 7 Gün İçin Döngü
        for day_idx in range(7):
            day_date = today + timedelta(days=day_idx)
            day_title = f"{tr_days[day_date.weekday()]} - {day_date.strftime('%d.%m.%Y')}"
            
            # Gün Başlığı
            elements.append(Paragraph(day_title, style_h2))
            
            # Tablo Verisi Hazırlığı
            # Header
            table_data = [[
                Paragraph('<b>İSTASYON</b>', style_cell_normal),
                Paragraph('<b>PLANLANAN İŞLER</b>', style_cell_normal)
            ]]
            
            has_data_for_day = False
            
            for machine in station_list:
                machine_key = machine  # Verideki anahtar (Örn: INTERMAC)
                
                orders = []
                try:
                    if machine_key in schedule_data:
                        if len(schedule_data[machine_key]) > day_idx:
                            orders = schedule_data[machine_key][day_idx]
                except:
                    orders = []
                
                if orders:
                    has_data_for_day = True
                    job_lines = []
                    for o in orders:
                        # o: {'code':..., 'customer':..., 'm2':..., 'batch':...}
                        # Satır formatı: <b>KOD</b> - Müşteri (m2) [Batch]
                        code = o.get('code', '?')
                        cust = o.get('customer', '?')[:15] # Çok uzunsa kes
                        m2 = o.get('m2', 0)
                        batch = o.get('batch', '')
                        
                        line = f"<b>{code}</b> - {cust} ({m2:.0f}m²) <font color='blue'>{batch}</font>"
                        job_lines.append(line)
                    
                    content = "<br/>".join(job_lines)
                    
                    # Tabloya satır ekle
                    table_data.append([
                        Paragraph(machine, style_cell_bold),
                        Paragraph(content, style_cell_normal)
                    ])

            if has_data_for_day:
                # Tablo Stili
                t = Table(table_data, colWidths=[120, 380])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke), # Header arkaplan
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),       # Izgara çizgileri
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),                # Üstten hizala
                    ('PADDING', (0, 0), (-1, -1), 4),                   # Hücre içi boşluk
                    ('FONTNAME', (0, 0), (-1, 0), self.font_bold),      # Header fontu
                ]))
                elements.append(t)
            else:
                elements.append(Paragraph("<i>Bu gün için planlanmış iş bulunmamaktadır.</i>", style_cell_normal))
            
            elements.append(Spacer(1, 10))
            
            # 3. günden sonra sayfa sonu (Rapor çok sıkışmasın)
            if day_idx == 2: 
                elements.append(PageBreak())

        try:
            doc.build(elements)
            return True, self.filename
        except Exception as e:
            return False, str(e)