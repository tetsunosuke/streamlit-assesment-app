#!/bin/bash
set -euo pipefail

echo "This script will set up Google Cloud for GitHub Actions Workload Identity Federation."
echo "You will need to provide your Google Cloud Project ID and Project Number."

# --- User Input ---
read -p "Enter your Google Cloud Project ID (e.g., my-project-123): " PROJECT_ID
read -p "Enter your Google Cloud Project Number (e.g., 1234567890): " PROJECT_NUMBER
read -p "Enter your GitHub organization/repository name (e.g., your-org/your-repo): " GITHUB_ORG_REPO

# --- Configuration ---
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
SERVICE_ACCOUNT_ID="github-deployer"
SERVICE_ACCOUNT_DISPLAY_NAME="GitHub Actions Cloud Run Deployer"
GITHUB_ACTIONS_ISSUER="https://token.actions.githubusercontent.com"

echo ""
echo "--- Starting Google Cloud setup ---"

# 1. Enable APIs
echo "1. Enabling required Google Cloud APIs..."
gcloud services enable iam.googleapis.com \
                         sts.googleapis.com \
                         iamcredentials.googleapis.com \
                         cloudbuild.googleapis.com \
                         --project="${PROJECT_ID}"
echo "APIs enabled."

# 2. Create a Workload Identity Pool
echo "2. Creating Workload Identity Pool: ${POOL_ID}..."
gcloud iam workload-identity-pools create "${POOL_ID}" 
  --project="${PROJECT_ID}" 
  --location="global" 
  --display-name="GitHub Actions pool for ${GITHUB_ORG_REPO}" || true # Allow if already exists
echo "Workload Identity Pool created/exists."

# 3. Create a Workload Identity Provider for GitHub
echo "3. Creating Workload Identity Provider: ${PROVIDER_ID}..."
gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" 
  --project="${PROJECT_ID}" 
  --location="global" 
  --workload-identity-pool="${POOL_ID}" 
  --display-name="GitHub Actions provider for ${GITHUB_ORG_REPO}" 
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" 
  --issuer-uri="${GITHUB_ACTIONS_ISSUER}" || true # Allow if already exists
echo "Workload Identity Provider created/exists."

# 4. Get the full resource name of the provider
echo "4. Retrieving Workload Identity Provider resource name..."
WORKLOAD_IDENTITY_PROVIDER=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" 
  --project="${PROJECT_ID}" 
  --location="global" 
  --workload-identity-pool="${POOL_ID}" 
  --format="value(name)")
echo "Workload Identity Provider Resource Name: ${WORKLOAD_IDENTITY_PROVIDER}"

# 5. Create a Service Account for Cloud Run Deployment
echo "5. Creating Service Account: ${SERVICE_ACCOUNT_ID}..."
gcloud iam service-accounts create "${SERVICE_ACCOUNT_ID}" 
  --project="${PROJECT_ID}" 
  --display-name="${SERVICE_ACCOUNT_DISPLAY_NAME}" || true # Allow if already exists
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Service Account Email: ${SERVICE_ACCOUNT_EMAIL}"

# 6. Grant Roles to the Service Account
echo "6. Granting necessary IAM roles to ${SERVICE_ACCOUNT_EMAIL}..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" 
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" 
  --role="roles/run.admin" 
  --role="roles/iam.serviceAccountUser" 
  --role="roles/secretmanager.secretAccessor" 
  --role="roles/storage.admin" 
  --project="${PROJECT_ID}"
echo "IAM roles granted."

# 7. Grant Workload Identity User Role to GitHub Provider
echo "7. Granting Workload Identity User role to GitHub provider for ${GITHUB_ORG_REPO}..."
gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT_EMAIL}" 
  --project="${PROJECT_ID}" 
  --role="roles/iam.workloadIdentityUser" 
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_ORG_REPO}" 
  --project="${PROJECT_ID}"
echo "Workload Identity User role granted."

echo ""
echo "--- Google Cloud setup complete! ---"
echo ""
echo "--- ACTION REQUIRED: Configure GitHub Secrets ---"
echo "Go to your GitHub repository settings: Settings > Secrets and variables > Actions > New repository secret."
echo ""
echo "Add the following secrets:"
echo "  1. GCP_PROJECT_ID: ${PROJECT_ID}"
echo "  2. WORKLOAD_IDENTITY_PROVIDER: ${WORKLOAD_IDENTITY_PROVIDER}"
echo "  3. SERVICE_ACCOUNT_EMAIL: ${SERVICE_ACCOUNT_EMAIL}"
echo ""
echo "Once these secrets are configured in GitHub, your deploy.yml workflow will be able to authenticate and deploy to Cloud Run."
