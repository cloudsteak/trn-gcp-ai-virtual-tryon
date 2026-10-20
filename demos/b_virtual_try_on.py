import base64
import json
import os
from pathlib import Path

import google.auth
import google.auth.transport.requests
import requests

PROJECT_ID = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION") or "europe-west1"
PERSON_IMAGE_URL = os.environ.get("PERSON_IMAGE_URL", "").strip()
GARMENT_IMAGE_URL = os.environ.get("GARMENT_IMAGE_URL", "").strip()
MODEL_NAME = "virtual-try-on-001"
BASE_STEPS = 32
OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "result.png"


def required(name, value):
    if not value:
        raise SystemExit(f"Hiányzik a környezeti változó: {name}")


def download_image(url, label):
    if not url.startswith("https://"):
        raise SystemExit(f"{label}: https:// link kell. Most ez van beállítva: {url}")
    print(f"Link: {url}")
    image_response = requests.get(url, timeout=60)
    print(f"Letöltés kész. HTTP {image_response.status_code}, {len(image_response.content)} byte.")
    image_response.raise_for_status()
    return image_response.content


def main():
    required("GCP_PROJECT_ID", PROJECT_ID)
    required("PERSON_IMAGE_URL", PERSON_IMAGE_URL)
    required("GARMENT_IMAGE_URL", GARMENT_IMAGE_URL)

    try:
        credentials, _ = google.auth.default()
        credentials.refresh(google.auth.transport.requests.Request())
    except google.auth.exceptions.DefaultCredentialsError as exc:
        raise SystemExit(
            "Nincs GCP bejelentkezés. Futtasd: gcloud auth application-default login"
        ) from exc

    print(f"Bejelentkezés kész. Projekt: {PROJECT_ID}")
    print(f"Régió: {LOCATION}")

    print("Kiválasztott modell:")
    person_bytes = download_image(PERSON_IMAGE_URL, "PERSON_IMAGE_URL")
    print("Kiválasztott ruhadarab:")
    garment_bytes = download_image(GARMENT_IMAGE_URL, "GARMENT_IMAGE_URL")

    b64_person_image = base64.b64encode(person_bytes).decode("utf-8")
    b64_product_image = base64.b64encode(garment_bytes).decode("utf-8")
    payload = {
        "instances": [
            {
                "personImage": {
                    "image": {"bytesBase64Encoded": b64_person_image}
                },
                "productImages": [
                    {"image": {"bytesBase64Encoded": b64_product_image}}
                ],
            }
        ],
        "parameters": {"baseSteps": BASE_STEPS},
    }
    preview = {
        "instances": [
            {
                "personImage": {"image": {"bytesBase64Encoded": "${B64_PERSON_IMAGE}"}},
                "productImages": [{"image": {"bytesBase64Encoded": "${B64_PRODUCT_IMAGE}"}}],
            }
        ],
        "parameters": {"baseSteps": BASE_STEPS},
    }
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/publishers/google/models/{MODEL_NAME}:predict"
    )
    print(f"Végpont: {url}")
    print("Elküldött kérés, a képek helyén helyőrzővel:")
    print(json.dumps(preview, indent=2, ensure_ascii=False))

    response = requests.post(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-user-project": PROJECT_ID,
        },
        timeout=180,
    )
    print(f"Válasz: HTTP {response.status_code}")
    if not response.ok:
        print(response.text[:500])
        raise SystemExit(f"A modellhívás sikertelen ({response.status_code}).")

    prediction = response.json()["predictions"][0]
    result_bytes = base64.b64decode(prediction["bytesBase64Encoded"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(result_bytes)
    print(f"Generált kép: {prediction.get('mimeType', 'image/png')}, {len(result_bytes)} byte.")
    print(f"Mentve: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
