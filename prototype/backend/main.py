import base64
import os

import google.auth
import google.auth.transport.requests
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")

app = FastAPI()
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)


@app.get("/health")
def status():
    return {"status": "ok"}


@app.post("/try-on")
async def try_on(
    person_image: UploadFile = File(...), product_images: list[UploadFile] = File(...)
):
    person_bytes = await person_image.read()
    product_bytes = await product_images[0].read()

    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        f"/projects/{PROJECT_ID}/locations/{LOCATION}"
        f"/publishers/google/models/virtual-try-on-001:predict"
    )
    response = requests.post(
        url,
        json={
            "instances": [
                {
                    "personImage": {
                        "image": {
                            "bytesBase64Encoded": base64.b64encode(
                                person_bytes
                            ).decode()
                        }
                    },
                    "productImages": [
                        {
                            "image": {
                                "bytesBase64Encoded": base64.b64encode(
                                    product_bytes
                                ).decode()
                            }
                        }
                    ],
                }
            ],
            "parameters": {"baseSteps": 10},
        },
        headers={"Authorization": f"Bearer {credentials.token}"},
    )
    result = response.json()
    return Response(
        base64.b64decode(result["predictions"][0]["bytesBase64Encoded"]),
        media_type="image/png",
    )
