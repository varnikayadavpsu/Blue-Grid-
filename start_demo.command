#!/bin/bash

# Blue Grid Demo Launcher
# Double-click this file on Mac to start the full demo

# Change to the script's directory
cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════╗"
echo "║   BLUE GRID — Water Infrastructure Dashboard  ║"
echo "║   Starting all services...                     ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Store PIDs for cleanup
PIDS=()

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all services...${NC}"
    for pid in "${PIDS[@]}"; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null
        fi
    done
    # Kill any remaining processes on our ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    lsof -ti:5002 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

# Trap Ctrl+C and other termination signals
trap cleanup SIGINT SIGTERM EXIT

# Check if ports are already in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}✗ Port $1 is already in use${NC}"
        echo "  Run: lsof -ti:$1 | xargs kill -9"
        echo "  Or use ./stop_demo.sh to kill all services"
        return 1
    fi
    return 0
}

echo -e "${CYAN}Checking ports...${NC}"
check_port 8000 || exit 1
check_port 5001 || exit 1
check_port 5002 || exit 1
echo -e "${GREEN}✓ All ports available${NC}"
echo ""

# Start HTTP server for dashboard
echo -e "${CYAN}[1/3] Starting web server on port 8000...${NC}"
python3 -m http.server 8000 > /tmp/bluegrid_web.log 2>&1 &
WEB_PID=$!
PIDS+=($WEB_PID)
sleep 1
if ps -p $WEB_PID > /dev/null; then
    echo -e "${GREEN}✓ Web server running (PID: $WEB_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start web server${NC}"
    exit 1
fi

# Start Redis API
echo -e "${CYAN}[2/3] Starting Redis vector search API on port 5001...${NC}"
if [ -f "redis_api.py" ]; then
    python3 redis_api.py > /tmp/bluegrid_redis.log 2>&1 &
    REDIS_PID=$!
    PIDS+=($REDIS_PID)
    sleep 2
    if ps -p $REDIS_PID > /dev/null; then
        echo -e "${GREEN}✓ Redis API running (PID: $REDIS_PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Redis API failed to start (check if Redis server is running)${NC}"
        echo "  See /tmp/bluegrid_redis.log for details"
    fi
else
    echo -e "${YELLOW}⚠ redis_api.py not found, skipping${NC}"
fi

# Start Anthropic proxy
echo -e "${CYAN}[3/3] Starting Anthropic API proxy on port 5002...${NC}"
if [ -f "anthropic_proxy.py" ]; then
    python3 anthropic_proxy.py > /tmp/bluegrid_anthropic.log 2>&1 &
    ANTHROPIC_PID=$!
    PIDS+=($ANTHROPIC_PID)
    sleep 2
    if ps -p $ANTHROPIC_PID > /dev/null; then
        echo -e "${GREEN}✓ Anthropic proxy running (PID: $ANTHROPIC_PID)${NC}"
    else
        echo -e "${RED}✗ Anthropic proxy failed to start${NC}"
        echo "  Make sure config.json has a valid API key"
        echo "  See /tmp/bluegrid_anthropic.log for details"
    fi
else
    echo -e "${YELLOW}⚠ anthropic_proxy.py not found, skipping${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Blue Grid is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "  Dashboard:     ${CYAN}http://localhost:8000${NC}"
echo -e "  Redis API:     ${CYAN}http://localhost:5001${NC}"
echo -e "  Anthropic API: ${CYAN}http://localhost:5002${NC}"
echo ""
echo -e "Logs saved to:"
echo "  /tmp/bluegrid_web.log"
echo "  /tmp/bluegrid_redis.log"
echo "  /tmp/bluegrid_anthropic.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Open browser after a short delay
sleep 2
if command -v open &> /dev/null; then
    echo -e "${CYAN}Opening browser...${NC}"
    open http://localhost:8000
fi

# Wait for user to press Ctrl+C
wait
