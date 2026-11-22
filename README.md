# 🎬 OpenSubtitles con Uploader — Addon para Stremio

Este addon para Stremio consulta la base de datos oficial de **OpenSubtitles.com** y le añade a cada subtítulo la etiqueta visible con:
- El nombre del usuario que lo subió (**Uploader**, ej: `[eljoar]`).
- La versión de video (**Release**, ej: `1080p.WEB`).
- Prioridad destacada (`⭐`) al inicio de la lista si fue subido por tu cuenta (`eljoar`).

---

## 🚀 1. Ejecución Local (Para probar de inmediato)

En tu computadora:
```powershell
# Desde la carpeta raíz del proyecto:
.\.venv\Scripts\python.exe stremio-addon\run_addon.py
```
El Addon se iniciará en `http://localhost:7000`.

### Para instalarlo en tu Stremio (PC / Web):
1. Abre tu navegador e ingresa a: `http://localhost:7000`
2. Haz clic en el botón morado **"Instalar en Stremio"** (o copia el enlace del `manifest.json` y pégalo en el buscador de Addons en Stremio).

### Para instalarlo en Google TV / Android TV:
1. Asegúrate de que tu PC y tu televisor estén en el mismo Wi-Fi.
2. Averigua la IP local de tu PC (en CMD / PowerShell escribe `ipconfig`, ej: `192.168.1.45`).
3. En la PC, abre Stremio Web (`web.stremio.com`), ve a Addons y en la barra de búsqueda pega:
   `http://192.168.1.45:7000/manifest.json`
4. Al instalarlo en tu cuenta, **se sincronizará automáticamente con tu Google TV**.

---

## ☁️ 2. Publicación Gratuita 24/7 en la Nube (Opcional, sin depender de la PC)

Si quieres que tu Google TV lo tenga activo las 24 horas sin necesidad de encender la computadora:

### En Render (Gratis):
1. Crea una cuenta en [render.com](https://render.com).
2. Crea un **New Web Service** conectando tu repositorio GitHub.
3. Configuración:
   - **Root Directory:** `stremio-addon`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. En **Environment Variables**:
   - `OPENSUBTITLES_API_KEY`: tu clave API.
   - `OPENSUBTITLES_USERNAME`: `eljoar`
5. Render te dará una URL (ej: `https://mi-addon-subtitulos.onrender.com`).
6. Abres esa URL en tu teléfono o PC, le das a **"Instalar en Stremio"** y ¡listo para siempre en todos tus dispositivos!
