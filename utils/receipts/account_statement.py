from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from datetime import datetime
from utils.receipts.paths import estado_cuenta
from utils.utils import format_currency
from decimal import Decimal


def generate_account_statement(cliente_info, movements, summary, commerce_name="Agroveterinaria El Fortín"):
    """Genera un estado de cuenta en formato clásico de cuenta corriente"""
    
    cliente_nombre = cliente_info['nombre']
    filepath = estado_cuenta(cliente_nombre)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=12*mm,
        bottomMargin=12*mm
    )
    
    styles = getSampleStyleSheet()
    
    # ================================================================
    # ESTILOS
    # ================================================================
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=3*mm
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.black
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.black
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.black
    )
    
    table_data_style = ParagraphStyle(
        'TableData',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica',
        leading=11
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    story = []
    
    # ================================================================
    # TÍTULO PRINCIPAL
    # ================================================================
    
    titulo = Table([[Paragraph("FICHA DE CUENTA CORRIENTE - CLIENTES", title_style)]], 
                   colWidths=[180*mm])
    titulo.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(titulo)
    story.append(Spacer(1, 3*mm))
    
    # ================================================================
    # INFORMACIÓN DEL CLIENTE
    # ================================================================
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    
    # Línea 1: Cliente y Crédito Acordado
    linea1_data = [
        [
            Paragraph(f"<b>CLIENTE:</b> {cliente_nombre}", label_style),
            Paragraph(f"<b>Crédito Acordado: $</b> {format_currency(summary['total_purchased'])}", label_style)
        ]
    ]
    
    linea1 = Table(linea1_data, colWidths=[110*mm, 70*mm])
    linea1.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(linea1)
    
    # Línea 2: Domicilio
    domicilio = cliente_info.get('domicilio', '') or '........................................................'
    linea2_data = [
        [Paragraph(f"<b>DOMICILIO:</b> {domicilio}", label_style)]
    ]
    
    linea2 = Table(linea2_data, colWidths=[180*mm])
    linea2.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(linea2)
    
    # Línea 3: Teléfono y CUIT
    telefono = cliente_info.get('telefono', '') or '......................'
    cuit = cliente_info.get('cuit', '') or '.......................'
    
    linea3_data = [
        [
            Paragraph(f"<b>Teléfono:</b> {telefono}", label_style),
            Paragraph(f"<b>CUIT N°:</b> {cuit}", label_style)
        ]
    ]
    
    linea3 = Table(linea3_data, colWidths=[90*mm, 90*mm])
    linea3.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(linea3)
    story.append(Spacer(1, 5*mm))
    
    # ================================================================
    # TABLA DE MOVIMIENTOS
    # ================================================================
    
    # Encabezados
    encabezados = [
        Paragraph("<b>FECHA</b>", table_header_style),
        Paragraph("<b>DETALLE</b>", table_header_style),
        Paragraph("<b>DEBE</b>", table_header_style),
        Paragraph("<b>HABER</b>", table_header_style),
        Paragraph("<b>SALDO</b>", table_header_style)
    ]
    
    table_data = [encabezados]
    
    # Agregar movimientos
    if movements:
        movements = list(reversed(movements))
        for mov in movements:
            fecha = str(mov[2])[:10]  # Solo fecha sin hora
            
            # Descripción más corta
            detalle = mov[4]
            if len(detalle) > 55:
                detalle = detalle[:55] + "..."
            
            # Formatear montos
            purchased = f"${format_currency(mov[5])}" if Decimal(mov[5]) > 0 else ""
            paid = f"${format_currency(mov[6])}" if Decimal(mov[6]) > 0 else ""
            debt = f"${format_currency(mov[7])}"
            
            table_data.append([
                Paragraph(fecha, table_data_style),
                Paragraph(detalle, table_data_style),
                Paragraph(purchased, ParagraphStyle('Right', parent=table_data_style, 
                                              alignment=TA_RIGHT)),
                Paragraph(paid, ParagraphStyle('Right', parent=table_data_style, 
                                               alignment=TA_RIGHT)),
                Paragraph(debt, ParagraphStyle('RightBold', parent=table_data_style, 
                                               alignment=TA_RIGHT, fontName='Helvetica-Bold'))
            ])
    
    # Agregar filas vacías para completar la página (estilo formulario clásico)
    filas_vacias = 12 - len(movements) if len(movements) < 12 else 0
    for _ in range(filas_vacias):
        table_data.append([
            Paragraph("", table_data_style),
            Paragraph("", table_data_style),
            Paragraph("", table_data_style),
            Paragraph("", table_data_style),
            Paragraph("", table_data_style)
        ])
    
    # Crear tabla
    movements_table = Table(
        table_data,
        colWidths=[25*mm, 75*mm, 25*mm, 25*mm, 30*mm],
        repeatRows=1
    )
    
    # Estilo minimalista blanco y negro
    table_style = TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        
        # Bordes gruesos (estilo formulario)
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
        
        # Alineación
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),      # Fecha
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),        # Detalle
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),      # Montos
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Padding uniforme
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ])
    
    movements_table.setStyle(table_style)
    story.append(movements_table)
    
    # ================================================================
    # RESUMEN AL PIE
    # ================================================================
    
    story.append(Spacer(1, 5*mm))
    
    resumen_data = [
        [
            Paragraph(f"<b>TOTAL DEBE:</b> ${format_currency(summary['total_purchased'])}", label_style),
            Paragraph(f"<b>TOTAL HABER:</b> ${format_currency(summary['total_paid'])}", label_style),
            Paragraph(f"<b>DEUDA RESTANTE:</b> ${format_currency(summary['total_debt'])}", 
                     ParagraphStyle('Bold', parent=label_style, fontSize=11))
        ]
    ]
    
    resumen_table = Table(resumen_data, colWidths=[60*mm, 60*mm, 60*mm])
    resumen_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(resumen_table)
    
    # ================================================================
    # FIRMA
    # ================================================================
    
    story.append(Spacer(1, 15*mm))
    
    firma_data = [
        [Paragraph("_" * 58, ParagraphStyle('Line', fontSize=10))],
        [Paragraph("<b>Firma y Aclaración del Cliente</b>", 
                  ParagraphStyle('Firma', parent=label_style, alignment=TA_CENTER))]
    ]
    
    firma_table = Table(firma_data, colWidths=[120*mm])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 1), (-1, 1), 3),
    ]))
    
    story.append(firma_table)
    
    # ================================================================
    # PIE DE PÁGINA
    # ================================================================
    
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        f"{commerce_name} | Fecha de emisión: {fecha_actual}",
        footer_style
    ))
    
    # ================================================================
    # CONSTRUIR PDF
    # ================================================================
    
    doc.build(story)
    return filepath