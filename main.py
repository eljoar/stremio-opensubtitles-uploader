import os
import re
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv

# Cargar variables de entorno (busca primero en .env local o en la raíz)
load_dotenv()
load_dotenv("../.env")

OPENSUBTITLES_API_KEY = os.getenv("OPENSUBTITLES_API_KEY", "TKh62mCcPfEorphr0grM4QyGsUak8wM1")
MY_USERNAME = os.getenv("OPENSUBTITLES_USERNAME", "eljoar").lower()

app = FastAPI(title="Stremio OpenSubtitles Uploader Addon")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caché en memoria para subtítulos descargados (evita consumir cuota en reproducciones repetidas)
SUBTITLE_CACHE: Dict[int, str] = {}

MANIFEST = {
    "id": "community.opensubtitles.uploader",
    "version": "1.0.1",
    "name": "OpenSubtitles [eljoar]",
    "description": "Subtítulos de OpenSubtitles identificados con [eljoar].",
    "logo": "https://raw.githubusercontent.com/stremio/stremio-addons/master/images/opensubtitles.png",
    "resources": [
        {
            "name": "subtitles",
            "types": ["movie", "series"],
            "idPrefixes": ["tt"]
        }
    ],
    "types": ["movie", "series"],
    "catalogs": []
}

@app.get("/ping")
@app.head("/ping")
@app.head("/")
async def ping():
    return Response(content="OK", media_type="text/plain", status_code=200)

@app.get("/manifest.json")
@app.head("/manifest.json")
async def get_manifest():
    return JSONResponse(content=MANIFEST, headers={"Access-Control-Allow-Origin": "*"})

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    host = request.headers.get("host", "127.0.0.1:7000")
    scheme = "https" if request.url.scheme == "https" or "render" in host or "koyeb" in host or "hf.space" in host else "http"
    manifest_url = f"{scheme}://{host}/manifest.json"
    stremio_link = f"stremio://{host}/manifest.json"

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenSubtitles [eljoar] - Stremio Addon</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl text-center space-y-6">
            <div class="inline-flex p-4 bg-purple-950/60 border border-purple-600/40 rounded-full text-purple-400">
                <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"/>
                </svg>
            </div>
            
            <div>
                <h1 class="text-2xl sm:text-3xl font-extrabold text-white">OpenSubtitles [eljoar]</h1>
                <p class="text-slate-400 text-sm mt-2">
                    Addon para Stremio que identifica claramente quién subió el subtítulo (ej: <span class="text-purple-400 font-semibold">[eljoar]</span>) y para qué release es.
                </p>
            </div>

            <div class="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 text-left text-xs sm:text-sm text-slate-300 space-y-2">
                <div class="flex items-center gap-2 text-emerald-400 font-medium">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    Servicio Activo
                </div>
                <p><strong>Enlace del Addon (Manifest):</strong></p>
                <div class="flex items-center gap-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-xs overflow-x-auto text-purple-300">
                    <span id="manifestUrl" class="truncate">{manifest_url}</span>
                </div>
            </div>

            <div class="flex flex-col sm:flex-row gap-3 justify-center">
                <a href="{stremio_link}" class="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold transition shadow-lg shadow-purple-600/30">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg>
                    Instalar en Stremio
                </a>
                <button onclick="navigator.clipboard.writeText('{manifest_url}'); alert('¡Enlace copiado! Pégalo en la barra de búsqueda de Addons en Stremio.');" class="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium border border-slate-700 transition">
                    Copiar Enlace
                </button>
            </div>

            <div class="text-xs text-slate-500 pt-2 border-t border-slate-800/80">
                Compatible con Google TV, Android TV, PC y Móvil.
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


def parse_stremio_id(raw_id: str) -> Dict[str, Any]:
    """
    Parsea los identificadores de Stremio.
    Ejemplos:
      Película: tt1254207
      Serie: tt1254207:1:5 (imdb_id, temporada 1, episodio 5)
    """
    cleaned = raw_id.replace("%3A", ":")
    parts = cleaned.split(":")
    
    imdb_str = parts[0]
    # Extraer el número entero del IMDb (sin el prefijo 'tt')
    imdb_match = re.search(r"tt(\d+)", imdb_str)
    imdb_id = int(imdb_match.group(1)) if imdb_match else None

    season = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    episode = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None

    return {
        "imdb_id": imdb_id,
        "season": season,
        "episode": episode
    }


