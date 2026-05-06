#!/bin/bash
# ClimateWise - NOAA Degradation Test for Unified Pricing
# Valida continuidade operacional do Unified Pricing sob degradação controlada dos parâmetros NOAA.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SERVER_ROOT="$PROJECT_ROOT/server"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
SERVER_LOG_FILE="${SERVER_LOG_FILE:-/tmp/climatewise_server.log}"
API_URL="${API_URL:-http://localhost:8000/api/v1/unified-pricing/calculate}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
REPORT_DIR="${REPORT_DIR:-$PROJECT_ROOT/reports/dr}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REPORT_MD="$REPORT_DIR/noaa_degradation_report_$TIMESTAMP.md"
SUMMARY_JSON="$REPORT_DIR/noaa_degradation_summary_$TIMESTAMP.json"

ORIG_NOAA_RISK_BLEND_WEIGHT="${NOAA_RISK_BLEND_WEIGHT-__UNSET__}"
ORIG_NOAA_PREMIUM_MAX_IMPACT="${NOAA_PREMIUM_MAX_IMPACT-__UNSET__}"

mkdir -p "$REPORT_DIR"

wait_for_health() {
    local max_attempts="${1:-60}"
    local delay_seconds="${2:-1}"

    for i in $(seq 1 "$max_attempts"); do
        code="$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")"
        if [[ "$code" == "200" ]]; then
            return 0
        fi
        sleep "$delay_seconds"
    done

    return 1
}

extract_json_field() {
    local file_path="$1"
    local dotted_path="$2"

    python3 - "$file_path" "$dotted_path" <<'PY'
import json
import sys

file_path = sys.argv[1]
path = sys.argv[2].split('.')

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cur = data
    for p in path:
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            cur = None
            break
    if isinstance(cur, (dict, list)):
        print(json.dumps(cur, ensure_ascii=True))
    elif cur is None:
        print("")
    else:
        print(cur)
except Exception:
    print("")
PY
}

restart_backend_with_env() {
    local blend_weight="$1"
    local max_impact="$2"

    pkill -f "uvicorn.*main:app" >/dev/null 2>&1 || true
    sleep 1

    (
        cd "$SERVER_ROOT"
        export PYTHONPATH="$SERVER_ROOT:$PROJECT_ROOT"
        if [[ "$blend_weight" == "__UNSET__" && "$max_impact" == "__UNSET__" ]]; then
            unset NOAA_RISK_BLEND_WEIGHT NOAA_PREMIUM_MAX_IMPACT
        else
            export NOAA_RISK_BLEND_WEIGHT="$blend_weight"
            export NOAA_PREMIUM_MAX_IMPACT="$max_impact"
        fi

        "$VENV_PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000 >>"$SERVER_LOG_FILE" 2>&1 &
    )

    if ! wait_for_health 120 1; then
        echo "ERROR: backend health check failed after restart" >&2
        return 1
    fi
}

is_close_number() {
    local expected="$1"
    local actual="$2"

    python3 - "$expected" "$actual" <<'PY'
import math
import sys

try:
    e = float(sys.argv[1])
    a = float(sys.argv[2])
    print("true" if math.isclose(e, a, rel_tol=1e-9, abs_tol=1e-9) else "false")
except Exception:
    print("false")
PY
}

run_case() {
    local case_name="$1"
    local blend_weight="$2"
    local max_impact="$3"
    local response_file="$REPORT_DIR/noaa_degradation_${case_name// /_}_$TIMESTAMP.json"

    restart_backend_with_env "$blend_weight" "$max_impact"

    local http_code
                http_code="$(curl -sS --connect-timeout 5 --max-time 120 -o "$response_file" -w "%{http_code}" -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -d '{
        "coverage_amount": 100000,
        "location_latitude": -23.5505,
        "location_longitude": -46.6333,
        "risk_factors": {
          "climatic_risk": 0.3,
          "economic_risk": 0.2,
          "location_risk": 0.25
                },
                "models_to_use": ["dynamic", "climate", "bayesian"]
      }')"

    local eff_blend
    local eff_impact
    local combined_risk
    local recommended_premium
    local warnings

    eff_blend="$(extract_json_field "$response_file" "explanation.noaa_blend_parameters.noaa_risk_blend_weight")"
    eff_impact="$(extract_json_field "$response_file" "explanation.noaa_blend_parameters.noaa_premium_max_impact")"
    combined_risk="$(extract_json_field "$response_file" "combined_risk_score")"
    recommended_premium="$(extract_json_field "$response_file" "recommended_premium")"
    warnings="$(extract_json_field "$response_file" "warnings")"

    local pass_http="false"
    local pass_params="false"

    [[ "$http_code" == "200" ]] && pass_http="true"

    if [[ "$blend_weight" != "__UNSET__" && "$max_impact" != "__UNSET__" ]]; then
        if [[ "$(is_close_number "$blend_weight" "$eff_blend")" == "true" && "$(is_close_number "$max_impact" "$eff_impact")" == "true" ]]; then
            pass_params="true"
        fi
    else
        pass_params="true"
    fi

    printf '%s\n' "{"
    printf '  "case": "%s",\n' "$case_name"
    printf '  "http_code": "%s",\n' "$http_code"
    printf '  "pass_http": %s,\n' "$pass_http"
    printf '  "pass_params": %s,\n' "$pass_params"
    printf '  "configured_noaa_risk_blend_weight": "%s",\n' "$blend_weight"
    printf '  "configured_noaa_premium_max_impact": "%s",\n' "$max_impact"
    printf '  "effective_noaa_risk_blend_weight": "%s",\n' "$eff_blend"
    printf '  "effective_noaa_premium_max_impact": "%s",\n' "$eff_impact"
    printf '  "combined_risk_score": "%s",\n' "$combined_risk"
    printf '  "recommended_premium": "%s",\n' "$recommended_premium"
    printf '  "warnings": %s,\n' "${warnings:-[]}" 
    printf '  "response_file": "%s"\n' "$response_file"
    printf '%s\n' "}"
}

