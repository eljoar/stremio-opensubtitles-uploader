import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7000))
    print(f"Iniciando Stremio Addon (OpenSubtitles con Uploader) en http://0.0.0.0:{port} ...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
