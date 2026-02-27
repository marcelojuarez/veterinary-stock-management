from models.iva import IVAModel

class ReportsController:
    def __init__(self):
        self.view = None
        self.iva_model = IVAModel()
        self.current_period = None
        self.current_mes = None
        self.current_anio = None

    def set_view(self, view):
        self.view = view 
    
    def load_period_reports(self, mes, anio):
        """Cargar todos los reportes para un periodo específico"""
        try:
            # Obtener fechas del periodo
            fecha_desde, fecha_hasta = self.iva_model.get_periodo_mes(mes, anio)
            self.current_period = (fecha_desde, fecha_hasta)
            self.current_mes = mes
            self.current_anio = anio
            
            # Obtener datos IVA
            posicion = self.iva_model.get_posicion_iva(fecha_desde, fecha_hasta)
            detalle_posicion = self.iva_model.get_posicion_iva_detallada(fecha_desde, fecha_hasta)
            ventas = self.iva_model.get_iva_ventas(fecha_desde, fecha_hasta)
            compras = self.iva_model.get_iva_compras(fecha_desde, fecha_hasta)

            # Obtener datos percepciones y retenciones
            perc_sufridas = self.iva_model.get_percepciones_sufridas(fecha_desde, fecha_hasta)
            perc_efectuadas = self.iva_model.get_percepciones_efectuadas(fecha_desde, fecha_hasta)
            ret_sufridas = self.iva_model.get_retenciones_sufridas(fecha_desde, fecha_hasta)
            ret_efectuadas = self.iva_model.get_retenciones_efectuadas(fecha_desde, fecha_hasta)
            total_per_s, total_per_e = self.iva_model.get_totales_percepciones(fecha_desde, fecha_hasta)
            total_ret_s, total_ret_e = self.iva_model.get_totales_retenciones(fecha_desde, fecha_hasta)

            # Actualizar vista IVA
            self.view.update_summary(posicion)
            self.view.update_resumen_table(detalle_posicion)
            self.view.update_ventas_table(ventas)
            self.view.update_compras_table(compras)

            # Actualizar vista percepciones y retenciones
            self.view.update_perc_sufridas_table(perc_sufridas)
            self.view.update_perc_efectuadas_table(perc_efectuadas)
            self.view.update_ret_sufridas_table(ret_sufridas)
            self.view.update_ret_efectuadas_table(ret_efectuadas)
            self.view.update_otros_summary({
                'per_sufridas': total_per_s,
                'per_efectuadas': total_per_e,
                'ret_sufridas': total_ret_s,
                'ret_efectuadas': total_ret_e,
            })
            
            # Mensaje de confirmación
            # periodo_nombre = f"{self.get_nombre_mes(mes)} {anio}"
            # self.view.show_success(f"Reportes cargados para {periodo_nombre}")
            
        except Exception as e:
            self.view.show_error(f"Error al cargar reportes: {e}")
    
    def export_to_pdf(self):
        """Exportar reporte actual a PDF"""
        if not self.current_period:
            self.view.show_warning("Primero debe cargar un periodo antes de exportar.")
            return

        try:
            from services.iva_report_pdf import IVAReportPDF

            fecha_desde, fecha_hasta = self.current_period

            # Obtener todos los datos del periodo actual
            posicion          = self.iva_model.get_posicion_iva(fecha_desde, fecha_hasta)
            detalle_posicion  = self.iva_model.get_posicion_iva_detallada(fecha_desde, fecha_hasta)
            ventas            = self.iva_model.get_iva_ventas(fecha_desde, fecha_hasta)
            compras           = self.iva_model.get_iva_compras(fecha_desde, fecha_hasta)
            perc_sufridas     = self.iva_model.get_percepciones_sufridas(fecha_desde, fecha_hasta)
            perc_efectuadas   = self.iva_model.get_percepciones_efectuadas(fecha_desde, fecha_hasta)
            ret_sufridas      = self.iva_model.get_retenciones_sufridas(fecha_desde, fecha_hasta)
            ret_efectuadas    = self.iva_model.get_retenciones_efectuadas(fecha_desde, fecha_hasta)
            totales_per       = self.iva_model.get_totales_percepciones(fecha_desde, fecha_hasta)
            totales_ret       = self.iva_model.get_totales_retenciones(fecha_desde, fecha_hasta)

            pdf_path = IVAReportPDF().generate(
                mes=self.current_mes,
                anio=self.current_anio,
                posicion=posicion,
                detalle_posicion=detalle_posicion,
                ventas=ventas,
                compras=compras,
                perc_sufridas=perc_sufridas,
                perc_efectuadas=perc_efectuadas,
                ret_sufridas=ret_sufridas,
                ret_efectuadas=ret_efectuadas,
                totales_per=totales_per,
                totales_ret=totales_ret,
            )

            self.view.show_success(f"PDF exportado correctamente:\n{pdf_path}")

            # Abrir el PDF automáticamente
            import subprocess, sys
            if sys.platform == "darwin":
                subprocess.Popen(["open", pdf_path])
            elif sys.platform == "win32":
                import os
                os.startfile(pdf_path)
            else:
                subprocess.Popen(["xdg-open", pdf_path])

        except Exception as e:
            self.view.show_error(f"Error al exportar PDF: {e}")
    
    def get_nombre_mes(self, mes):
        """Convertir número de mes a nombre"""
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        return meses[mes - 1]