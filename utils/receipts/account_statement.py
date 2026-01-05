from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from datetime import datetime
from utils.receipts.paths import estado_cuenta
import os


def generate_account_statement(cliente_nombre, movements, summary, commerce_name="Agroveterinaria El Fortín"):
    filepath = estado_cuenta(cliente_nombre)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos minimalistas en blanco y negro
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=4*mm,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=6*mm,
        fontName='Helvetica'
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        spaceAfter=1*mm
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        leading=11
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Oblique',
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    story = []
    
    # Encabezado
    story.append(Paragraph(commerce_name.upper(), title_style))
    story.append(Paragraph("ESTADO DE CUENTA", subtitle_style))
    
    # Información del cliente
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    hora_actual = datetime.now().strftime("%H:%M")
    
    cliente_info = [
        [Paragraph("<b>CLIENTE:</b>", normal_style), cliente_nombre],
        [Paragraph("<b>FECHA:</b>", normal_style), fecha_actual],
        [Paragraph("<b>HORA:</b>", normal_style), hora_actual]
    ]
    
    cliente_table = Table(cliente_info, colWidths=[25*mm, 150*mm])
    cliente_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    story.append(cliente_table)
    story.append(Spacer(1, 8*mm))
    
    # Resumen de cuenta
    resumen_data = [
        [Paragraph("<b>RESUMEN DE CUENTA</b>", header_style), "", "", ""],
        ["Total Comprado:", f"${summary['total_comprado']:,.2f}", 
         "Total Pagado:", f"${summary['total_pagado']:,.2f}"],
        ["Ventas:", f"{summary['ventas_pagadas']}/{summary['total_ventas']} pagadas",
         "Saldo:", f"${summary['deuda_pendiente']:,.2f}" if summary['deuda_pendiente'] > 0 
         else f"${summary['saldo_a_favor']:,.2f} a favor"]
    ]
    
    resumen_table = Table(resumen_data, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
    resumen_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (3, 2), (3, 2), 'RIGHT'),
    ]))
    
    story.append(resumen_table)
    story.append(Spacer(1, 10*mm))
    
    # Historial de movimientos
    if movements:
        story.append(Paragraph("<b>DETALLE DE MOVIMIENTOS</b>", header_style))
        story.append(Spacer(1, 2*mm))
        
        encabezados = ["Fecha", "Tipo", "Descripción", "Debe", "Haber", "Saldo"]
        table_data = [encabezados]
        
        for mov in movements:
            fecha = mov["fecha"][:10] if len(str(mov["fecha"])) > 10 else str(mov["fecha"])
            descripcion = mov["descripcion"][:40] + "..." if len(mov["descripcion"]) > 40 else mov["descripcion"]
            
            debe = f"${mov['debe']:,.2f}" if mov["debe"] > 0 else "-"
            haber = f"${mov['haber']:,.2f}" if mov["haber"] > 0 else "-"
            saldo = f"${mov['saldo']:,.2f}" if mov["saldo"] >= 0 else f"(${abs(mov['saldo']):,.2f})"
            
            table_data.append([fecha, mov["tipo"], descripcion, debe, haber, saldo])
        
        movements_table = Table(
            table_data, 
            colWidths=[25*mm, 20*mm, 65*mm, 25*mm, 25*mm, 30*mm],
            repeatRows=1
        )
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 3),
        ])
        
        # Alternar colores de fila para mejor legibilidad
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
        movements_table.setStyle(table_style)
        story.append(movements_table)
    
    story.append(Spacer(1, 15*mm))
    
    # Línea de firma
    firma_linea = Table([[""]], colWidths=[170*mm])
    firma_linea.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 0.5, colors.black),
        ('PADDING', (0, 0), (0, 0), 8),
    ]))
    story.append(firma_linea)
    
    firma_texto = Table([[Paragraph("Firma del Cliente", normal_style)]], colWidths=[170*mm])
    firma_texto.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
    ]))
    story.append(firma_texto)
    
    # Pie de página
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        f"Documento generado el {fecha_actual} a las {hora_actual} • {commerce_name}",
        footer_style
    ))
    
    doc.build(story)
    return filepath