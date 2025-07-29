# AI System Installation Guide

## 🚀 Quick Installation (Recommended)

### Option 1: Windows Installers (Easiest - No Admin Required)

**For Windows 10/11 (PowerShell):**
1. **Right-click and "Run with PowerShell":**
   ```powershell
   .\install_windows.ps1
   ```
   - Or with custom path: `.\install_windows.ps1 -InstallPath "C:\MyApps"`
   - Force reinstall: `.\install_windows.ps1 -Force`

**For All Windows Versions (Batch):**
1. **Double-click to run:**
   ```batch
   install_windows.bat
   ```

**Features:**
- ✅ **No administrator privileges required**
- ✅ Installs to user directory (`%LOCALAPPDATA%\AI-System`)
- ✅ Creates virtual environment automatically
- ✅ Installs all dependencies
- ✅ Creates desktop shortcuts
- ✅ Includes uninstaller
- ✅ Tests installation automatically

**After Installation:**
- Use desktop shortcut "AI-System"
- Or run from: `%LOCALAPPDATA%\AI-System\AI-System.bat`
- Web dashboard: http://localhost:8080

### Option 2: One-Click Python Installer

1. **Download and run:**
   ```bash
   python install_executable.py
   ```
   
2. **Follow the prompts:**
   - The script will guide you through the installation
   - All dependencies will be installed automatically

## 🔧 Manual Installation

### Prerequisites

- **Python 3.8 or higher**
- **pip package manager**
- **Git** (optional, for cloning)
- **At least 2GB free disk space**
- **Internet connection** for downloading dependencies

### Step 1: Get the Source Code

#### Option A: Download ZIP
1. Download the project ZIP file
2. Extract to your desired location

#### Option B: Clone Repository
```bash
git clone https://github.com/ai-system/ai-system.git
cd ai-system
```

### Step 2: Run Installation Script

#### Linux/macOS:
```bash
chmod +x install.sh
./install.sh
```

#### Windows:
```bash
install.bat
```

#### Or use Python setup:
```bash
python setup.py install
```

### Step 3: Configure the System

1. **Edit configuration files:**
   ```bash
   # Copy default configuration
   cp config/config.example.json config/config.json
   
   # Edit with your settings
   nano config/config.json
   ```

2. **Set up API keys (if using external services):**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

### Step 4: Start the System

```bash
python src/main.py
```

## 🐳 Docker Installation

### Quick Start with Docker

1. **Build the Docker image:**
   ```bash
   docker build -t ai-system .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 8080:8080 --name ai-system ai-system
   ```

3. **Access the dashboard:**
   - Open http://localhost:8080 in your browser

### Docker Compose (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop services:**
   ```bash
   docker-compose down
   ```

## 🔍 System Requirements

### Minimum Requirements
- **OS:** Windows 7+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 2GB free space
- **Network:** Internet connection for initial setup

### Recommended Requirements
- **OS:** Windows 10+, macOS 11+, or Linux (Ubuntu 20.04+)
- **Python:** 3.10 or higher
- **RAM:** 16GB or more
- **Storage:** 10GB free space (for models and data)
- **GPU:** CUDA-compatible GPU for AI acceleration (optional)

## 🧪 Verification

### Test Installation

1. **Run the verification script:**
   ```bash
   python verify_installation.py
   ```

2. **Run basic tests:**
   ```bash
   python -m pytest tests/ -v
   ```

3. **Check system status:**
   ```bash
   python -c "from src.main import AISystem; print('✅ Installation successful!')"
   ```

### Expected Output

After successful installation, you should see:
- ✅ All system components initialized
- 🌐 Web dashboard accessible at http://localhost:8080
- 🎤 Voice interface ready (if supported)
- 📊 System monitoring active

## 🛠️ Troubleshooting

### Common Issues

#### 1. Python Version Error
```
Error: Python 3.8+ required
```
**Solution:** Install Python 3.8 or higher from https://python.org

#### 2. Permission Denied (Linux/macOS)
```
Error: Permission denied
```
**Solution:** Run with appropriate permissions:
```bash
sudo chmod +x install.sh
sudo ./install.sh
```

#### 3. Package Installation Failed
```
Error: Failed to install package X
```
**Solution:** Update pip and try again:
```bash
python -m pip install --upgrade pip
pip install -r requirements/requirements.txt
```

#### 4. Port Already in Use
```
Error: Port 8080 already in use
```
**Solution:** Change port in config or stop conflicting service:
```bash
# Change port in config/config.json
"ui": {
    "dashboard_port": 8081
}
```

#### 5. CUDA/GPU Issues
```
Error: CUDA not available
```
**Solution:** Install CUDA drivers or disable GPU acceleration:
```bash
# Install CPU-only PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Getting Help

1. **Check the logs:**
   ```bash
   tail -f logs/system.log
   ```

2. **Run diagnostics:**
   ```bash
   python src/diagnostics.py
   ```

3. **Report issues:**
   - GitHub Issues: https://github.com/ai-system/ai-system/issues
   - Include system info, error messages, and log files

## 📋 Post-Installation Setup

### 1. Configure API Keys

Edit `config/config.json`:
```json
{
  "ai_models": {
    "openai_api_key": "your-key-here",
    "anthropic_api_key": "your-key-here"
  }
}
```

### 2. Set Up Voice Interface

1. **Install voice dependencies:**
   ```bash
   pip install SpeechRecognition pyttsx3 pyaudio
   ```

2. **Configure microphone:**
   - Test microphone access
   - Adjust sensitivity in config

### 3. Initialize Knowledge Base

1. **Add documents to RAG system:**
   ```bash
   python -m src.ai.rag_engine --add-documents /path/to/documents
   ```

2. **Build vector database:**
   ```bash
   python -m src.ai.rag_engine --build-index
   ```

### 4. Set Up Monitoring

1. **Configure system monitoring:**
   - Edit monitoring settings in config
   - Set up alerts and notifications

2. **Start monitoring services:**
   ```bash
   python -m src.monitoring.system_monitor
   ```

## 🔄 Updates and Maintenance

### Updating the System

1. **Check for updates:**
   ```bash
   git pull origin main
   ```

2. **Update dependencies:**
   ```bash
   pip install -r requirements/requirements.txt --upgrade
   ```

3. **Restart services:**
   ```bash
   python src/main.py --restart
   ```

### Backup and Restore

1. **Backup configuration and data:**
   ```bash
   tar -czf ai-system-backup.tar.gz config/ data/ logs/
   ```

2. **Restore from backup:**
   ```bash
   tar -xzf ai-system-backup.tar.gz
   ```

## 🗑️ Uninstallation

### Windows
Run the uninstaller from the installation directory:
```bash
uninstall.bat
```

### Linux/macOS
```bash
./uninstall.sh
```

### Manual Removal
```bash
# Remove installation directory
rm -rf /path/to/ai-system

# Remove configuration files
rm -rf ~/.config/ai-system

# Remove desktop entries (Linux)
rm -f ~/.local/share/applications/ai-system.desktop
```

## 📞 Support

- **Documentation:** https://ai-system.readthedocs.io/
- **GitHub Issues:** https://github.com/ai-system/ai-system/issues
- **Discussions:** https://github.com/ai-system/ai-system/discussions
- **Email:** support@ai-system.dev

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.