cleanup_restore_baseline() {
    set +e
    if [[ "$ORIG_NOAA_RISK_BLEND_WEIGHT" == "__UNSET__" && "$ORIG_NOAA_PREMIUM_MAX_IMPACT" == "__UNSET__" ]]; then
        restart_backend_with_env "__UNSET__" "__UNSET__"
    else
        restart_backend_with_env "$ORIG_NOAA_RISK_BLEND_WEIGHT" "$ORIG_NOAA_PREMIUM_MAX_IMPACT"
    fi

    if [[ $? -ne 0 ]]; then
        echo "WARNING: failed to restore backend baseline NOAA env after test" >&2
    fi
}

trap cleanup_restore_baseline EXIT

LIGHT_CASE_JSON="$(run_case "degradacao_leve" "0.10" "0.08")"
STRONG_CASE_JSON="$(run_case "degradacao_forte" "0.00" "0.00")"

printf '%s\n' "{" > "$SUMMARY_JSON"
printf '  "timestamp": "%s",\n' "$(date -Iseconds)" >> "$SUMMARY_JSON"
printf '  "api_url": "%s",\n' "$API_URL" >> "$SUMMARY_JSON"
printf '  "health_url": "%s",\n' "$HEALTH_URL" >> "$SUMMARY_JSON"
printf '  "light": %s,\n' "$LIGHT_CASE_JSON" >> "$SUMMARY_JSON"
printf '  "strong": %s\n' "$STRONG_CASE_JSON" >> "$SUMMARY_JSON"
printf '%s\n' "}" >> "$SUMMARY_JSON"

LIGHT_HTTP="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["light"]["pass_http"])' "$SUMMARY_JSON")"
LIGHT_PARAMS="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["light"]["pass_params"])' "$SUMMARY_JSON")"
STRONG_HTTP="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["strong"]["pass_http"])' "$SUMMARY_JSON")"
STRONG_PARAMS="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["strong"]["pass_params"])' "$SUMMARY_JSON")"

cat > "$REPORT_MD" <<EOF
# NOAA Degradation Test Report

- Timestamp: $(date -Iseconds)
- API: $API_URL
- Health: $HEALTH_URL
- Summary JSON: $SUMMARY_JSON

## Acceptance Results

| Scenario | HTTP 200 | NOAA Params Applied |
|---|---|---|
| Degradação leve (0.10 / 0.08) | $LIGHT_HTTP | $LIGHT_PARAMS |
| Degradação forte (0.00 / 0.00) | $STRONG_HTTP | $STRONG_PARAMS |

## Evidence Files

- $(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["light"]["response_file"])' "$SUMMARY_JSON")
- $(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["strong"]["response_file"])' "$SUMMARY_JSON")

## Notes

- Este teste valida disponibilidade do endpoint e aplicação dos parâmetros NOAA via ambiente.
- Evidência de fallback neutro por indisponibilidade real do NOAA depende do cenário de conectividade no momento do teste.
EOF

if [[ "$LIGHT_HTTP" == "True" && "$LIGHT_PARAMS" == "True" && "$STRONG_HTTP" == "True" && "$STRONG_PARAMS" == "True" ]]; then
    echo "PASS: NOAA degradation test completed"
    echo "Report: $REPORT_MD"
    echo "Summary: $SUMMARY_JSON"
    exit 0
fi

echo "FAIL: NOAA degradation test failed (check report and summary)"
echo "Report: $REPORT_MD"
echo "Summary: $SUMMARY_JSON"
exit 1
