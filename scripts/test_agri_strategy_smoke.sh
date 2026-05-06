#!/usr/bin/env bash
# ClimateAI - Agri Strategy smoke test with retry for local instability.

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_PREFIX="${API_PREFIX:-/api/v1}"
MAX_RETRIES="${MAX_RETRIES:-10}"
RETRY_DELAY_SECONDS="${RETRY_DELAY_SECONDS:-2}"
REPORT_DIR="${REPORT_DIR:-./reports/smoke}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REPORT_FILE="${REPORT_DIR}/agri_strategy_smoke_${TIMESTAMP}.json"

HEALTH_URL="${BASE_URL}/health"
AGRI_HEALTH_URL="${BASE_URL}${API_PREFIX}/agri-strategy/health"
AGRI_CATALOG_URL="${BASE_URL}${API_PREFIX}/agri-strategy/catalog"
AGRI_PLAN_URL="${BASE_URL}${API_PREFIX}/agri-strategy/plan"

mkdir -p "${REPORT_DIR}"

wait_for_backend() {
  local attempt=1

  while [[ "${attempt}" -le "${MAX_RETRIES}" ]]; do
    local code
    code="$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" || true)"

    if [[ "${code}" == "200" ]]; then
      return 0
    fi

    echo "[smoke] Backend not ready (attempt ${attempt}/${MAX_RETRIES}, HTTP=${code:-000})"
    sleep "${RETRY_DELAY_SECONDS}"
    attempt=$((attempt + 1))
  done

  return 1
}

retry_curl_json() {
  local method="$1"
  local url="$2"
  local body="${3:-}"

  local attempt=1
  while [[ "${attempt}" -le "${MAX_RETRIES}" ]]; do
    local response
    local code

    if [[ -n "${body}" ]]; then
      response="$(curl -sS -X "${method}" "${url}" -H "Content-Type: application/json" -d "${body}" -w "\n%{http_code}" || true)"
    else
      response="$(curl -sS -X "${method}" "${url}" -w "\n%{http_code}" || true)"
    fi

    code="$(printf "%s" "${response}" | tail -n 1)"
    payload="$(printf "%s" "${response}" | sed '$d')"

    if [[ "${code}" == "200" ]]; then
      printf "%s" "${payload}"
      return 0
    fi

    echo "[smoke] ${method} ${url} failed (attempt ${attempt}/${MAX_RETRIES}, HTTP=${code:-000})"
    sleep "${RETRY_DELAY_SECONDS}"
    attempt=$((attempt + 1))
  done

  return 1
}

if ! wait_for_backend; then
  echo "[smoke] FAIL: backend health endpoint unavailable after retries"
  exit 1
fi

plan_request='{
  "crop_type": "soybean",
  "phenological_stage": "flowering",
  "latitude": -23.55,
  "longitude": -46.63,
  "planning_horizon_days": 120,
  "risk_tolerance": "medium",
  "farm_profile": {
    "irrigation_available": false,
    "drainage_level": "medium",
    "soil_cover_level": "medium"
  }
}'

agri_health_json="$(retry_curl_json GET "${AGRI_HEALTH_URL}")"
catalog_json="$(retry_curl_json GET "${AGRI_CATALOG_URL}")"
plan_json="$(retry_curl_json POST "${AGRI_PLAN_URL}" "${plan_request}")"

python3 - <<'PY' "${agri_health_json}" "${catalog_json}" "${plan_json}" "${REPORT_FILE}"
import json
import sys

agri_health = json.loads(sys.argv[1])
catalog = json.loads(sys.argv[2])
plan = json.loads(sys.argv[3])
report_file = sys.argv[4]

required_plan_keys = [
    "crop_type",
    "phenological_stage",
    "climate_outlook",
    "exposure_scores",
    "operational_actions",
    "financial_actions",
    "alert_triggers",
]

missing_keys = [k for k in required_plan_keys if k not in plan]

report = {
    "status": "PASS" if not missing_keys else "FAIL",
    "checks": {
        "agri_health_status": agri_health.get("status") == "healthy",
        "catalog_supported_crops": isinstance(catalog.get("supported_crops"), list) and len(catalog.get("supported_crops", [])) > 0,
        "catalog_supported_stages": isinstance(catalog.get("supported_stages"), list) and len(catalog.get("supported_stages", [])) > 0,
        "plan_required_keys": not missing_keys,
    },
    "missing_plan_keys": missing_keys,
    "sample_outputs": {
        "agri_health": agri_health,
        "catalog": {
            "supported_crops_count": len(catalog.get("supported_crops", [])),
            "supported_stages_count": len(catalog.get("supported_stages", [])),
        },
        "plan": {
            "crop_type": plan.get("crop_type"),
            "phenological_stage": plan.get("phenological_stage"),
            "risk_tolerance": plan.get("risk_tolerance"),
            "top_exposure_keys": list(plan.get("exposure_scores", {}).keys())[:3],
            "operational_actions_count": len(plan.get("operational_actions", [])),
            "financial_actions_count": len(plan.get("financial_actions", [])),
            "alert_triggers_count": len(plan.get("alert_triggers", [])),
        },
    },
}

with open(report_file, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=True, indent=2)

print(report["status"])
print(report_file)
PY
