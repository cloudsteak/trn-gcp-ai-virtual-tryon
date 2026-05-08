import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .config import ALLOWED_ORIGIN
from .agent_platform import run_virtual_tryon

app = FastAPI(title="Virtual Try-On API")

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
    product_image: UploadFile = File(...),
):
    # Mindket kep beolvasasa
    person_bytes = await person_image.read()
    product_bytes = await product_image.read()

    validate_image(person_image, person_bytes)
    validate_image(product_image, product_bytes)

    try:
        # Vertex AI hivas 60 masodperces timeouttal
        result_bytes = await asyncio.wait_for(
            asyncio.to_thread(run_virtual_tryon, person_bytes, product_bytes),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        print("ERROR: Vertex AI call timed out after 60 seconds")
        raise HTTPException(status_code=500, detail="Vertex AI request timed out.")
    except Exception as e:
        print(f"ERROR: Vertex AI call failed: {e}")
        raise HTTPException(status_code=500, detail="Vertex AI error.")

    return Response(content=result_bytes, media_type="image/png")
