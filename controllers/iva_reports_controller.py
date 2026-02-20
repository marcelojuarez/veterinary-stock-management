from models.iva import IVAModel

class ReportsController:
    def __init__(self):
        self.view = None
        self.iva_model = IVAModel()
        self.current_period = None

    def set_view(self, view):
        self.view = view 
    
    def load_period_reports(self, mes, anio):
        """Cargar todos los reportes para un periodo específico"""
        try:
            # Obtener fechas del periodo
            fecha_desde, fecha_hasta = self.iva_model.get_periodo_mes(mes, anio)
            self.current_period = (fecha_desde, fecha_hasta)
            
            # Obtener datos
            posicion = self.iva_model.get_posicion_iva(fecha_desde, fecha_hasta)
            detalle_posicion = self.iva_model.get_posicion_iva_detallada(fecha_desde, fecha_hasta)
            ventas = self.iva_model.get_iva_ventas(fecha_desde, fecha_hasta)
            compras = self.iva_model.get_iva_compras(fecha_desde, fecha_hasta)
            
            # Actualizar vista
            self.view.update_summary(posicion)
            self.view.update_resumen_table(detalle_posicion)
            self.view.update_ventas_table(ventas)
            self.view.update_compras_table(compras)
            
            # Mensaje de confirmación
            # periodo_nombre = f"{self.get_nombre_mes(mes)} {anio}"
            # self.view.show_success(f"Reportes cargados para {periodo_nombre}")
            
        except Exception as e:
            self.view.show_error(f"Error al cargar reportes: {e}")
    
    def export_to_pdf(self):
        """Exportar reporte actual a PDF"""
        if not self.current_period:
            self.view.show_warning("Primero debe cargar un periodo")
            return
        
        try:
            # Aquí puedes implementar la generación de PDF
            # Por ahora solo mostramos un mensaje
            self.view.show_warning("Funcionalidad de exportación a PDF en desarrollo")
            
            # TODO: Implementar generación de PDF con reportlab
            # from services.iva_report_pdf import IVAReportPDF
            # pdf_service = IVAReportPDF()
            # pdf_path = pdf_service.generate(...)
            
        except Exception as e:
            self.view.show_error(f"Error al exportar: {e}")
    
    def get_nombre_mes(self, mes):
        """Convertir número de mes a nombre"""
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        return meses[mes - 1]