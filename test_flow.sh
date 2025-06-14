#!/bin/bash

# ==============================================================================
# Storyteller API End-to-End Test Script
# ==============================================================================
# This script simulates a full user flow:
# 1. Generates a new story with a specific prompt.
# 2. Extracts the story text and arc from the response.
# 3. Sends a complex refinement request using the generated story as context.
#
# Requirements:
# - curl: For making HTTP requests.
# - jq: For parsing JSON responses. (brew install jq / apt-get install jq)
#
# Usage:
# 1. Make sure the backend server is running.
# 2. Run this script from your terminal: ./test_flow.sh
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
BASE_URL="http://localhost:8000"
CHAT_ENDPOINT="$BASE_URL/chat"
REFINE_ENDPOINT="$BASE_URL/refine-with-feedback"

# --- Test Data ---
INITIAL_PROMPT="A story about a brave knight named Bob and his friend, a grumpy gnome."
REFINEMENT_REQUEST="Can you change Bob's name to Sir Reginald and make the gnome a friendly dragon instead?"

# --- Helper function for logging ---
log() {
    echo "=============================================================================="
    echo "➡️  $1"
    echo "=============================================================================="
}

# --- Step 1: Generate the Initial Story ---
log "STEP 1: GENERATING A NEW STORY"
echo "  - Sending prompt to $CHAT_ENDPOINT:"
echo "    '$INITIAL_PROMPT'"

# Send the request and capture the response
CHAT_RESPONSE=$(curl -s -X POST "$CHAT_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"$INITIAL_PROMPT\"}")

# Check if the response contains an error
if echo "$CHAT_RESPONSE" | jq -e '.detail' > /dev/null; then
    echo "❌ ERROR: Story generation failed."
    echo "   Response: $(echo "$CHAT_RESPONSE" | jq)"
    exit 1
fi

# Extract the story and arc using jq
ORIGINAL_STORY=$(echo "$CHAT_RESPONSE" | jq -r '.response')
STORY_ARC=$(echo "$CHAT_RESPONSE" | jq '.story_arc')

if [ -z "$ORIGINAL_STORY" ] || [ "$STORY_ARC" == "null" ]; then
    echo "❌ ERROR: Failed to parse story or arc from the chat response."
    echo "   Response: $CHAT_RESPONSE"
    exit 1
fi

log "STEP 1: SUCCESS"
echo "  - Generated Story (first 100 chars): ${ORIGINAL_STORY:0:100}..."
echo "  - Story Arc captured successfully."
echo ""

# --- Step 2: Refine the Generated Story ---
log "STEP 2: REFINING THE STORY"
echo "  - Sending refinement request to $REFINE_ENDPOINT:"
echo "    '$REFINEMENT_REQUEST'"

# Use jq to safely construct the JSON payload with the variables
REFINEMENT_PAYLOAD=$(jq -n \
                  --arg feedback "$REFINEMENT_REQUEST" \
                  --arg story "$ORIGINAL_STORY" \
                  --argjson arc "$STORY_ARC" \
                  '{user_feedback: $feedback, original_story: $story, story_arc: $arc}')

# Send the refinement request
REFINE_RESPONSE=$(curl -s -X POST "$REFINE_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d "$REFINEMENT_PAYLOAD")

if echo "$REFINE_RESPONSE" | jq -e '.detail' > /dev/null; then
    echo "❌ ERROR: Story refinement failed."
    echo "   Response: $(echo "$REFINE_RESPONSE" | jq)"
    exit 1
fi

REFINED_STORY=$(echo "$REFINE_RESPONSE" | jq -r '.response')

log "STEP 2: SUCCESS"
echo ""

# --- Step 3: Display Final Result ---
log "FINAL REFINED STORY"
echo "$REFINED_STORY"
echo ""

log "TEST COMPLETE" 