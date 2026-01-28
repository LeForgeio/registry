#!/bin/bash
# =============================================================================
# Build LeForge Plugin Docker Image with Integration Assets
# 
# This script generates platform integration assets and builds the Docker image
# with those assets bundled for air-gapped distribution.
#
# Usage:
#   ./scripts/build-plugin-image.sh <plugin-name> [docker-tag] [--push]
#
# Examples:
#   ./scripts/build-plugin-image.sh llm-service
#   ./scripts/build-plugin-image.sh crypto-service v2.0.0
#   ./scripts/build-plugin-image.sh llm-service latest --push
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

PLUGIN_NAME="${1:-}"
TAG="${2:-latest}"
PUSH="${3:-}"

if [ -z "$PLUGIN_NAME" ]; then
    echo -e "${RED}Error: Plugin name required${NC}"
    echo "Usage: $0 <plugin-name> [tag] [--push]"
    echo ""
    echo "Available plugins:"
    ls -1 "$ROOT_DIR/plugins" | grep -v README
    exit 1
fi

PLUGIN_DIR="$ROOT_DIR/plugins/$PLUGIN_NAME"

if [ ! -d "$PLUGIN_DIR" ]; then
    echo -e "${RED}Error: Plugin directory not found: $PLUGIN_DIR${NC}"
    exit 1
fi

echo "============================================================"
echo -e "${GREEN}Building LeForge Plugin: $PLUGIN_NAME${NC}"
echo "============================================================"
echo ""

# Step 1: Generate integration assets
echo -e "${YELLOW}Step 1: Generating integration assets...${NC}"

INTEGRATIONS_DIR="$PLUGIN_DIR/integrations"
rm -rf "$INTEGRATIONS_DIR"
mkdir -p "$INTEGRATIONS_DIR"

# Generate for all supported platforms
PLATFORMS=("nintex-cloud" "nintex-k2" "power-automate" "salesforce" "servicenow")

for platform in "${PLATFORMS[@]}"; do
    echo "  Generating $platform..."
    python "$ROOT_DIR/scripts/generate-integrations.py" \
        --plugin "$PLUGIN_NAME" \
        --platform "$platform" \
        --output "$INTEGRATIONS_DIR" \
        2>/dev/null || echo "    (skipped - not supported)"
done

# Copy generated assets into plugin's integrations folder
if [ -d "$ROOT_DIR/integrations" ]; then
    for platform in "${PLATFORMS[@]}"; do
        PLATFORM_DIR="$ROOT_DIR/integrations/$platform"
        # Find the plugin's folder (case-insensitive match)
        PLUGIN_FOLDER=$(find "$PLATFORM_DIR" -maxdepth 1 -type d -iname "*${PLUGIN_NAME//-/}*" 2>/dev/null | head -1)
        if [ -n "$PLUGIN_FOLDER" ] && [ -d "$PLUGIN_FOLDER" ]; then
            mkdir -p "$INTEGRATIONS_DIR/$platform"
            cp -r "$PLUGIN_FOLDER"/* "$INTEGRATIONS_DIR/$platform/" 2>/dev/null || true
        fi
    done
fi

echo -e "${GREEN}  ✓ Integration assets generated${NC}"
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"

IMAGE_NAME="LeForge/$PLUGIN_NAME:$TAG"

docker build \
    --target production \
    -t "$IMAGE_NAME" \
    -f "$PLUGIN_DIR/Dockerfile" \
    "$PLUGIN_DIR"

echo -e "${GREEN}  ✓ Image built: $IMAGE_NAME${NC}"
echo ""

# Step 3: Verify integrations are included
echo -e "${YELLOW}Step 3: Verifying integration assets...${NC}"

docker run --rm "$IMAGE_NAME" ls -la /integrations/ 2>/dev/null || echo "  (verification skipped)"

echo ""

# Step 4: Optional push
if [ "$PUSH" = "--push" ]; then
    echo -e "${YELLOW}Step 4: Pushing to registry...${NC}"
    docker push "$IMAGE_NAME"
    echo -e "${GREEN}  ✓ Pushed: $IMAGE_NAME${NC}"
fi

echo ""
echo "============================================================"
echo -e "${GREEN}Build complete!${NC}"
echo "============================================================"
echo ""
echo "Image: $IMAGE_NAME"
echo ""
echo "To extract integrations for air-gapped deployment:"
echo "  docker run --rm -v \$(pwd)/output:/out $IMAGE_NAME cp -r /integrations /out/"
echo ""
echo "To save image for transfer:"
echo "  docker save $IMAGE_NAME -o ${PLUGIN_NAME}.tar"
