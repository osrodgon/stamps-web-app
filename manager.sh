#!/bin/bash

# --- Configuration ---
# Define file locations and service names

NETWORK="stamps-network"

# Get current path and script path
CURRENT_PATH=$(pwd)
SCRIPT_PATH=$(dirname $(readlink -f $0))

echo $SCRIPT_PATH

# Backend Configuration
BACKEND_DIR="backend"
BACKEND_BASE_COMPOSE_FILE="backend/docker-compose.yml"
BACKEND_DEV_COMPOSE_FILE="backend/docker-compose.dev.yml"
BACKEND_TEST_COMPOSE_FILE="backend/docker-compose.test.yml"
BACKEND_PROD_COMPOSE_FILE="backend/docker-compose.prod.yml"
BACKEND_SERVICE="stamps-backend" # Main backend service name (Django)

# Frontend Configuration
FRONTEND_DIR="frontend"
FRONTEND_BASE_COMPOSE_FILE="frontend/docker-compose.yml"
FRONTEND_DEV_COMPOSE_FILE="frontend/docker-compose.dev.yml"
FRONTEND_TEST_COMPOSE_FILE="frontend/docker-compose.test.yml"
FRONTEND_PROD_COMPOSE_FILE="frontend/docker-compose.prod.yml"
FRONTEND_SERVICE="stamps-frontend" # Main frontend service name (e.g., React/Vue container)

# --- Utility Functions ---

# Function to show usage instructions
show_usage() {
    echo "Usage: $0 [dev|test|prod] [start|stop|rebuild|log] "
    echo ""
    echo "Commands:"
    echo "  start     Starts the containers in detached mode (Backend + Frontend)."
    echo "  stop      Stops and removes containers, networks, and volumes."
    echo "  rebuild   Forces a complete image rebuild (no-cache) and restarts the environment."
    echo "  log       Shows the logs for Backend and Frontend in separate GNOME Terminal tabs."
    echo ""
    echo "Environments:"
    echo "  dev       (Backend + Frontend)"
    echo "  test      (Backend only - runs unit tests)"
    echo "  prod      (Backend + Frontend)"
    exit 1
}

# Function to check if any container for the given environment is running
is_env_running() {
    local compose_files=$1
    # Check if 'docker compose ps' finds any running containers
    if docker compose $compose_files ps -q | grep -q '.'; then
        return 0 # Running
    else
        return 1 # Not running
    fi
}

# Function to get the correct override file based on environment
get_compose_files() {
    local env=$1
    local compose_files=""
    
    case "$env" in
        dev)
            # Backend + Frontend for development
            compose_files="-f $BACKEND_BASE_COMPOSE_FILE -f $BACKEND_DEV_COMPOSE_FILE -f $FRONTEND_BASE_COMPOSE_FILE -f $FRONTEND_DEV_COMPOSE_FILE"
            ;;
        test)
            # Backend & frontend as separated parameters for unit tests
            compose_files="-f $BACKEND_TEST_COMPOSE_FILE -f $FRONTEND_TEST_COMPOSE_FILE"
            ;;
        prod)
            # Backend + Frontend for production
            compose_files="-f $BACKEND_BASE_COMPOSE_FILE -f $BACKEND_PROD_COMPOSE_FILE -f $FRONTEND_BASE_COMPOSE_FILE -f $FRONTEND_PROD_COMPOSE_FILE"
            ;;
        *)
            echo "Error: Unknown environment '$env'." >&2
            show_usage
            ;;
    esac
    echo "$compose_files"
}

# --- Action Functions ---

# Function to execute the start command
start_env() {
    local compose_files=$1
    local env=$2
    
    echo "Starting $env environment..."
    
    if [ "$env" == "test" ]; then
        # TEST: Run tests, then remove containers
        echo "Running unit tests..."
        backend_compose_files=$(echo "$compose_files" | grep -oE "\-f backend[^ ]*")
        frontend_compose_files=$(echo "$compose_files" | grep -oE "\-f frontend[^ ]*")
        docker compose $backend_compose_files run --rm -t $BACKEND_SERVICE
        docker compose $frontend_compose_files run --rm -t $FRONTEND_SERVICE
        docker network rm backend_default
        docker network rm frontend_default
        TEST_RESULT=$?
        
        # Cleanup containers and networks immediately after test run
        docker compose $compose_files down -v --remove-orphans > /dev/null 2>&1
        
        if [ $TEST_RESULT -eq 0 ]; then
            echo "✅   Unit tests completed successfully."
        else
            echo "❌   Unit tests failed (Exit code $TEST_RESULT)."
            exit 1
        fi
    else
        # DEV/PROD: Start services in detached mode
        backend_compose_files=$(echo "$compose_files" | grep -oE "\-f backend[^ ]*")
        frontend_compose_files=$(echo "$compose_files" | grep -oE "\-f frontend[^ ]*")
        docker network create $NETWORK
        docker compose $backend_compose_files up -d --force-recreate
        docker compose $frontend_compose_files up -d --force-recreate
        if [ $? -eq 0 ]; then
            echo "✅   Environment '$env' started successfully."
        else
            echo "❌   Error starting environment '$env'."
            exit 1
        fi
    fi
}

