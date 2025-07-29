#!/bin/bash

# AI System Installation Script
# Comprehensive setup for the AI System with all dependencies

set -e  # Exit on any error

echo "=========================================="
echo "AI System Installation Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. Some features may require non-root execution."
    fi
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            DISTRO="debian"
        elif command -v yum &> /dev/null; then
            DISTRO="redhat"
        elif command -v pacman &> /dev/null; then
            DISTRO="arch"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        OS="windows"
        DISTRO="windows"
    else
        OS="unknown"
        DISTRO="unknown"
    fi
    
    log_info "Detected OS: $OS ($DISTRO)"
}

# Check Python version
check_python() {
    log_info "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [[ $PYTHON_MAJOR -eq 3 ]] && [[ $PYTHON_MINOR -ge 8 ]]; then
            log_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            log_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    case $DISTRO in
        "debian")
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                python3-dev \
                python3-pip \
                python3-venv \
                portaudio19-dev \
                espeak \
                espeak-data \
                libespeak1 \
                libespeak-dev \
                ffmpeg \
                alsa-utils \
                pulseaudio \
                git \
                curl \
                wget \
                cmake \
                pkg-config \
                libssl-dev \
                libffi-dev \
                libbz2-dev \
                libreadline-dev \
                libsqlite3-dev \
                libncursesw5-dev \
                xz-utils \
                tk-dev \
                libxml2-dev \
                libxmlsec1-dev \
                liblzma-dev
            ;;
        "redhat")
            sudo yum update -y
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y \
                python3-devel \
                python3-pip \
                portaudio-devel \
                espeak \
                espeak-devel \
                ffmpeg \
                alsa-lib-devel \
                pulseaudio-libs-devel \
                git \
                curl \
                wget \
                cmake \
                pkgconfig \
                openssl-devel \
                libffi-devel \
                bzip2-devel \
                readline-devel \
                sqlite-devel \
                ncurses-devel \
                xz-devel \
                tk-devel \
                libxml2-devel \
                xmlsec1-devel
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm \
                base-devel \
                python \
                python-pip \
                portaudio \
                espeak \
                ffmpeg \
                alsa-lib \
                pulseaudio \
                git \
                curl \
                wget \
                cmake \
                pkg-config \
                openssl \
                libffi \
                bzip2 \
                readline \
                sqlite \
                ncurses \
                xz \
                tk \
                libxml2 \
                xmlsec
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            brew update
            brew install \
                portaudio \
                espeak \
                ffmpeg \
                git \
                cmake \
                pkg-config \
                openssl \
                libffi \
                readline \
                sqlite3 \
                xz \
                libxml2 \
                libxmlsec1
            ;;
        *)
            log_warning "Unknown distribution. You may need to install system dependencies manually."
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Create virtual environment
create_venv() {
    log_info "Creating Python virtual environment..."
    
    if [[ -d "venv" ]]; then
        log_warning "Virtual environment already exists. Removing..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log_success "Virtual environment created and activated"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Ensure we're in the virtual environment
    source venv/bin/activate
    
    # Install core requirements
    pip install -r requirements/requirements.txt
    
    # Install optional dependencies based on system capabilities
    log_info "Installing optional dependencies..."
    
    # Try to install voice dependencies
    if pip install SpeechRecognition pyttsx3; then
        log_success "Voice interface dependencies installed"
        
        # Try to install PyAudio (may fail on some systems)
        if pip install pyaudio; then
            log_success "Audio dependencies installed"
        else
            log_warning "PyAudio installation failed. Voice interface may not work properly."
        fi
    else
        log_warning "Voice dependencies installation failed"
    fi
    
    # Try to install GPU support if CUDA is available
    if command -v nvidia-smi &> /dev/null; then
        log_info "NVIDIA GPU detected. Installing CUDA support..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        log_success "CUDA support installed"
    else
        log_info "No NVIDIA GPU detected. Using CPU-only PyTorch."
    fi
    
    log_success "Python dependencies installed"
}

# Setup directories
setup_directories() {
    log_info "Setting up directory structure..."
    
    # Create necessary directories
    mkdir -p data
    mkdir -p logs
    mkdir -p temp
    mkdir -p config
    mkdir -p templates
    mkdir -p static
    mkdir -p drivers
    mkdir -p docs
    
    # Set permissions
    chmod 755 data logs temp config templates static drivers docs
    
    log_success "Directory structure created"
}

