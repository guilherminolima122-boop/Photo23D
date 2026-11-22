import os
import uuid
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
OUT = BASE / "generated"
OUT.mkdir(exist_ok=True)

app = FastAPI(title="Foto para 3D")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

@app.get("/")
async def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/status")
async def status():
    return {"ready": True, "mode": "connected" if os.getenv("GENERATOR_URL") else "demo"}

@app.post("/api/generate")
async def generate(
    front: UploadFile = File(...),
    side: UploadFile = File(...),
    back: UploadFile = File(...)
):
    uploads = {"front": front, "side": side, "back": back}
    for label, item in uploads.items():
        if not item.content_type or not item.content_type.startswith("image/"):
            raise HTTPException(400, f"O arquivo {label} precisa ser uma imagem.")
    payload = {}
    for label, item in uploads.items():
        data = await item.read()
        if len(data) > 15 * 1024 * 1024:
            raise HTTPException(413, "Cada imagem deve ter no máximo 15 MB.")
        payload[label] = (item.filename or f"{label}.jpg", data, item.content_type)

    endpoint = os.getenv("GENERATOR_URL")
    if not endpoint:
        return JSONResponse(
            status_code=503,
            content={
                "error": "MODO DEMO: o site está funcionando, mas falta conectar um servidor de IA 3D com GPU.",
                "hint": "Configure GENERATOR_URL com um endpoint compatível. O Render hospeda o site, não executa esse modelo pesado gratuitamente."
            }
        )

    headers = {}
    token = os.getenv("GENERATOR_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=600) as client:
            result = await client.post(endpoint, files=payload, headers=headers)
        result.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Falha ao chamar o gerador 3D: {exc}")

    if "model/gltf-binary" in result.headers.get("content-type", "") or result.content[:4] == b"glTF":
        name = f"{uuid.uuid4().hex}.glb"
        path = OUT / name
        path.write_bytes(result.content)
        return {"model_url": f"/models/{name}"}

    try:
        body = result.json()
    except ValueError:
        raise HTTPException(502, "O gerador respondeu em um formato não reconhecido.")
    if body.get("model_url"):
        return {"model_url": body["model_url"]}
    raise HTTPException(502, "Resposta do gerador sem model_url ou arquivo GLB.")

@app.get("/models/{name}")
async def model(name: str):
    path = OUT / Path(name).name
    if not path.exists():
        raise HTTPException(404, "Modelo não encontrado.")
    return FileResponse(path, media_type="model/gltf-binary", filename=path.name)
