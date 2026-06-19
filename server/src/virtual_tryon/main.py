import asyncio
import json
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
import google.auth
from .config import ALLOWED_ORIGIN, LOCATION, MODEL_NAME, PROJECT_ID
from .agent_platform import iter_virtual_tryon, run_virtual_tryon

# FastAPI alkalmazas letrehozasa
app = FastAPI(title="Virtual Try-On API")

# Aktualis GCP projekt kiirasa inditaskor – ellenorzeshez hasznos
try:
    _, detected_project = google.auth.default()
except google.auth.exceptions.DefaultCredentialsError:
    detected_project = PROJECT_ID or "unknown"
print(f"INFO: Starting with project={detected_project}, location={LOCATION}, model={MODEL_NAME}")

# CORS beallitas: csak az engedelyezett frontend URL-rol fogad kereseket
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Feltoltheto fajl maximalis merete es engedelyezett tipusai
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


def validate_image(file: UploadFile, content: bytes) -> None:
    # Fajltipus ellenorzese – csak jpg es png engedelyezett
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only jpg and png images are accepted.")
    # Fajlmeret ellenorzese – max 10MB
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")


def _parse_show_model_response(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _stream_try_on(person_bytes: bytes, product_bytes_list: list[bytes]) -> StreamingResponse:
    def generate():
        try:
            for event in iter_virtual_tryon(person_bytes, product_bytes_list):
                if isinstance(event, tuple):
                    complete_event, result_image = event
                    yield (json.dumps(complete_event, ensure_ascii=False) + "\n").encode("utf-8")
                    yield result_image
                    return

                yield (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")
        except Exception as e:
            print(f"ERROR: {MODEL_NAME} call failed: {e}")
            yield (json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False) + "\n").encode("utf-8")

    return StreamingResponse(
        generate(),
        media_type="application/octet-stream",
        headers={
            "X-TryOn-Mode": "stream-summary",
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )


@app.post("/try-on")
async def try_on(
    person_image: UploadFile = File(...),
    product_images: List[UploadFile] = File(...),
    show_model_response: str = Form("false"),
):
    # Szemelykep beolvasasa es validalasa
    person_bytes = await person_image.read()
    validate_image(person_image, person_bytes)

    # Osszes ruhadarab beolvasasa es validalasa
    product_bytes_list = []
    for product_image in product_images:
        content = await product_image.read()
        validate_image(product_image, content)
        product_bytes_list.append(content)

    include_model_response = _parse_show_model_response(show_model_response)

    if include_model_response:
        return _stream_try_on(person_bytes, product_bytes_list)

    try:
        # Agent Platform hivas kulonallo szalban, 180 masodperces timeouttal
        # (tobb ruhadarabnal tobb egymast koveto hivas tortenik)
        result_bytes = await asyncio.wait_for(
            asyncio.to_thread(run_virtual_tryon, person_bytes, product_bytes_list),
            timeout=180.0,
        )
    except asyncio.TimeoutError:
        print(f"ERROR: {MODEL_NAME} call timed out after 180 seconds")
        raise HTTPException(status_code=500, detail=f"{MODEL_NAME} request timed out.")
    except Exception as e:
        print(f"ERROR: {MODEL_NAME} call failed: {e}")
        raise HTTPException(status_code=500, detail=f"{MODEL_NAME} error.")

    # Generalt kep visszakuldese PNG formatumban
    return Response(content=result_bytes, media_type="image/png")