@app.get("/subtitles/{type}/{id}.json")
@app.get("/subtitles/{type}/{id}/{extra}.json")
async def get_subtitles(type: str, id: str, request: Request, extra: Optional[str] = None):
    """
    Endpoint principal del protocolo de Stremio para consultar subtítulos.
    Estrategia de detección infalible:
    1. Consulta el clúster oficial de Stremio (donde Stremio indexa los subtítulos).
    2. Comprueba si el subtítulo contiene la dedicatoria o firma 'eljoar'.
    3. Consulta también OpenSubtitles REST API v1 por si fue subido recientemente.
    """
    subtitles_list: List[Dict[str, Any]] = []
    seen_urls = set()

    # 1. Búsqueda directa en el repositorio oficial de Stremio
    try:
        stremio_api_url = f"https://opensubtitles-v3.strem.io/subtitles/{type}/{id}.json"
        async with httpx.AsyncClient(follow_redirects=True, timeout=6.0) as client:
            res = await client.get(stremio_api_url)
            if res.status_code == 200:
                subs = res.json().get("subtitles", [])
                for s in subs:
                    # Nos enfocamos en subtítulos en español (es, spa, spl)
                    if s.get("lang") in ["spl", "spa", "es", "es-419"]:
                        url = s.get("url")
                        if url and url not in seen_urls:
                            try:
                                # Comprobar los primeros 600 bytes del archivo buscando 'eljoar'
                                peek = await client.get(url, headers={"Range": "bytes=0-600"}, timeout=3.5)
                                if "eljoar" in peek.text.lower():
                                    subtitles_list.append({
                                        "id": f"eljoar_{s.get('id')}",
                                        "url": url,
                                        "lang": s.get("lang", "spl"),
                                        "label": "Español Latino [eljoar]"
                                    })
                                    seen_urls.add(url)
                            except Exception:
                                pass
    except Exception as e:
        print(f"Error consultando clúster Stremio: {e}")

    # 2. Búsqueda en OpenSubtitles REST API v1
    parsed = parse_stremio_id(id)
    if parsed["imdb_id"]:
        try:
            url = "https://api.opensubtitles.com/api/v1/subtitles"
            params = {
                "imdb_id": parsed["imdb_id"],
                "languages": "es,spl"
            }
            if parsed["season"] is not None:
                params["season_number"] = parsed["season"]
            if parsed["episode"] is not None:
                params["episode_number"] = parsed["episode"]

            headers = {
                "Api-Key": OPENSUBTITLES_API_KEY,
                "User-Agent": "StremioOpenSubtitlesUploader v1.0"
            }

            host = request.headers.get("host", "127.0.0.1:7000")
            scheme = "https" if request.url.scheme == "https" or "render" in host or "koyeb" in host or "hf.space" in host else "http"

            async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
                res = await client.get(url, params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    for item in data:
                        attrs = item.get("attributes", {})
                        files = attrs.get("files", [])
                        if not files:
                            continue
                        file_id = files[0].get("file_id")
                        if not file_id:
                            continue

                        uploader_info = attrs.get("uploader") or {}
                        uploader_name = (uploader_info.get("name") or "").lower()
                        release = (attrs.get("release") or "").lower()
                        filename = (files[0].get("file_name") or "").lower()

                        if "eljoar" in uploader_name or "eljoar" in release or "eljoar" in filename:
                            sub_url = f"{scheme}://{host}/sub/{file_id}.srt"
                            if sub_url not in seen_urls:
                                lang_code = attrs.get("language", "es").lower()
                                stremio_lang = "spl" if lang_code == "spl" else "spa"
                                subtitles_list.append({
                                    "id": f"os_uploader_{file_id}",
                                    "url": sub_url,
                                    "lang": stremio_lang,
                                    "label": f"Latino [eljoar] - {attrs.get('release') or 'WEB'}"
                                })
                                seen_urls.add(sub_url)
        except Exception as e:
            print(f"Error consultando OpenSubtitles REST: {e}")

    return JSONResponse(
        content={"subtitles": subtitles_list},
        headers={"Access-Control-Allow-Origin": "*"}
    )


@app.get("/sub/{file_id}.srt")
async def proxy_subtitle(file_id: int):
    """
    Descarga el archivo desde OpenSubtitles, normaliza su codificación a UTF-8 limpio
    y se lo entrega a Stremio de inmediato. Guarda en caché para no volver a gastar descarga.
    """
    if file_id in SUBTITLE_CACHE:
        return Response(
            content=SUBTITLE_CACHE[file_id],
            media_type="text/plain; charset=utf-8",
            headers={"Access-Control-Allow-Origin": "*"}
        )

    url = "https://api.opensubtitles.com/api/v1/download"
    headers = {
        "Api-Key": OPENSUBTITLES_API_KEY,
        "User-Agent": "StremioOpenSubtitlesUploader v1.0"
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            res = await client.post(url, json={"file_id": file_id}, headers=headers)
            if res.status_code == 200:
                dl_data = res.json()
                dl_link = dl_data.get("link")
                if dl_link:
                    srt_res = await client.get(dl_link, timeout=15.0)
                    if srt_res.status_code == 200:
                        raw_bytes = srt_res.content
                        # Decodificación resiliente a UTF-8
                        text = None
                        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
                            try:
                                text = raw_bytes.decode(enc)
                                break
                            except UnicodeDecodeError:
                                continue
                        if not text:
                            text = raw_bytes.decode("utf-8", errors="replace")

                        # Guardar en memoria caché
                        if len(SUBTITLE_CACHE) > 200:
                            SUBTITLE_CACHE.clear()
                        SUBTITLE_CACHE[file_id] = text

                        return Response(
                            content=text,
                            media_type="text/plain; charset=utf-8",
                            headers={"Access-Control-Allow-Origin": "*"}
                        )
    except Exception as e:
        print(f"Error descargando subtítulo {file_id}: {e}")

    raise HTTPException(status_code=404, detail="No se pudo obtener el subtítulo solicitado.")
