#!/bin/bash

# --- Configuration ---
NETWORK="stamps-network"

# Ensure we are in the script's directory (Project Root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT" || { echo "❌ Failed to change directory to project root: $PROJECT_ROOT"; exit 1; }

# Backend
BACKEND_COMPOSE="-f backend/docker-compose.yml -f backend/docker-compose.dev.yml"
BACKEND_SVC="stamps-backend"
DB_SVC="db"

# Frontend
FRONTEND_COMPOSE="-f frontend/docker-compose.yml -f frontend/docker-compose.dev.yml"
FRONTEND_SVC="stamps-frontend"

# Testing
BACKEND_TEST_COMPOSE="-f backend/docker-compose.test.yml"
FRONTEND_TEST_COMPOSE="-f frontend/docker-compose.test.yml"

# --- Utility Functions ---

fail() { echo "❌ Error: $1" >&2; exit 1; }

show_usage() {
    echo "Usage: $0 [env] [command] [args]"
    echo ""
    echo "Environments:"
    echo "  dev"
    echo "  test"
    echo "  prod"
    echo ""
    echo "Commands (for dev):"
    echo "  start [service]        Starts services in order (detached)."
    echo "                         No args: starts all (db -> backend -> frontend)"
    echo "                         stamps-db: starts db only"
    echo "                         stamps-backend: starts db and backend"
    echo "                         stamps-frontend: starts all three"
    echo "  log                    Shows both backend and frontend logs"
    echo "  stop                   Stops and removes all dev containers"
    echo "  rebuild                Forces a fresh build of dev images (no-cache)"
    echo "  reset                  Full database and migration reset"
    echo ""
    echo "Commands (for test):"
    echo "  run [-v|--verbose]     Runs pytest in backend and then frontend (rebuilds if needed)."
    echo "                         By default, runs in quiet mode. Use -v or --verbose for detailed"
    echo "                         output."
    echo "  rebuild [-v|--verbose] Forces a fresh build of test images (no-cache). By default, runs in"
    echo "                         quiet mode. Use -v or --verbose for detailed output."
    echo ""
    echo "Commands (for prod):"
    echo "  release [-v|--verbose] Builds and pushes multi-arch images to Docker Hub. By default, runs"
    echo "                         in quiet mode. Use -v or --verbose for detailed output"
    exit 1
}

is_running() {
    local service=$1
    if [ -z "$service" ]; then
        # Check if anything is running
        docker compose $BACKEND_COMPOSE $FRONTEND_COMPOSE ps -q | grep -q '.'
    else
        # Check specific service
        docker ps --filter "name=$service" --filter "status=running" -q | grep -q '.'
    fi
}

ensure_network() {
    docker network inspect $NETWORK >/dev/null 2>&1 || docker network create $NETWORK
}

# --- Action implementation ---

do_start() {
    local target=$1
    ensure_network

    case "$target" in
        "")
            echo "🚀 Starting all services (db -> backend -> frontend)..."
            docker compose $BACKEND_COMPOSE up -d --build db
            docker compose $BACKEND_COMPOSE up -d --build $BACKEND_SVC
            docker compose $FRONTEND_COMPOSE up -d --build $FRONTEND_SVC
            ;;
        "stamps-db" | "db")
            echo "🚀 Starting stamps-db..."
            docker compose $BACKEND_COMPOSE up -d --build db
            ;;
        "stamps-backend" | "backend")
            echo "🚀 Starting stamps-db and stamps-backend..."
            docker compose $BACKEND_COMPOSE up -d --build db
            docker compose $BACKEND_COMPOSE up -d --build $BACKEND_SVC
            ;;
        "stamps-frontend" | "frontend")
            echo "🚀 Starting stamps-db, stamps-backend and stamps-frontend..."
            docker compose $BACKEND_COMPOSE up -d --build db
            docker compose $BACKEND_COMPOSE up -d --build $BACKEND_SVC
            docker compose $FRONTEND_COMPOSE up -d --build $FRONTEND_SVC
            ;;
        *)
            fail "Unknown service '$target'. Available: stamps-db, stamps-backend, stamps-frontend"
            ;;
    esac
    echo "✅ Start command completed."
}

do_log() {
    local backend_up=false
    local frontend_up=false

    is_running "$BACKEND_SVC" && backend_up=true
    is_running "$FRONTEND_SVC" && frontend_up=true

    if [ "$backend_up" = true ] && [ "$frontend_up" = true ]; then
        if command -v gnome-terminal >/dev/null 2>&1; then
            gnome-terminal --tab --title="Backend Logs" -- /bin/bash -c "docker compose $BACKEND_COMPOSE logs -f $BACKEND_SVC" &
            gnome-terminal --tab --title="Frontend Logs" -- /bin/bash -c "docker compose $FRONTEND_COMPOSE logs -f $FRONTEND_SVC" &
            echo "✅ Logs opened in GNOME Terminal tabs."
        else
            echo "⚠️ GNOME Terminal not found. Streaming merged logs (Ctrl+C to stop)..."
            docker compose $BACKEND_COMPOSE $FRONTEND_COMPOSE logs -f
        fi
    else
        [ "$backend_up" = false ] && echo "❌ Error: $BACKEND_SVC is not running."
        [ "$frontend_up" = false ] && echo "❌ Error: $FRONTEND_SVC is not running."
        fail "Both backend and frontend must be running to use the log command."
    fi
}

do_stop() {
    echo "🛑 Stopping all containers..."
    docker compose $BACKEND_COMPOSE down --remove-orphans
    docker compose $FRONTEND_COMPOSE down --remove-orphans
    echo "✅ Stopped."
}

