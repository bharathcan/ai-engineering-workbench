#!/bin/bash
# Setup script to populate example requirements for the assignment

API_URL="${API_URL:-http://localhost:8000}"
DELAY="${DELAY:-1}"  # Delay between requests to avoid race conditions

echo "🚀 Setting up AI Engineering Workbench examples..."
echo "API URL: $API_URL"
echo ""

# Function to create a requirement
create_requirement() {
  local title=$1
  local text=$2

  echo "📝 Creating: $title"
  curl -s -X POST "$API_URL/api/v1/requirements" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$text\"}" | jq '.'
  echo ""
  sleep $DELAY
}

echo "=================================================="
echo "SCENARIO A: GREENFIELD (New System Development)"
echo "=================================================="
create_requirement "URL Shortener Service" \
  "Build a scalable URL shortener service with REST APIs, persistence, and analytics. Users should be able to create short links from long URLs, redirect through short links, and view click-through analytics. The service must scale to handle 100k requests per second with <100ms latency."

echo ""
echo "=================================================="
echo "SCENARIO B: BROWNFIELD (Performance Optimization)"
echo "=================================================="
create_requirement "Performance Optimization" \
  "Optimize the URL shortener's database query performance. Current redirect lookup takes >200ms at 10k req/s. Target <50ms latency at 100k req/s with <1% error rate. Maintain API compatibility and backward compatibility with existing clients. Consider indexing strategies, connection pooling, query optimization, and caching layers."

echo ""
echo "=================================================="
echo "SCENARIO C: AMBIGUOUS (Vague Specification)"
echo "=================================================="
create_requirement "Analytics Enhancement" \
  "Add analytics to the shortener. Track user behavior for insights. We need better visibility into how users are using the service."

echo ""
echo "✅ Example requirements created!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:5173 in your browser"
echo "2. Select each requirement from the dropdown"
echo "3. Follow the workflow: Analyze → Plan → Execute → Artifacts → Report"
echo ""
echo "For the ambiguous requirement, you'll be asked to clarify what 'insights' means"
echo "Try answering with: 'Track daily click counts by country and device type, store in same DB'"
