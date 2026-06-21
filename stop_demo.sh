#!/bin/bash

# Blue Grid Demo Stopper
# Kills all services started by start_demo.command

echo "Stopping Blue Grid services..."

# Kill processes on specific ports
for port in 8000 5001 5002; do
    PIDS=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
        echo "  Killing processes on port $port..."
        echo "$PIDS" | xargs kill -9 2>/dev/null
    fi
done

# Also kill by process name as fallback
pkill -f "python.*redis_api.py" 2>/dev/null
pkill -f "python.*anthropic_proxy.py" 2>/dev/null
pkill -f "python.*http.server 8000" 2>/dev/null

echo "✓ All services stopped"
echo ""
echo "To restart, run: ./start_demo.command"
