import base64
from google import genai
from google.genai import types
from .config import PROJECT_ID, LOCATION


def run_virtual_tryon(person_image_bytes: bytes, garment_image_bytes: bytes) -> bytes:
    # Vertex AI kliens inicializalasa ADC-vel
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )

    # Kepek base64 kodolasa
    person_b64 = base64.b64encode(person_image_bytes).decode("utf-8")
    garment_b64 = base64.b64encode(garment_image_bytes).decode("utf-8")

    # TODO: Toltsd ki a modell nevet a Vertex AI Model Garden adatlapjarol
    response = client.models.generate_content(
        model="",  # <-- ez hianyos szandekosan
        contents=[
            types.Content(
                parts=[
                    types.Part(text="Generate a virtual try-on image."),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type="image/jpeg",
                            data=person_b64,
                        )
                    ),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type="image/jpeg",
                            data=garment_b64,
                        )
                    ),
                ]
            )
        ],
    )

    # Generalt kep kinyerese a valaszbol
    result_part = response.candidates[0].content.parts[0]
    return base64.b64decode(result_part.inline_data.data)
