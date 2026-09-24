#!/usr/bin/with-contenv bashio

export OPENAI_API_KEY="$(bashio::config 'openai_api_key')"

echo "================================"
echo "Farm Agent started"
echo "================================"

python3 -u /agent.py