# VoiceBot

A Windows-friendly Python voice assistant and chatbot that uses Google Gemini for AI responses and a Tkinter interface for chat and voice interaction.

## Features
- Gemini-powered responses with conversational context
- Voice input and spoken responses through the local system voice stack
- Tkinter GUI with transcript-style chat experience
- Built-in local command responses for basic questions and quick offline interactions
- Creator identity built into the assistant: Nilanjan Das

## Project structure
- `voicebot.py` — main voice assistant script
- `requirements.txt` — standard dependency list for GitHub usage
- `voice_requirements.txt` — kept for compatibility with earlier local setup
- `.env.example` — example environment file for API credentials

## Setup
1. Clone the repository.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Set your Gemini API key in the current terminal session:

   ```powershell
   $env:GEMINI_API_KEY = "your-key-here"
   ```

   To keep it available in future PowerShell sessions:

   ```powershell
   [Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key-here", "User")
   ```

5. Run the app:

   ```powershell
   .\.venv\Scripts\python.exe voicebot.py
   ```

## Notes
- Do not commit your real API key to GitHub.
- Keep the key in your environment or a local `.env` file that is ignored by Git.
- `voicebot.py` will still provide offline local responses if the Gemini key or SDK is unavailable.

## Example prompts
- "python?"
- "AI news"
- "who made you?"
- "help"
