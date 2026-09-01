#!/bin/bash
# ==============================================================================
# 1-Click Cloud Shell Deploy for Gemini Enterprise
# Project: gmi-ccai-insights
# ==============================================================================

set -e

PROJECT_ID="gmi-ccai-insights"
REGION="us-central1"
SERVICE_NAME="pepsico-sc-agent"
AR_REPO="pepsico-docker"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${SERVICE_NAME}:latest"

echo "================================================================================"
echo "  PepsiCo SC Agent → Cloud Run (Project: $PROJECT_ID)"
echo "================================================================================"

gcloud config set project "$PROJECT_ID" --quiet

# ── Step 1: Enable APIs ──
echo "[1/7] Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --quiet 2>/dev/null || true

# ── Step 2: Create Artifact Registry repo if it doesn't exist ──
echo "[2/7] Ensuring Artifact Registry Docker repository exists..."
gcloud artifacts repositories create "$AR_REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="PepsiCo SC Agent container images" \
    --quiet 2>/dev/null || echo "    (Repository already exists, continuing)"

# ── Step 3: Grant permissions ──
echo "[3/7] Granting service account permissions..."
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SA_COMPUTE="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_COMPUTE}" \
    --role="roles/artifactregistry.writer" --quiet --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_COMPUTE}" \
    --role="roles/storage.admin" --quiet --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_COMPUTE}" \
    --role="roles/logging.logWriter" --quiet --condition=None 2>/dev/null || true

echo "    Waiting 10s for IAM propagation..."
sleep 10

# ── Step 4: Clone repo ──
echo "[4/7] Cloning latest codebase..."
rm -rf PepsiCo-SC-Analyst
git clone https://github.com/ybgoog/PepsiCo-SC-Analyst.git
cd PepsiCo-SC-Analyst

# ── Step 5: Configure Docker for Artifact Registry ──
echo "[5/7] Configuring Docker authentication for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet 2>/dev/null || true

# ── Step 6: Build container with Cloud Build ──
echo "[6/7] Building container image via Cloud Build..."
gcloud builds submit --tag "$IMAGE_TAG" --quiet --timeout=600

# ── Step 7: Deploy to Cloud Run ──
echo "[7/7] Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --quiet

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
