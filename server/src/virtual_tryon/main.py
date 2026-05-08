import asyncio
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import google.auth
from .config import ALLOWED_ORIGIN, LOCATION, MODEL_NAME
from .agent_platform import run_virtual_tryon

app = FastAPI(title="Virtual Try-On API")

_, detected_project = google.auth.default()
print(f"INFO: Starting with project={detected_project}, location={LOCATION}, model={MODEL_NAME}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


def validate_image(file: UploadFile, content: bytes) -> None:
    # Fajltipus ellenorzese
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only jpg and png images are accepted.")
    # Fajlmeret ellenorzese
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")


@app.post("/try-on")
async def try_on(
    person_image: UploadFile = File(...),
    product_images: List[UploadFile] = File(...),
):
    person_bytes = await person_image.read()
    validate_image(person_image, person_bytes)

    product_bytes_list = []
    for product_image in product_images:
        content = await product_image.read()
        validate_image(product_image, content)
        product_bytes_list.append(content)

    try:
        # Vertex AI hivas 60 masodperces timeouttal
        result_bytes = await asyncio.wait_for(
            asyncio.to_thread(run_virtual_tryon, person_bytes, product_bytes_list),
            timeout=180.0,
        )
    except asyncio.TimeoutError:
        print("ERROR: Vertex AI call timed out after 180 seconds")
        raise HTTPException(status_code=500, detail="Vertex AI request timed out.")
    except Exception as e:
        print(f"ERROR: Vertex AI call failed: {e}")
        raise HTTPException(status_code=500, detail="Vertex AI error.")

    return Response(content=result_bytes, media_type="image/png")
