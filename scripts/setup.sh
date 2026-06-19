#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

PROJECT_ID="${GCP_PROJECT_ID:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${GCP_REGION:-europe-west1}"
BACKEND_SERVICE="${BACKEND_SERVICE:-virtual-tryon-server}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-virtual-tryon-client}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-virtual-tryon-sa}"
MODEL_NAME="${MODEL_NAME:-virtual-try-on-001}"
SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Hiba: allitsd be a GCP_PROJECT_ID vagy GOOGLE_CLOUD_PROJECT kornyezeti valtozot."
  exit 1
fi

echo "GCP projekt beallitasa: ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}"

echo "Szukseges API-k engedelyezese..."
gcloud services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com

echo "Service account letrehozasa: ${SERVICE_ACCOUNT}"
if gcloud iam service-accounts describe "${SA_EMAIL}" >/dev/null 2>&1; then
  echo "A service account mar letezik, kihagyva."
else
  gcloud iam service-accounts create "${SERVICE_ACCOUNT}" \
    --display-name="Virtual Try-On Service Account"
fi

wait_for_service_account "${SA_EMAIL}"

echo "IAM szerepkorok hozzarendelese a service accounthoz..."
add_project_iam_binding "${PROJECT_ID}" "serviceAccount:${SA_EMAIL}" "roles/run.invoker"
add_project_iam_binding "${PROJECT_ID}" "serviceAccount:${SA_EMAIL}" "roles/aiplatform.user"

echo "Cloud Run backend service letrehozasa placeholder image-dzsel..."
if gcloud run services describe "${BACKEND_SERVICE}" --region="${REGION}" >/dev/null 2>&1; then
  echo "A backend service mar letezik, kihagyva."
else
  gcloud run deploy "${BACKEND_SERVICE}" \
    --image="gcr.io/cloudrun/hello" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --service-account="${SA_EMAIL}" \
    --quiet
fi

echo "Cloud Run frontend service letrehozasa placeholder image-dzsel..."
if gcloud run services describe "${FRONTEND_SERVICE}" --region="${REGION}" >/dev/null 2>&1; then
  echo "A frontend service mar letezik, kihagyva."
else
  gcloud run deploy "${FRONTEND_SERVICE}" \
    --image="gcr.io/cloudrun/hello" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --service-account="${SA_EMAIL}" \
    --quiet
fi

BACKEND_URL="$(gcloud run services describe "${BACKEND_SERVICE}" --region="${REGION}" --format='value(status.url)')"
FRONTEND_URL="$(gcloud run services describe "${FRONTEND_SERVICE}" --region="${REGION}" --format='value(status.url)')"

echo "Backend kornyezeti valtozok beallitasa..."
gcloud run services update "${BACKEND_SERVICE}" \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},ALLOWED_ORIGIN=${FRONTEND_URL},MODEL_NAME=${MODEL_NAME}"

echo "Frontend kornyezeti valtozok beallitasa..."
gcloud run services update "${FRONTEND_SERVICE}" \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --set-env-vars="VITE_API_URL=${BACKEND_URL}"

echo "Setup kesz."
echo "Backend URL: ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"
echo ""
echo "Kovetkezo lepes: GitHub Actions WIF beallitasa (JSON kulcs nelkul):"
echo "  export GITHUB_REPO=<szervezet>/<repo-nev>"
echo "  ./scripts/setup-wif.sh"
echo "  ./scripts/setup-github.sh"
