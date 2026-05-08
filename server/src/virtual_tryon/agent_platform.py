import base64
import google.auth
import google.auth.transport.requests
import requests
from .config import PROJECT_ID, LOCATION, MODEL_NAME


def run_virtual_tryon(person_image_bytes: bytes, garment_image_bytes: bytes) -> bytes:
    # ADC token lekerdese
    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        f"/projects/{PROJECT_ID}/locations/{LOCATION}"
        f"/publishers/google/models/{MODEL_NAME}:predict"
    )

    payload = {
        "instances": [
            {
                "personImage": {
                    "image": {
                        "bytesBase64Encoded": base64.b64encode(person_image_bytes).decode("utf-8")
                    }
                },
                "productImages": [
                    {
                        "image": {
                            "bytesBase64Encoded": base64.b64encode(garment_image_bytes).decode("utf-8")
                        }
                    }
                ],
            }
        ],
        "parameters": {"baseSteps": 10},
    }

    response = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=60,
    )

    response.raise_for_status()

    # Generalt kep kinyerese a valaszbol
    result = response.json()
    image_b64 = result["predictions"][0]["bytesBase64Encoded"]
    return base64.b64decode(image_b64)
