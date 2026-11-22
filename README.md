# FOTO → 3D

MVP web app: upload front/side/back reference photos, preview them, and submit them to a configurable image-to-3D inference endpoint.

## Important deployment note
Render hosts the web app/API; it does not provide a free GPU suitable for running modern 3D-generation models. This project therefore separates the web app from the inference engine. The app works in demo mode immediately. To generate real meshes, connect a compatible inference endpoint using the environment variables below.

The adapter expects an endpoint that accepts multipart form data with `front`, `side`, and `back` image files and returns either:
- a binary `.glb` response, or
- JSON containing `model_url` (a publicly reachable GLB URL).

A compatible endpoint can be your own GPU server/Space. GPU inference providers may charge, and free quotas/availability can change.

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000

## Deploy on Render
1. Push this folder to a GitHub repository.
2. In Render, create **New + → Web Service** and connect the repo.
3. Runtime: Python.
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Optional environment variables:
   - `GENERATOR_URL`: URL of your image-to-3D inference endpoint
   - `GENERATOR_TOKEN`: bearer token, if required

Without `GENERATOR_URL`, the app clearly reports demo mode instead of pretending a real model was generated.

## Multi-view note
The interface collects three views, but the quality depends on the connected model. Many public image-to-3D models accept only one image; a multi-view endpoint must be specifically designed to use all three images. The API adapter sends all three.