# Function to execute the stop command (removing containers)
stop_env() {
    local compose_files=$1
    local env=$2
    
    if ! is_env_running "$compose_files"; then
        echo "⚠️   Environment '$env' is NOT running. No action taken."
        return 0
    fi
    
    echo "Stopping and removing containers for $env environment..."
    backend_compose_files=$(echo "$compose_files" | grep -oE "\-f backend[^ ]*")
    frontend_compose_files=$(echo "$compose_files" | grep -oE "\-f frontend[^ ]*")
    docker compose $backend_compose_files down -v --remove-orphans
    docker compose $frontend_compose_files down -v --remove-orphans
    docker network rm $NETWORK
    if [ $? -eq 0 ]; then
        echo "✅   Environment '$env' stopped and containers removed."
    else
        echo "❌   Error stopping environment '$env'."
        exit 1
    fi
}

# Function to execute the rebuild command
rebuild_env() {
    local compose_files=$1
    local env=$2
    
    # Stop before rebuilding
    stop_env "$compose_files" "$env"
    
    echo "Forcing complete rebuild (no-cache) for '$env'..."
    docker compose $compose_files build --no-cache --force-rm
    
    if [ $? -eq 0 ]; then
        echo "✅   Images for '$env' rebuilt successfully. Starting now..."
        start_env "$compose_files" "$env"
    else
        echo "❌   Error during image rebuild for '$env'."
        exit 1
    fi
}

# Function to show the log
show_log() {
    local compose_files=$1
    local env=$2

    backend_compose_files=$(echo "$compose_files" | grep -oE "\-f backend[^ ]*")
    frontend_compose_files=$(echo "$compose_files" | grep -oE "\-f frontend[^ ]*")

    # CRITICAL: Test environment is a one-off run and doesn't need 'log'
    if [ "$env" == "test" ]; then
        echo "❌   Logs are not available for the 'test' environment (it's a single run)."
        return 1
    fi

    if ! is_env_running "$compose_files"; then
        echo "❌   Cannot show logs: Environment '$env' is NOT running."
        return 1
    fi
    
    echo "Opening GNOME Terminal tabs for '$env' logs (Backend + Frontend)..."
    
    # 1. LOGS FOR THE BACKEND SERVICE
    backend_cmd_array=(
        docker
        compose
        ${backend_compose_files}
        logs
        -f
        ${BACKEND_SERVICE}
    )
    backend_cmd=""${backend_cmd_array[*]}""
    gnome-terminal --tab --title="${env} Logs (${BACKEND_SERVICE})" -- /bin/bash -c "${backend_cmd}" &

    # 2. LOGS FOR THE FRONTEND SERVICE
    frontend_cmd_array=(
        docker
        compose
        ${frontend_compose_files}
        logs
        -f
        ${FRONTEND_SERVICE}
    )
    frontend_cmd=""${frontend_cmd_array[*]}""
    gnome-terminal --tab --title="${env} Logs (${FRONTEND_SERVICE})" -- /bin/bash -c "${frontend_cmd}" &

    if [ $? -eq 0 ]; then
        echo "✅   Log streamers launched for '$env'. Two tabs opened (Backend and Frontend)."
    else
        echo "❌   Error launching log streamers for '$env'."
    fi
}

# --- Main Logic ---

# Check if the correct number of arguments is provided
if [ $# -lt 2 ]; then
    show_usage
fi

ACTION=$2
ENVIRONMENT=$1

# Change to dir where the script is located before doing anything.
cd $SCRIPT_PATH

# Check if the requested action is valid for the test environment
if [ "$ENVIRONMENT" == "test" ] && ([ "$ACTION" == "stop" ] || [ "$ACTION" == "log" ]); then
    echo "❌   Action '$ACTION' is not typically used for the 'test' environment." >&2
    echo "     Use 'start test' to run tests." >&2
    exit 1
fi

# Get the specific Compose files for the environment
COMPOSE_FILES=$(get_compose_files "$ENVIRONMENT")

# Execute the required action
case "$ACTION" in
    start)
        start_env "$COMPOSE_FILES" "$ENVIRONMENT"
        ;;
    stop)
        stop_env "$COMPOSE_FILES" "$ENVIRONMENT"
        ;;
    rebuild)
        rebuild_env "$COMPOSE_FILES" "$ENVIRONMENT"
        ;;
    log)
        show_log "$COMPOSE_FILES" "$ENVIRONMENT"
        ;;
    *)
        echo "Error: Unknown action '$ACTION'." >&2
        show_usage
        ;;
esac

# Change back to original dir
cd $CURRENT_PATH

exit 0
