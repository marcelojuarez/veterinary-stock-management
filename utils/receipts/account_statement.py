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
    
    # Estilos profesionales en blanco y negro
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=3*mm,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=8*mm,
        fontName='Helvetica'
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        spaceAfter=3*mm
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        leading=12
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.grey
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
    
    # ================================================================
    # ENCABEZADO
    # ================================================================
    story.append(Paragraph(commerce_name.upper(), title_style))
    story.append(Paragraph("Estado de Cuenta Corriente", subtitle_style))
    
    # Información del cliente y fecha
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    hora_actual = datetime.now().strftime("%H:%M")
    
    cliente_info = [
        [Paragraph("<b>Cliente:</b>", normal_style), Paragraph(cliente_nombre, normal_style)],
        [Paragraph("<b>Fecha:</b>", normal_style), Paragraph(f"{fecha_actual} - {hora_actual}", normal_style)]
    ]
    
    cliente_table = Table(cliente_info, colWidths=[30*mm, 150*mm])
    cliente_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    story.append(cliente_table)
    story.append(Spacer(1, 8*mm))
    
    # ================================================================
    # RESUMEN DE CUENTA (como en la app)
    # ================================================================
    story.append(Paragraph("RESUMEN DE CUENTA", header_style))
    story.append(Spacer(1, 3*mm))
    
    resumen_data = [
        # Encabezados
        [
            Paragraph("<b>Total Comprado</b>", normal_style),
            Paragraph("<b>Total Pagado</b>", normal_style),
            Paragraph("<b>Deuda Pendiente</b>", normal_style),
            Paragraph("<b>Ventas</b>", normal_style)
        ],
        # Valores
        [
            Paragraph(f"<font size=13><b>${summary['total_comprado']:,.2f}</b></font>", normal_style),
            Paragraph(f"<font size=13><b>${summary['total_pagado']:,.2f}</b></font>", normal_style),
            Paragraph(f"<font size=13><b>${summary['deuda_pendiente']:,.2f}</b></font>", normal_style),
            Paragraph(f"<font size=12><b>{summary['ventas_texto']}</b></font>", normal_style)
        ]
    ]
    
    # Si hay saldo a favor, agregarlo
    if summary['saldo_a_favor'] > 0:
        resumen_data[0].append(Paragraph("<b>Saldo a Favor</b>", normal_style))
        resumen_data[1].append(Paragraph(f"<font size=13><b>${summary['saldo_a_favor']:,.2f}</b></font>", normal_style))
        col_widths = [42*mm, 42*mm, 42*mm, 35*mm, 35*mm]
    else:
        col_widths = [50*mm, 50*mm, 50*mm, 40*mm]
    
    resumen_table = Table(resumen_data, colWidths=col_widths)
    resumen_table.setStyle(TableStyle([
        # Bordes
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        
        # Encabezados con fondo gris claro
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        
        # Valores
        ('FONTSIZE', (0, 1), (-1, 1), 13),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(resumen_table)
    story.append(Spacer(1, 10*mm))
    
    # ================================================================
    # HISTORIAL DE MOVIMIENTOS (exacto a la tabla de la app)
    # ================================================================
    if movements:
        story.append(Paragraph("HISTORIAL DE MOVIMIENTOS", header_style))
        story.append(Spacer(1, 3*mm))
        
        # Encabezados (igual que en la app)
        encabezados = [
            Paragraph("<b>Fecha</b>", normal_style),
            Paragraph("<b>Tipo</b>", normal_style),
            Paragraph("<b>Descripción</b>", normal_style),
            Paragraph("<b>Compra</b>", normal_style),
            Paragraph("<b>Pago</b>", normal_style),
            Paragraph("<b>Deuda/Crédito</b>", normal_style)
        ]
        
        table_data = [encabezados]
        
        for mov in movements:
            # Formatear fecha
            fecha = mov["fecha"][:16] if len(str(mov["fecha"])) > 16 else str(mov["fecha"])
            
            # Descripción
            descripcion = mov["descripcion"]
            if len(descripcion) > 45:
                descripcion = descripcion[:42] + "..."
            
            # Compra (solo si es venta)
            compra = f"${mov['debe']:,.2f}" if mov["debe"] > 0 else ""
            
            # Pago (solo si es pago)
            pago = f"${mov['haber']:,.2f}" if mov["haber"] > 0 else ""
            
            # Saldo (exacto como en la app)
            saldo_val = mov["saldo"]
            if abs(saldo_val) < 0.01:
                saldo = "$0.00"
            else:
                saldo = f"${saldo_val:,.2f}"
            
            table_data.append([
                Paragraph(fecha, normal_style),
                Paragraph(f"<b>{mov['tipo']}</b>", normal_style),
                Paragraph(descripcion, normal_style),
                Paragraph(compra, normal_style),
                Paragraph(pago, normal_style),
                Paragraph(saldo, normal_style)
            ])
        
        # Tabla de movimientos
        movements_table = Table(
            table_data,
            colWidths=[32*mm, 20*mm, 62*mm, 25*mm, 25*mm, 28*mm],
            repeatRows=1
        )
        
        table_style = TableStyle([
            # Encabezado con fondo gris oscuro
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Contenido
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            
            # Alineación
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),   # Fecha y Tipo
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),     # Descripción
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),   # Montos
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordes
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.white),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#D0D0D0')),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ])
        
        # Alternar filas (gris muy claro)
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F5F5F5'))
        
        # Colorear filas según tipo (sutilmente)
        row_idx = 1
        for mov in movements:
            if mov["tipo"] == "VENTA":
                table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#FFF8E1'))
            elif mov["tipo"] == "PAGO":
                table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#E8F5E9'))
            row_idx += 1
        
        movements_table.setStyle(table_style)
        story.append(movements_table)
        
        # Nota explicativa
        story.append(Spacer(1, 5*mm))
        nota = Paragraph(
            "<i>Nota: La columna 'Deuda/Crédito' muestra el saldo acumulado después de cada movimiento. "
            "Un saldo positivo indica deuda pendiente, un saldo negativo indica saldo a favor del cliente.</i>",
            small_style
        )
        story.append(nota)
    
    # ================================================================
    # FIRMA Y PIE DE PÁGINA
    # ================================================================
    story.append(Spacer(1, 15*mm))
    
    # Línea de firma
    firma_data = [["_" * 60]]
    firma_table = Table(firma_data, colWidths=[150*mm])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (0, 0), 8),
    ]))
    story.append(firma_table)
    
    firma_texto = Paragraph("<b>Firma y Aclaración del Cliente</b>", normal_style)
    firma_texto_table = Table([[firma_texto]], colWidths=[150*mm])
    firma_texto_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
    ]))
    story.append(firma_texto_table)
    
    # Pie de página
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        f"Documento generado el {fecha_actual} a las {hora_actual} | {commerce_name}",
        footer_style
    ))
    
    # Construir PDF
    doc.build(story)
    return filepath