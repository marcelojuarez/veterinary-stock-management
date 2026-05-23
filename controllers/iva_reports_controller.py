from tkinter import messagebox
from utils.printing import send_to_printer

class ReportsController:
    def __init__(self, iva_model):
        self.view = None
        self.iva_model = iva_model
        self.current_period = None
        self.current_month = None
        self.current_year = None

    def set_view(self, view):
        self.view = view 
    
    def load_period_reports(self, month, year):
        """Load all reports for a specific period"""
        try:
            # Get period dates
            from_date, until_date = self.iva_model.get_month_period(month, year)
            self.current_period = (from_date, until_date)
            self.current_month = month
            self.current_year = year
            
            # Get IVA data
            position         = self.iva_model.get_iva_position(from_date, until_date)
            position_detail  = self.iva_model.get_detailed_iva_position(from_date, until_date)
            sales            = self.iva_model.get_sales_iva(from_date, until_date)
            purchases        = self.iva_model.get_purchases_iva(from_date, until_date)

            # Get perceptions and retentions data
            suffered_percept = self.iva_model.get_suffered_perceptions(from_date, until_date)
            made_percept     = self.iva_model.get_made_perceptions(from_date, until_date)
            suffered_ret     = self.iva_model.get_suffered_retentions(from_date, until_date)
            made_ret         = self.iva_model.get_made_retentions(from_date, until_date)
            total_per_s, total_per_e = self.iva_model.get_total_perceptions(from_date, until_date)
            total_ret_s, total_ret_e = self.iva_model.get_total_retentions(from_date, until_date)

            # Update IVA view
            self.view.update_summary(position)
            self.view.update_summary_table(position_detail)
            self.view.update_sales_table(sales)
            self.view.update_purchases_table(purchases)

            # Update perceptions and retentions view
            self.view.update_suffered_percep_table(suffered_percept)
            self.view.update_made_percep_table(made_percept)
            self.view.update_suffered_ret_table(suffered_ret)
            self.view.update_made_ret_table(made_ret)
            self.view.update_other_summary({
                'per_suffered': total_per_s,
                'per_made':     total_per_e,
                'ret_suffered': total_ret_s,
                'ret_made':     total_ret_e,
            })
            
        except Exception as e:
            self.view.show_error(f"Error al cargar reportes: {e}")
    
    def export_to_pdf(self):
        """Export current report to PDF"""
        if not self.current_period:
            self.view.show_warning("Primero debe cargar un periodo antes de exportar.")
            return

        try:
            from services.iva_report_pdf import IVAReportPDF

            from_date, until_date = self.current_period

            # Get all data for the current period
            position         = self.iva_model.get_iva_position(from_date, until_date)
            position_detail  = self.iva_model.get_detailed_iva_position(from_date, until_date)
            sales            = self.iva_model.get_sales_iva(from_date, until_date)
            purchases        = self.iva_model.get_purchases_iva(from_date, until_date)
            suffered_percept = self.iva_model.get_suffered_perceptions(from_date, until_date)
            made_percept     = self.iva_model.get_made_perceptions(from_date, until_date)
            suffered_ret     = self.iva_model.get_suffered_retentions(from_date, until_date)
            made_ret         = self.iva_model.get_made_retentions(from_date, until_date)
            total_per        = self.iva_model.get_total_perceptions(from_date, until_date)
            total_ret        = self.iva_model.get_total_retentions(from_date, until_date)

            pdf_path = IVAReportPDF().generate(
                month=self.current_month,
                year=self.current_year,
                position=position,
                position_detail=position_detail,
                sales=sales,
                purchases=purchases,
                suffered_percept=suffered_percept,
                made_percept=made_percept,
                suffered_ret=suffered_ret,
                made_ret=made_ret,
                total_per=total_per,
                total_ret=total_ret,
            )

            self.view.show_success(f"PDF exportado correctamente:\n{pdf_path}")

            if messagebox.askyesno("Imprimir Reporte", "¿Desea imprimir el reporte de IVA?"):
                if not send_to_printer(pdf_path):
                    self.view.show_error("No se pudo enviar a la impresora. Verifique la conexión.")
            else:
                # Si elige "No", lo abrimos en pantalla para que lo vea (Fallback)
                import sys, subprocess, os
                if sys.platform == "win32":
                    os.startfile(pdf_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", pdf_path])
                else:
                    subprocess.Popen(["xdg-open", pdf_path])

        except Exception as e:
            self.view.show_error(f"Error al exportar PDF: {e}")
    
    def get_month_name(self, month):
        """Convert month number to name"""
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return months[month - 1]