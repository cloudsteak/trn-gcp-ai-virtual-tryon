import base64
import google.auth
import google.auth.transport.requests
import requests
from .config import PROJECT_ID, LOCATION, MODEL_NAME


def _try_on_single(credentials, url: str, person_bytes: bytes, garment_bytes: bytes) -> bytes:
    # Kepek base64 kodolasa – az API csak szoveges formatumot fogad
    payload = {
        "instances": [
            {
                "personImage": {
                    "image": {
                        "bytesBase64Encoded": base64.b64encode(person_bytes).decode("utf-8")
                    }
                },
                "productImages": [
                    {
                        "image": {
                            "bytesBase64Encoded": base64.b64encode(garment_bytes).decode("utf-8")
                        }
                    }
                ],
            }
        ],
        # baseSteps: minnel magasabb, annal jobb a minoseg, de lassabb a valasz
        "parameters": {"baseSteps": 10},
    }

    response = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=120,
    )
    response.raise_for_status()

    # Generalt kep kinyerese es dekodolasa
    result = response.json()
    return base64.b64decode(result["predictions"][0]["bytesBase64Encoded"])


def run_virtual_tryon(person_image_bytes: bytes, garment_images_bytes: list[bytes]) -> bytes:
    # ADC token lekerdese – a Cloud Run-on a Service Account vegzi automatikusan
    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())

    # Agent Platform predict endpoint URL-je
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        f"/projects/{PROJECT_ID}/locations/{LOCATION}"
        f"/publishers/google/models/{MODEL_NAME}:predict"
    )

    # Lancolt probafuelke: minden ruhadarabot egymasutan probaljuk fel,
    # az elozo eredmenykepet hasznalva szemelykepkent a kovetkezo korben
    current_person = person_image_bytes
    for garment_bytes in garment_images_bytes:
        current_person = _try_on_single(credentials, url, current_person, garment_bytes)

    return current_person
