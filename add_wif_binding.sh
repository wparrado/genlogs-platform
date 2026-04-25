#!/usr/bin/env bash
set -euo pipefail
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# --- CONFIG ---
PROJECT_ID="genlogs-494223"
PROJECT_NUMBER="347212169781"
POOL="github-pool"
PROVIDER="github-provider"
SA_EMAIL="github-deployer@genlogs-494223.iam.gserviceaccount.com"
# Set REPO to 'owner/repo' to restrict the binding to a single GitHub repository.
# Leave empty to fall back to provider-based binding.
REPO="wparrado/genlogs-platform"
# MEMBER selection: prefer attribute.repository when REPO is provided.
if [ -n "${REPO}" ]; then
  MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}"
else
  MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
fi
ROLE="roles/iam.workloadIdentityUser"
# ----------------

echo "Checking gcloud..."
if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Install or use Cloud Shell." >&2
  exit 1
fi

echo "Getting current IAM policy for ${SA_EMAIL}..."
gcloud iam service-accounts get-iam-policy "${SA_EMAIL}" --project="${PROJECT_ID}" --format=json > "${TMP_DIR}/policy.json" || echo '{}' > "${TMP_DIR}/policy.json"

echo "Updating policy to add member ${MEMBER} with role ${ROLE}..."
python3 - <<PY
import json, os, sys
pfile = os.path.join("$TMP_DIR", "policy.json")
out = os.path.join("$TMP_DIR", "policy2.json")
with open(pfile, "r") as f:
    try:
        p = json.load(f)
    except Exception:
        p = {}
bindings = p.get("bindings", [])
# ensure members lists exist
found = False
for b in bindings:
    if b.get("role") == "$ROLE":
        members = b.get("members", [])
        if "$MEMBER" not in members:
            members.append("$MEMBER")
            b["members"] = members
        found = True
        break
if not found:
    bindings.append({"role": "$ROLE", "members": ["$MEMBER"]})
p["bindings"] = bindings
with open(out, "w") as f:
    json.dump(p, f)
print("Wrote", out)
PY

echo "Setting updated IAM policy on ${SA_EMAIL}..."
gcloud iam service-accounts set-iam-policy "${SA_EMAIL}" "${TMP_DIR}/policy2.json" --project="${PROJECT_ID}"

echo "Granting Artifact Registry writer to ${SA_EMAIL} on project ${PROJECT_ID}..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer" || true

echo "Verifying bindings for ${SA_EMAIL}:"
gcloud iam service-accounts get-iam-policy "${SA_EMAIL}" --project="${PROJECT_ID}" --format="yaml(bindings)"

echo
echo "Done. Ahora re-ejecuta el workflow. Desde el runner el comando 'gcloud auth print-identity-token' debería devolver un token."