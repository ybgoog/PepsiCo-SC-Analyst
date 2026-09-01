#!/bin/bash
# ==============================================================================
# Deploy PepsiCo SC Agent to Google Cloud Run for Gemini Enterprise / GEAP
# ==============================================================================

set -e

SERVICE_NAME="pepsico-sc-agent"
REGION="${GCP_REGION:-us-central1}"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null || echo '')"

echo "================================================================================"
echo "  Deploying PepsiCo Supply Chain Agent to Google Cloud Run (GEAP Service)"
echo "  Target Region: $REGION"
echo "  Project ID:    ${PROJECT_ID:-'(Using default gcloud project)'}"
echo "================================================================================"

# Deploy container directly from source using Google Cloud Build & Cloud Run
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-env-vars="PORT=8080"

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")"

echo ""
echo "================================================================================"
echo "  [SUCCESS] GEAP Agent Service Deployed to Google Cloud Run!"
echo "  Service URL: $SERVICE_URL"
echo "  OpenAPI Spec: $SERVICE_URL/openapi.json"
echo ""
echo "  Next Step in Gemini Enterprise / Agentspace:"
echo "  1. Navigate to Gemini Enterprise Agent Builder > Tools > Add Tool"
echo "  2. Select 'Import OpenAPI Specification'"
echo "  3. Paste URL: $SERVICE_URL/openapi.json"
echo "================================================================================"
