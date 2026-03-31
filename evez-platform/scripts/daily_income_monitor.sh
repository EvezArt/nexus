#!/bin/bash
# Daily Income Monitor — runs via cron
# Checks all income sources, runs scan, updates projection

echo "=== EVEZ Daily Income Monitor ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M UTC')"

echo "--- Income Scan ---"
curl -s -X POST http://localhost:8080/api/income/scan | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Opportunities found: {data[\"total\"]}')
for opp in data['opportunities'][:5]:
    print(f'  - {opp[\"title\"]}: \${opp[\"estimated_value_usd\"]}/day')
"

echo "--- Market Data ---"
curl -s -X POST http://localhost:8080/api/finance/observe | python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('prices', []):
    chg = p['change_24h']
    print(f'  {p[\"asset\"]}: \${p[\"price_usd\"]:,.0f} ({chg:+.1f}%)')
"

echo "--- Daily Runbook ---"
curl -s http://localhost:8080/api/daily/runbook | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Target: \${data[\"daily_target\"]}/day')
print(f'Expected: \${data[\"plan_expected_total\"]}/day')
print(f'Coverage: {data[\"coverage_pct\"]}%')
print(f'Status: {data[\"status\"]}')
for action in data.get('actions', []):
    print(f'  -> {action[\"source\"]}: \${action[\"expected_income\"]}')
for unlock in data.get('signup_unlocks', [])[:3]:
    print(f'  UNLOCK {unlock[\"source\"]}: {unlock[\"action\"]}')
"

echo "=== Done ==="
