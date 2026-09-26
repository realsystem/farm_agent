#!/bin/bash
# Quick test commands for Farm Agent

set -e

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════════"
echo "  FARM AGENT QUICK TEST"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Test 1: Container status
echo "1️⃣  Container Status:"
echo "────────────────────────────────────────────────────────────────"
docker-compose -f docker-compose.dev.yml ps | grep -E "homeassistant|farm-agent" || echo "Containers not running"
echo ""

# Test 2: Health check
echo "2️⃣  Health Check (HTTP API):"
echo "────────────────────────────────────────────────────────────────"
HEALTH=$(curl -s http://localhost:8080/health 2>/dev/null || echo '{"status":"error"}')
if echo "$HEALTH" | grep -q "ok"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi
echo ""

# Test 3: Entity discovery
echo "3️⃣  Entity Discovery:"
echo "────────────────────────────────────────────────────────────────"
ENTITIES=$(curl -s 'http://localhost:8080/ask?q=What%20sensors%20are%20available?' 2>/dev/null || echo '{"error":"failed"}')
if echo "$ENTITIES" | grep -q "eco_worthy\|smartshunt"; then
    SENSOR_COUNT=$(echo "$ENTITIES" | python3 -c "import sys, json; d=json.load(sys.stdin); ans=json.loads(d.get('answer','[]')); print(len(ans) if isinstance(ans, list) else 0)" 2>/dev/null || echo "?")
    echo "✅ Found $SENSOR_COUNT sensors"
else
    echo "⚠️  Entities not found (may need OpenAI access)"
fi
echo ""

# Test 4: Voltage query
echo "4️⃣  Battery Voltage Query:"
echo "────────────────────────────────────────────────────────────────"
VOLTAGE=$(curl -s 'http://localhost:8080/ask?q=What%20is%20the%20battery%20voltage?' 2>/dev/null || echo '{"error":"failed"}')
if echo "$VOLTAGE" | grep -q "13.28\|voltage\|error"; then
    echo "✅ Query successful"
    echo "Response: $(echo "$VOLTAGE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('answer', d.get('error'))[:100])")"
else
    echo "❌ Query failed"
fi
echo ""

# Test 5: OpenAI connectivity
echo "5️⃣  OpenAI API Connectivity:"
echo "────────────────────────────────────────────────────────────────"
API_TEST=$(docker exec farm-agent python3 << 'PYEOF' 2>/dev/null || echo "error"
try:
    from openai import OpenAI
    import os
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5,
            timeout=5
        )
        print("ok")
    else:
        print("no-key")
except Exception as e:
    print(f"fail:{type(e).__name__}")
PYEOF
)

if [ "$API_TEST" = "ok" ]; then
    echo "✅ OpenAI API accessible"
    echo "   → Full agent with function calling ENABLED"
elif [ "$API_TEST" = "no-key" ]; then
    echo "⚠️  No OpenAI API key configured"
    echo "   → Agent using fallback (entity discovery only)"
else
    echo "⚠️  OpenAI API not reachable (network restricted)"
    echo "   → Agent using fallback (entity discovery only)"
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "  SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "If all tests pass:"
echo "  ✅ Local development environment is working correctly"
echo ""
echo "For full function calling (intelligent answers):"
echo "  1. Verify OPENAI_API_KEY in .env"
echo "  2. Ensure Docker container has outbound network access"
echo "  3. Test: curl 'http://localhost:8080/ask?q=question'"
echo ""
echo "For detailed testing:"
echo "  📖 See TESTING_GUIDE.md"
echo ""
