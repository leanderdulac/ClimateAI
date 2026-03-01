#!/bin/bash

# Deploy script for Google Cloud Run
# Usage: ./deploy_gcp.sh [PROJECT_ID] [REGION]

set -e

# Default values
SERVICE_NAME="climatewise-backend"
REGION="us-central1"

echo "============================================="
echo "   ClimateWise - Google Cloud Run Deployer     "
echo "============================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null;
then
    echo "❌ Error: gcloud CLI is not installed."
    echo "Please install it: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 1. Setup Project ID
if [ -z "$1" ]; then
    CURRENT_PROJECT=$(gcloud config get-value project)
    echo "Current GCP Project: $CURRENT_PROJECT"
    read -p "Use this project? (y/n): " confirm
    if [[ "$confirm" != "y" ]]; then
        read -p "Enter Google Cloud Project ID: " PROJECT_ID
    else
        PROJECT_ID=$CURRENT_PROJECT
    fi
else
    PROJECT_ID=$1
fi

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: Project ID is required."
    exit 1
fi

# 2. Setup Region
if [ -n "$2" ]; then
    REGION=$2
fi

echo "---------------------------------------------"
echo "Target Configuration:"
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Service: $SERVICE_NAME"
echo "---------------------------------------------"

read -p "Proceed with deployment? (y/n): " proceed
if [[ "$proceed" != "y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# 3. Enable required services
echo ">> Enabling Cloud Build and Cloud Run APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com --project "$PROJECT_ID"

# 4. Submit Build
echo ">> Submitting build to Google Cloud Build..."
cd ../server # Move to server directory where cloudbuild.yaml is
gcloud builds submit --config cloudbuild.yaml \
    --project "$PROJECT_ID" \
    --substitutions=_SERVICE_NAME="$SERVICE_NAME",_REGION="$REGION" .

echo "============================================="
echo "✅ Deployment Process Completed!"
echo "Check the Cloud Run URL above or in the GCP Console."
echo "Don't forget to set your environment variables in Cloud Run:"
echo "  gcloud run services update $SERVICE_NAME --update-env-vars KEY=VALUE"
echo "============================================="
