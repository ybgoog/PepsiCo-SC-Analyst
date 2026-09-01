#!/bin/bash
# ==============================================================================
# 1-Click Cloud Shell Deploy for Gemini Enterprise
# Project: gmi-ccai-insights
# ==============================================================================

set -e

PROJECT_ID="gmi-ccai-insights"
REGION="us-central1"
SERVICE_NAME="pepsico-sc-agent"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "================================================================================"
echo "  PepsiCo SC Agent → Cloud Run (Project: $PROJECT_ID)"
echo "================================================================================"

gcloud config set project "$PROJECT_ID" --quiet

# ── Step 1: Enable APIs ──
echo "[1/6] Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    --quiet 2>/dev/null || true

# ── Step 2: Fix service account permissions ──
echo "[2/6] Granting required permissions to Compute Engine service account..."
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SA_COMPUTE="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
BUCKET="run-sources-${PROJECT_ID}-${REGION}"

# Grant on the specific staging bucket used by Cloud Run
gsutil iam ch "serviceAccount:${SA_COMPUTE}:objectViewer" "gs://${BUCKET}" 2>/dev/null || true
gsutil iam ch "serviceAccount:${SA_COMPUTE}:objectAdmin" "gs://${BUCKET}" 2>/dev/null || true

# Storage admin (project-level fallback)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_COMPUTE}" \
    --role="roles/storage.admin" --quiet --condition=None 2>/dev/null || true

# Artifact Registry writer (needed to push container images to gcr.io)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_COMPUTE}" \
    --role="roles/artifactregistry.writer" --quiet --condition=None 2>/dev/null || true

# Cloud Build logs writer
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_COMPUTE}" \
    --role="roles/logging.logWriter" --quiet --condition=None 2>/dev/null || true

echo "    Waiting 15s for IAM propagation..."
sleep 15

# ── Step 3: Clone repo ──
echo "[3/6] Cloning latest codebase..."
rm -rf PepsiCo-SC-Analyst
git clone https://github.com/ybgoog/PepsiCo-SC-Analyst.git
cd PepsiCo-SC-Analyst

# ── Step 4: Build container with Cloud Build (separate step) ──
echo "[4/6] Building container image via Cloud Build..."
gcloud builds submit --tag "$IMAGE_TAG" --quiet --timeout=600

# ── Step 5: Deploy pre-built image to Cloud Run ──
echo "[5/6] Deploying pre-built image to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --quiet

# ── Step 6: Print result ──
SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")"

echo ""
echo "================================================================================"
echo "  ✅ SUCCESS! Cloud Run service is live."
echo ""
echo "  Service URL:  $SERVICE_URL"
echo "  Health Check: $SERVICE_URL/health"
echo "  OpenAPI Spec: $SERVICE_URL/openapi.json"
echo ""
echo "  NEXT → Register in Gemini Enterprise Agent Builder:"
echo "  https://console.cloud.google.com/gemini-enterprise/locations/global/engines/gemini-enterprise-17624298_1762429821316/agentic/agents?project=$PROJECT_ID"
echo "================================================================================"
