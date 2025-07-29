# IGED Quick Start Guide

Get IGED running in 5 minutes!

## 🚀 Quick Installation

### Windows
1. **Install Python 3.8+** from [python.org](https://python.org)
2. **Download IGED** and extract to a folder
3. **Run installer**: Double-click `install.bat`
4. **Start IGED**: Double-click `launcher.py` or run `python launcher.py`

### Linux/Mac
```bash
# Install Python 3.8+
sudo apt install python3 python3-pip  # Ubuntu/Debian
brew install python3                  # Mac

# Install IGED
pip install -r requirements.txt
python launcher.py
```

## 🎯 First Commands

Try these voice or text commands:

- **"Generate a Flask web application"**
- **"Show system information"**
- **"Scan local network for vulnerabilities"**
- **"Analyze data from sales.csv"**

## 🌐 Access Interfaces

- **GUI**: Automatic Windows interface
- **Web Admin**: http://localhost:8080
- **Android**: Connect to port 9090

## 🔧 Configuration

1. **Voice Settings**: Adjust sensitivity in GUI Settings tab
2. **Offline Mode**: Enable in Settings for air-gapped operation
3. **Memory**: View and search command history in Memory tab

## 🚨 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python 3.8+ from python.org
- Add Python to PATH during installation

**"Microphone not working"**
- Check microphone permissions
- Try different microphone in system settings

**"Dependencies failed"**
- Run `pip install -r requirements.txt` manually
- Check internet connection

**"Encryption key error"**
- Delete `config/secret.key` and restart
- Key will be regenerated automatically

### Getting Help

1. Check the logs in `iged.log`
2. View system status in GUI Status tab
3. Restart IGED if components fail

## 🎉 You're Ready!

IGED is now your sovereign AI assistant. Speak naturally and watch it execute your commands!

---

**Need more help?** Check the full README.md for detailed documentation. 