# Create configuration files
create_config() {
    log_info "Creating configuration files..."
    
    # Create default configuration if it doesn't exist
    if [[ ! -f "config/system_config.json" ]]; then
        cat > config/system_config.json << EOF
{
    "ai_model": {
        "model_name": "gpt-4",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 30
    },
    "rag": {
        "vector_db_path": "data/vector_db",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "similarity_threshold": 0.7,
        "max_retrieved_docs": 5
    },
    "ui": {
        "dashboard_port": 8080,
        "dashboard_host": "0.0.0.0",
        "voice_enabled": true,
        "voice_language": "en-US",
        "theme": "dark"
    },
    "security": {
        "encryption_enabled": true,
        "audit_logging": true,
        "access_control_enabled": true,
        "max_login_attempts": 3,
        "session_timeout": 3600
    }
}
EOF
        log_success "Default configuration created"
    else
        log_info "Configuration file already exists"
    fi
    
    # Create environment file template
    if [[ ! -f ".env.template" ]]; then
        cat > .env.template << EOF
# AI System Environment Variables
# Copy this file to .env and fill in your values

# OpenAI API Key (required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Other API Keys (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# System Configuration
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO

# Dashboard Configuration
DASHBOARD_PORT=8080
DASHBOARD_HOST=0.0.0.0

# Voice Interface
VOICE_ENABLED=true
VOICE_LANGUAGE=en-US

# Security
ENCRYPTION_ENABLED=true
SECURITY_ENABLED=true
EOF
        log_success "Environment template created"
    fi
}

# Install the package
install_package() {
    log_info "Installing AI System package..."
    
    # Ensure we're in the virtual environment
    source venv/bin/activate
    
    # Install in development mode
    pip install -e .
    
    log_success "AI System package installed"
}

# Create systemd service (Linux only)
create_service() {
    if [[ "$OS" == "linux" ]] && command -v systemctl &> /dev/null; then
        log_info "Creating systemd service..."
        
        INSTALL_DIR=$(pwd)
        USER=$(whoami)
        
        sudo tee /etc/systemd/system/ai-system.service > /dev/null << EOF
[Unit]
Description=AI System - Comprehensive Multi-Agent Architecture
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-system

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable ai-system
        
        log_success "Systemd service created and enabled"
        log_info "Use 'sudo systemctl start ai-system' to start the service"
    else
        log_info "Skipping systemd service creation (not applicable for this system)"
    fi
}

# Run tests
run_tests() {
    log_info "Running system tests..."
    
    # Ensure we're in the virtual environment
    source venv/bin/activate
    
    # Install test dependencies
    pip install pytest pytest-asyncio pytest-cov
    
    # Run tests if they exist
    if [[ -d "tests" ]]; then
        python -m pytest tests/ -v
        log_success "Tests completed"
    else
        log_info "No tests directory found, skipping tests"
    fi
}

# Final setup and verification
final_setup() {
    log_info "Performing final setup and verification..."
    
    # Ensure we're in the virtual environment
    source venv/bin/activate
    
    # Test import
    if python -c "import sys; sys.path.insert(0, 'src'); from main import main; print('Import successful')"; then
        log_success "Package import test passed"
    else
        log_error "Package import test failed"
        exit 1
    fi
    
    # Create startup script
    cat > start.sh << 'EOF'
#!/bin/bash
# AI System Startup Script

cd "$(dirname "$0")"
source venv/bin/activate
python src/main.py "$@"
EOF
    
    chmod +x start.sh
    
    # Create dashboard script
    cat > dashboard.sh << 'EOF'
#!/bin/bash
# AI System Dashboard Launcher

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting AI System Dashboard..."
echo "Dashboard will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop"

python src/main.py
EOF
    
    chmod +x dashboard.sh
    
    log_success "Startup scripts created"
}

# Print installation summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "AI System Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Installation Summary:"
    echo "- OS: $OS ($DISTRO)"
    echo "- Python: $PYTHON_VERSION"
    echo "- Installation Directory: $(pwd)"
    echo ""
    echo "Quick Start:"
    echo "1. Copy .env.template to .env and configure your API keys"
    echo "2. Run: ./start.sh"
    echo "3. Access dashboard at: http://localhost:8080"
    echo ""
    echo "Available Commands:"
    echo "- ./start.sh                 # Start the AI system"
    echo "- ./dashboard.sh             # Start with dashboard focus"
    echo "- source venv/bin/activate   # Activate virtual environment"
    echo ""
    if [[ "$OS" == "linux" ]] && command -v systemctl &> /dev/null; then
        echo "Systemd Service:"
        echo "- sudo systemctl start ai-system    # Start service"
        echo "- sudo systemctl stop ai-system     # Stop service"
        echo "- sudo systemctl status ai-system   # Check status"
        echo ""
    fi
    echo "Documentation:"
    echo "- README.md for detailed information"
    echo "- config/system_config.json for configuration"
    echo "- logs/ directory for system logs"
    echo ""
    echo "Enjoy your AI System!"
    echo "=========================================="
}

# Main installation process
main() {
    log_info "Starting AI System installation..."
    
    check_root
    detect_os
    check_python
    install_system_deps
    create_venv
    install_python_deps
    setup_directories
    create_config
    install_package
    create_service
    run_tests
    final_setup
    print_summary
    
    log_success "Installation completed successfully!"
}

# Run main function
main "$@"