#!/bin/bash
# ==============================================================================
# 1-Click Cloud Shell Deploy & Registration for Gemini Enterprise
# Project: gmi-ccai-insights
# ==============================================================================

set -e

PROJECT_ID="gmi-ccai-insights"
REGION="us-central1"
SERVICE_NAME="pepsico-sc-agent"

echo "================================================================================"
echo "  Deploying PepsiCo Supply Chain Agent to Project: $PROJECT_ID"
echo "================================================================================"

gcloud config set project "$PROJECT_ID"

# 1. Clean clone repository
echo "Fetching latest agent codebase..."
rm -rf PepsiCo-SC-Analyst
git clone https://github.com/ybgoog/PepsiCo-SC-Analyst.git
cd PepsiCo-SC-Analyst

# 2. Deploy to Cloud Run
echo "Deploying Cloud Run microservice..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --quiet

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")"

echo ""
echo "================================================================================"
echo "  [SUCCESS] Cloud Run Service Live at:"
echo "  $SERVICE_URL"
echo ""
echo "  OpenAPI Spec URL for Gemini Enterprise:"
echo "  $SERVICE_URL/openapi.json"
echo "================================================================================"
