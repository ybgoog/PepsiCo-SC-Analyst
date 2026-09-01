#!/bin/bash
# ==============================================================================
# 1-Click Cloud Shell Deploy & Registration for Gemini Enterprise
# Project: gmi-ccai-insights
# ==============================================================================

set -e

PROJECT_ID="gmi-ccai-insights"
REGION="us-central1"
SERVICE_NAME="pepsico-sc-agent"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "================================================================================"
echo "  Deploying PepsiCo Supply Chain Agent to Project: $PROJECT_ID"
echo "================================================================================"

gcloud config set project "$PROJECT_ID" --quiet

# 1. Enable Required Services
echo "[*] Enabling required Google Cloud APIs (Cloud Run, Cloud Build, Artifact Registry)..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com --quiet || true

# 2. Configure Service Account Permissions
echo "[*] Configuring Cloud Build & Compute service account permissions..."
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectViewer" --quiet || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.admin" --quiet || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder" --quiet || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/storage.objectViewer" --quiet || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/storage.admin" --quiet || true

# 3. Clean clone repository
echo "[*] Fetching latest agent codebase from GitHub..."
rm -rf PepsiCo-SC-Analyst
git clone https://github.com/ybgoog/PepsiCo-SC-Analyst.git
cd PepsiCo-SC-Analyst

# 4. Build Container Image with Cloud Build
echo "[*] Building container image with Google Cloud Build..."
gcloud builds submit --tag "$IMAGE_TAG" --quiet

# 5. Deploy Image to Cloud Run
echo "[*] Deploying container image to Cloud Run ($SERVICE_NAME)..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --quiet

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")"

echo ""
echo "================================================================================"
echo "  [SUCCESS] PepsiCo SC Agent Deployed to Cloud Run!"
echo "  Live Service URL: $SERVICE_URL"
echo "  OpenAPI Spec URL: $SERVICE_URL/openapi.json"
echo "================================================================================"
echo ""
echo "  NEXT STEP IN GEMINI ENTERPRISE (AGENTS TAB):"
echo "  1. Go to: https://console.cloud.google.com/gemini-enterprise/locations/global/engines/gemini-enterprise-17624298_1762429821316/agentic/agents?project=$PROJECT_ID"
echo "  2. Go to Tools > Create Tool > OpenAPI > Enter URL: $SERVICE_URL/openapi.json"
echo "  3. Create Agent > Select Tool > Publish!"
echo "================================================================================"
