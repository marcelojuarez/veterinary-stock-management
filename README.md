# Veterinary Stock Management 🐾

**Veterinary Stock Management** es un sistema de escritorio para la **gestión de stock en veterinarias**, desarrollado en **Python** con **CustomTkinter** para ofrecer una interfaz moderna, intuitiva y personalizable. 

El objetivo principal es ofrecer una herramienta **ágil, simple y moderna** para la administración diaria.


## 🚀 Funcionalidades principales

-  **Gestión de productos**: nombre, descripción, precio y stock actual.  
- **Movimientos de stock**: registro de entradas y salidas.   
-  **Persistencia de datos** mediante SQLite.  
-  **Consulta y búsqueda** de productos de forma ágil.  
-  **Gestión de clientes y proveedores**.  
-  **Facturación y comprobantes**:  
    - Facturas para clientes y proveedores  
    - Remitos con generación de 2 copias (impactan en la BD)  
    - Recibos  
    - Control de deudas a proveedores  


## 🛠️ Tecnologías utilizadas
```
Python CustomTkinter SQLite tksheet
Tkinter python-escpos MVC venv
```

## ⚙️ Instalacion

Clona el repositorio e instala las dependencias:

```bash
  git clone https://github.com/marcelojuarez/veterinary-stock-management.git
  cd veterinary-stock-management
  python -m venv venv
```

Activa el entorno virtual (recomendado)

Windows: 

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

Instala los paquetes necesarios:

```bash
pip install -r requirements.txt
```

Ejecuta la aplicacion: 


```bash
python main.py 
```

¡Listo! 🐾 La aplicación debería abrirse y estar lista para usar.

## Integrantes
- [Marcelo Juarez](https://www.github.com/marcelojuarez)
- [Juan Cruz Reynoso](https://www.github.com/juancreynoso)
- [Agustin Cesari](https://www.github.com/AgusCesari)