# Jarvis AI Assistant

Your personal AI assistant optimized for Windows.

## Features
- 🎤 Voice-activated with "Hey Jarvis"
- 🧠 Powered by Google Gemini AI
- 🌐 Web browsing and automation
- 📱 App control and integration
- ⏰ Smart reminders
- 💬 Natural conversation with memory

## Installation

### Prerequisites
- Python 3.10+
- Windows 10/11
- 8GB RAM minimum (16GB recommended)
- Microphone

### Setup
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate`
4. Install: `pip install -r requirements.txt`
5. Download models: `python -m spacy download en_core_web_sm`
6. Setup playwright: `playwright install chromium`
7. Copy `.env.example` to `.env` and add API keys
8. Run: `python main_standalone.py`

## Configuration
Edit `.env` file with your API keys and preferences.

## Building Executable
```bash
python build_exe.py
```

## Troubleshooting
- If wake word doesn't work: Check microphone in System Settings
- If web agent fails: Ensure Playwright is installed
- If TTS silent: Check volume and audio device settings