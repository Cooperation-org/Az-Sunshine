#!/bin/bash
echo "========================================="
echo "Triggering SOI Scrape: $(date)"
echo "========================================="

curl -X POST http://localhost:5000/trigger \
  -H "X-Service-Secret: s0m3R@nd0mS3cret" \
  -H "Content-Type: application/json" \
  -d '{"triggered_by":"cron"}' \
  -w "\nHTTP Status: %{http_code}\n"

echo "========================================="
