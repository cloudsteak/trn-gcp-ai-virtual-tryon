import os

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:5173")
MODEL_NAME = os.environ.get("MODEL_NAME", "")
