import base64
import json
import time
from io import BytesIO

import google.auth
import google.auth.transport.requests
import requests
from PIL import Image

from .config import PROJECT_ID, LOCATION, MODEL_NAME

# A képzéshez mutatott JSON vaz – a tenyleges base64 helyett leiras szerepel
REQUEST_BODY_TEMPLATE = {
    "instances": [
        {
            "personImage": {"image": {"bytesBase64Encoded": "<base64 string – a feltoltott szemelykep>"}},
            "productImages": [{"image": {"bytesBase64Encoded": "<base64 string – a ruhadarab kepe>"}}],
        }
    ],
    "parameters": {"baseSteps": 10},
}

RESPONSE_BODY_TEMPLATE = {
    "predictions": [
        {
            "mimeType": "image/png",
            "bytesBase64Encoded": "<base64 string – az AI altal generalt kep>",
        }
    ]
}


def describe_image(image_bytes: bytes) -> dict:
    # Kep metaadatok – a hallgatok latjak a bemenet/kimenet meretet formatum nelkul base64 nelkul
    with Image.open(BytesIO(image_bytes)) as img:
        return {
            "format": img.format,
            "width": img.width,
            "height": img.height,
            "size_bytes": len(image_bytes),
            "size_human": _human_size(len(image_bytes)),
        }


def _human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def _try_on_single(
    credentials,
    url: str,
    person_bytes: bytes,
    garment_bytes: bytes,
    *,
    garment_index: int,
    uses_previous_result_as_person: bool,
) -> tuple[bytes, dict]:
    parameters = {"baseSteps": 10}
    started_at = time.perf_counter()

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
        "parameters": parameters,
    }

    response = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=120,
    )
    duration_seconds = round(time.perf_counter() - started_at, 2)
    response.raise_for_status()

    result = response.json()
    image_bytes = base64.b64decode(result["predictions"][0]["bytesBase64Encoded"])

    return image_bytes, {
        "garment_index": garment_index,
        "chain_note": _chain_note(garment_index, uses_previous_result_as_person),
        "duration_seconds": duration_seconds,
        "request": _build_request_summary(url, parameters, person_bytes, garment_bytes),
        "response": _build_response_summary(response.status_code, result, image_bytes),
    }


def _chain_note(garment_index: int, uses_previous_result_as_person: bool) -> str:
    if garment_index == 1:
        return "Az eredeti feltoltott szemelykep kerul a modellnek."
    if uses_previous_result_as_person:
        return "A szemelykep helyett az elozo kor AI altal generalt kepe megy be (lancolt probafuelke)."
    return "Kovetkezo ruhadarab probafelvetele."


def _build_request_summary(url: str, parameters: dict, person_bytes: bytes, garment_bytes: bytes) -> dict:
    return {
        "method": "POST",
        "endpoint": url,
        "model": MODEL_NAME,
        "parameters": parameters,
        "body_shape": REQUEST_BODY_TEMPLATE,
        "inputs": {
            "person_image": describe_image(person_bytes),
            "product_image": describe_image(garment_bytes),
        },
    }


def _build_response_summary(http_status: int, api_body: dict, image_bytes: bytes) -> dict:
    prediction = api_body.get("predictions", [{}])[0]
    return {
        "http_status": http_status,
        "body_shape": RESPONSE_BODY_TEMPLATE,
        "predictions_count": len(api_body.get("predictions", [])),
        "generated_image": {
            "mimeType": prediction.get("mimeType", "image/png"),
            **describe_image(image_bytes),
        },
    }


def _build_summary_base(garment_count: int) -> dict:
    return {
        "model": MODEL_NAME,
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "garment_count": garment_count,
    }


def _build_summary(garment_calls: list[dict], garment_count: int, total_started_at: float) -> dict:
    return {
        **_build_summary_base(garment_count),
        "total_duration_seconds": round(time.perf_counter() - total_started_at, 2),
        "garment_calls": garment_calls,
    }


def _log_stream_event(event: dict) -> None:
    event_type = event.get("type")
    if event_type == "started":
        print(f"INFO: {MODEL_NAME} API summary started: {json.dumps(event['model_summary'], ensure_ascii=False)}")
        return
    if event_type == "progress":
        garment_index = event.get("garment_index")
        print(
            f"INFO: {MODEL_NAME} API summary (garment {garment_index}): "
            f"{json.dumps(event['call_summary'], ensure_ascii=False)}"
        )
        return
    if event_type == "complete":
        print(
            f"INFO: {MODEL_NAME} API summary (complete): "
            f"{json.dumps(event['model_summary'], ensure_ascii=False)}"
        )


def iter_virtual_tryon(person_image_bytes: bytes, garment_images_bytes: list[bytes]):
    # ADC token lekerdese – a Cloud Run-on a Service Account vegzi automatikusan
    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())

    # Agent Platform predict endpoint URL-je
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1"
        f"/projects/{PROJECT_ID}/locations/{LOCATION}"
        f"/publishers/google/models/{MODEL_NAME}:predict"
    )

    garment_count = len(garment_images_bytes)
    total_started_at = time.perf_counter()
    garment_calls: list[dict] = []

    started_event = {
        "type": "started",
        "model_summary": _build_summary([], garment_count, total_started_at),
    }
    _log_stream_event(started_event)
    yield started_event

    # Lancolt probafuelke: minden ruhadarabot egymasutan probaljuk fel,
    # az elozo eredmenykepet hasznalva szemelykepkent a kovetkezo korben
    current_person = person_image_bytes
    for index, garment_bytes in enumerate(garment_images_bytes, start=1):
        current_person, call_summary = _try_on_single(
            credentials,
            url,
            current_person,
            garment_bytes,
            garment_index=index,
            uses_previous_result_as_person=index > 1,
        )
        garment_calls.append(call_summary)

        model_summary = _build_summary(garment_calls, garment_count, total_started_at)
        progress_event = {
            "type": "progress",
            "garment_index": index,
            "call_summary": call_summary,
            "model_summary": model_summary,
        }
        _log_stream_event(progress_event)
        yield progress_event

    final_summary = _build_summary(garment_calls, garment_count, total_started_at)
    complete_event = {
        "type": "complete",
        "model_summary": final_summary,
    }
    _log_stream_event(complete_event)
    yield complete_event, current_person


def run_virtual_tryon(person_image_bytes: bytes, garment_images_bytes: list[bytes]) -> bytes:
    result_image = None
    for event in iter_virtual_tryon(person_image_bytes, garment_images_bytes):
        if isinstance(event, tuple):
            _, result_image = event

    if result_image is None:
        raise RuntimeError("Virtual try-on did not produce a result.")

    return result_image
