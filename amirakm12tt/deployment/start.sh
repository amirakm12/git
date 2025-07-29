#!/bin/bash

# AI System Startup Script
# This script handles the initialization and startup of the AI System

set -e

echo "Starting AI System..."
echo "Environment: ${ENVIRONMENT:-development}"
echo "Debug Mode: ${DEBUG_MODE:-false}"
echo "Python Path: ${PYTHONPATH}"

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service_name at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "$service_name is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "ERROR: $service_name failed to start within expected time"
    return 1
}

# Function to check Python dependencies
check_dependencies() {
    echo "Checking Python dependencies..."
    
    required_packages=(
        "asyncio"
        "aiohttp"
        "psutil"
        "numpy"
        "torch"
        "transformers"
        "sentence_transformers"
        "chromadb"
        "uvloop"
        "cryptography"
        "pyttsx3"
        "SpeechRecognition"
        "pyaudio"
    )
    
    for package in "${required_packages[@]}"; do
        if ! python -c "import $package" 2>/dev/null; then
            echo "ERROR: Required package '$package' not found"
            exit 1
        fi
    done
    
    echo "All Python dependencies are available"
}

# Function to initialize directories
init_directories() {
    echo "Initializing directories..."
    
    directories=(
        "data"
        "logs"
        "temp"
        "config"
        "data/vector_db"
        "drivers"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            echo "Created directory: $dir"
        fi
    done
    
    # Set permissions
    chmod 755 data logs temp config drivers
    chmod 700 config  # Secure config directory
}

# Function to check system resources
check_system_resources() {
    echo "Checking system resources..."
    
    # Check available memory (minimum 2GB)
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -lt 2048 ]; then
        echo "WARNING: Low available memory: ${available_memory}MB (recommended: 2048MB+)"
    else
        echo "Available memory: ${available_memory}MB"
    fi
    
    # Check disk space (minimum 10GB)
    available_disk=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$available_disk" -lt 10 ]; then
        echo "WARNING: Low disk space: ${available_disk}GB (recommended: 10GB+)"
    else
        echo "Available disk space: ${available_disk}GB"
    fi
    
    # Check CPU cores
    cpu_cores=$(nproc)
    echo "CPU cores: $cpu_cores"
}

# Function to setup logging
setup_logging() {
    echo "Setting up logging..."
    
    # Create log files if they don't exist
    touch logs/system.log
    touch logs/error.log
    touch logs/performance.log
    touch logs/security.log
    
    # Rotate old logs if they're too large (>100MB)
    for log_file in logs/*.log; do
        if [ -f "$log_file" ] && [ $(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file") -gt 104857600 ]; then
            mv "$log_file" "${log_file}.old"
            touch "$log_file"
            echo "Rotated large log file: $log_file"
        fi
    done
}

# Function to validate configuration
validate_config() {
    echo "Validating configuration..."
    
    # Check for required environment variables
    required_vars=(
        "ENVIRONMENT"
        "PYTHONPATH"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "ERROR: Required environment variable '$var' is not set"
            exit 1
        fi
    done
    
    # Validate Python path
    if [ ! -d "$PYTHONPATH" ]; then
        echo "ERROR: PYTHONPATH directory does not exist: $PYTHONPATH"
        exit 1
    fi
    
    echo "Configuration validation passed"
}

# Function to perform health check
health_check() {
    echo "Performing initial health check..."
    
    # Check if main.py exists
    if [ ! -f "src/main.py" ]; then
        echo "ERROR: Main application file not found: src/main.py"
        exit 1
    fi
    
    # Test Python syntax
    if ! python -m py_compile src/main.py; then
        echo "ERROR: Python syntax error in main.py"
        exit 1
    fi
    
    echo "Health check passed"
}

# Function to handle graceful shutdown
cleanup() {
    echo "Received shutdown signal, cleaning up..."
    
    # Kill background processes
    jobs -p | xargs -r kill
    
    # Wait for processes to terminate
    sleep 2
    
    echo "Cleanup completed"
    exit 0
}

# Setup signal handlers
trap cleanup SIGTERM SIGINT

# Main startup sequence
main() {
    echo "=================================================="
    echo "AI System Container Startup"
    echo "Version: ${VERSION:-1.0.0}"
    echo "Build Date: ${BUILD_DATE:-unknown}"
    echo "=================================================="
    
    # Pre-flight checks
    validate_config
    check_dependencies
    check_system_resources
    init_directories
    setup_logging
    health_check
    
    # Wait for dependent services if in production
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "Production environment detected, waiting for services..."
        
        # Wait for ChromaDB
        if [ -n "$CHROMADB_HOST" ]; then
            wait_for_service "${CHROMADB_HOST:-chromadb}" "${CHROMADB_PORT:-8000}" "ChromaDB"
        fi
        
        # Wait for Redis
        if [ -n "$REDIS_HOST" ]; then
            wait_for_service "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}" "Redis"
        fi
    fi
    
    echo "All pre-flight checks passed, starting AI System..."
    
    # Start the main application
    cd /app
    exec python src/main.py
}

# Run main function
main "$@"