do_rebuild() {
    echo "🏗️  Forcing fresh build of dev images (no-cache)..."
    docker compose $BACKEND_COMPOSE build --no-cache
    docker compose $FRONTEND_COMPOSE build --no-cache
    echo "✅ Dev images rebuilt."
}

do_reset() {
    echo "🔄 Starting full reset..."
    
    # Ensure backend (and thus db) is running before exec
    if ! is_running "$BACKEND_SVC"; then
        echo "📡 Backend is not running. Starting dependency (stamps-backend)..."
        do_start "stamps-backend"
    fi

    echo "⚙️  Executing reset sequences via $BACKEND_SVC..."
    docker exec -t $BACKEND_SVC python manage.py dumpdata admin auth sessions contenttypes rest_framework_api_key --indent 4 > admin_backup_reset.json
    docker exec -t $BACKEND_SVC python manage.py reset_db --noinput
    docker exec -t $BACKEND_SVC python manage.py stamps_clean_migrations
    docker exec -t $BACKEND_SVC python manage.py makemigrations
    docker exec -t $BACKEND_SVC python manage.py migrate

    echo "👤 Creating new django superuser (admin)..."
    docker exec -it $BACKEND_SVC python manage.py createsuperuser --username admin --email admin@example.com
    
    echo "👤 Creating new stamps admin user (interactive)..."
    docker exec -it $BACKEND_SVC python manage.py stamps_create_admin_user
    
    cat admin_backup_reset.json | docker exec -i $BACKEND_SVC python manage.py loaddata --format=json -
    rm admin_backup_reset.json
    
    #docker exec -t $BACKEND_SVC python manage.py stamps_import_csv
    echo "✅ Reset complete!"
}

do_test_run() {
    local test_args="--no-header"
    local build_args="--quiet "
    if [[ "$1" == "--verbose" || "$1" == "-v" ]]; then
        echo "🔊 Verbose mode enabled."
        test_args=""
        build_args=""
    else
        echo "🤫 Quiet mode enabled. Only test results will be shown."
    fi

    echo "🧪 Running tests for Backend..."
    docker compose $BACKEND_TEST_COMPOSE run -e PYTEST_ARGS=$test_args --build --rm $build_args $BACKEND_SVC || fail "Backend tests failed"
    
    echo "🧪 Running tests for Frontend..."
    docker compose $FRONTEND_TEST_COMPOSE run -e PYTEST_ARGS=$test_args --build --rm $build_args $FRONTEND_SVC || fail "Frontend tests failed"
    
    echo "✅ All tests passed!"
}

do_test_rebuild() {
    echo "🏗️  Forcing fresh build of test images..."

    local build_args="--quiet "
    if [[ "$1" == "--verbose" || "$1" == "-v" ]]; then
        echo "🔊 Verbose mode enabled. Showing build output."
        build_args=""
    else
        echo "🤫 Quiet mode enabled. Suppressing build output."
    fi
    docker compose $BACKEND_TEST_COMPOSE build --no-cache $build_args
    docker compose $FRONTEND_TEST_COMPOSE build --no-cache $build_args
    echo "✅ Test images rebuilt."
}

do_prod_release() {
    local build_args="--quiet"
    if [[ "$1" == "--verbose" || "$1" == "-v" ]]; then
        echo "🔊 Verbose mode enabled. Showing build output."
        build_args=""
    else
        echo "🤫 Quiet mode enabled. Suppressing build output."
    fi

    local platforms="linux/amd64,linux/arm64"
    local backend_img="osrogon/stamps-backend:latest"
    local frontend_img="osrogon/stamps-frontend:latest"
    local builder="multiarch-builder"

    echo "🚀 Starting Production Release..."

    # Ensure builder exists and is selected
    if ! docker buildx inspect "$builder" >/dev/null 2>&1; then
        echo "🏗️  Creating buildx builder: $builder..."
        docker buildx create --name "$builder" --use || fail "Failed to create builder $builder"
    else
        echo "🏗️  Using buildx builder: $builder..."
        docker buildx use "$builder"
    fi

    # Build and Push Backend
    echo "📦 Building and pushing Multi-Arch Backend image..."
    docker buildx build $build_args --platform "$platforms" \
        -f backend/Dockerfile.prod \
        -t "$backend_img" \
        --push backend || { docker buildx use default; fail "Backend release failed"; }

    # Build and Push Frontend
    echo "📦 Building and pushing Multi-Arch Frontend image..."
    docker buildx build $build_args --platform "$platforms" \
        -f frontend/Dockerfile.prod \
        -t "$frontend_img" \
        --push frontend || { docker buildx use default; fail "Frontend release failed"; }

    # Switch back to default builder
    echo "🔄 Switching back to default buildx builder..."
    docker buildx use default

    echo "✅ Production Release complete! Images pushed to Docker Hub."
}

# --- Main Logic ---

if [ $# -lt 2 ]; then show_usage; fi

ENV=$1
CMD=$2
shift 2
ARGS=$@

# Validate Environment
if [[ "$ENV" != "dev" && "$ENV" != "test" && "$ENV" != "prod" ]]; then
    fail "Environment '$ENV' not supported. Use 'dev', 'test', or 'prod'."
fi

if [ "$ENV" == "dev" ]; then
    case "$CMD" in
        start)   do_start "$ARGS" ;;
        stop)    do_stop ;;
        log)     do_log ;;
        rebuild) do_rebuild ;;
        reset)   do_reset ;;
        *)       show_usage ;;
    esac
elif [ "$ENV" == "test" ]; then
    case "$CMD" in
        run)       do_test_run "$ARGS" ;;
        rebuild)   do_test_rebuild "$ARGS" ;;
        *)         show_usage ;;
    esac
elif [ "$ENV" == "prod" ]; then
    case "$CMD" in
        release)   do_prod_release "$ARGS" ;;
        *)         show_usage ;;
    esac
fi
