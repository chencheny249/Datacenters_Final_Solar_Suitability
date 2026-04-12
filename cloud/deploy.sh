#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="solar-suitability-demo"
REGION="us-central1"
REPOSITORY="solar-images"
IMAGE_NAME="solar-cloud"
SERVICE_NAME="solar-api-demo"
INSTANCE_CONNECTION_NAME="solar-suitability-demo:us-central1:solar-postgis-cloud"

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}"

echo "Building image..."
docker build -f cloud/Dockerfile -t "${IMAGE_URI}" .

echo "Pushing image..."
docker push "${IMAGE_URI}"

echo "Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080 \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --env-vars-file cloud/cloudrun.env

echo "Done."