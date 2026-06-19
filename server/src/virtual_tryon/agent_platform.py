import base64
import copy
import google.auth
import google.auth.transport.requests
import requests
from .config import PROJECT_ID, LOCATION, MODEL_NAME


def sanitize_model_response(data, max_preview: int = 60) -> dict | list | str | int | float | bool | None:
    # Base64 mezok roviditese – olvashato log es UI szamara
    if isinstance(data, dict):
        return {key: sanitize_model_response(value, max_preview) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_model_response(item, max_preview) for item in data]
    if isinstance(data, str) and len(data) > max_preview:
        return f"{data[:max_preview]}... [{len(data)} chars, truncated]"
    return data


def _try_on_single(
    credentials, url: str, person_bytes: bytes, garment_bytes: bytes
) -> tuple[bytes, dict]:
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
    image_bytes = base64.b64decode(result["predictions"][0]["bytesBase64Encoded"])
    return image_bytes, result


def run_virtual_tryon(
    person_image_bytes: bytes, garment_images_bytes: list[bytes]
) -> tuple[bytes, list[dict]]:
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
    model_responses: list[dict] = []
    for index, garment_bytes in enumerate(garment_images_bytes, start=1):
        current_person, api_response = _try_on_single(credentials, url, current_person, garment_bytes)
        model_responses.append({"garment_index": index, "response": copy.deepcopy(api_response)})

    return current_person, model_responses
