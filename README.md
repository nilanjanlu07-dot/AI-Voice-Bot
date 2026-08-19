# VoiceBot

A Windows-friendly Python voice assistant and chatbot that uses **Google Gemini** for AI-powered responses and **Tkinter** for a simple desktop chat and voice interface.

VoiceBot can accept questions through voice or text, generate responses using Gemini, display the conversation in a chat-style interface, and speak the response back to the user.

## Features

* 🧠 Gemini-powered AI responses with conversational context
* 🎤 Voice input using speech recognition
* 🔊 Spoken AI responses using the local system voice stack
* 💬 Tkinter-based desktop chat interface
* ⚡ Built-in local responses for basic questions and quick offline interactions
* 👤 Assistant identity and creator information built into the application
* 📴 Basic offline functionality when Gemini is unavailable

## Technologies Used

* **Python**
* **Tkinter** — Desktop GUI
* **Google Gemini API** — AI-generated responses
* **SpeechRecognition** — Voice input
* **pyttsx3** — Text-to-speech
* **Environment Variables** — Secure API key management

## How It Works

```text
🎤 Voice / Text Input
        ↓
🗣️ Speech Recognition
        ↓
🧠 Google Gemini API
        ↓
💬 AI Response
        ↓
🖥️ Display Response
        ↓
🔊 Speak Response
```

The application receives a question from the user through voice or text. Voice input is converted into text using speech recognition, and the prompt is sent to Google Gemini. The generated response is displayed in the Tkinter interface and can also be spoken aloud.

For supported basic commands, VoiceBot can provide local responses without requiring Gemini.

## 📸 Demo

### Application Screenshot

<img width="1919" height="1019" alt="Screenshot 2026-08-19 192135" src="https://github.com/user-attachments/assets/fc9c4a25-3727-4e37-8ebb-f720b063c68c" />
<img width="1919" height="983" alt="Screenshot 2026-08-19 192121" src="https://github.com/user-attachments/assets/37e0a5f7-eedb-48eb-a9b5-951d0a6de9ed" />
<img width="1234" height="859" alt="Screenshot 2026-08-19 192523" src="https://github.com/user-attachments/assets/5ca9faae-a88b-43db-b7c5-5bcd28c5fb36" />



### Demo Video

https://github.com/user-attachments/assets/50452268-ba74-416c-8579-31412e310cb3





## 📁 Project Structure

```text
VoiceBot/
│
├── voicebot.py              # Main voice assistant application
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment configuration
├── .gitignore               # Files ignored by Git
├── README.md                # Project documentation
└── LICENSE                  # Project license
```

## ⚙️ Setup

### 1. Clone the repository

Clone this repository to your local computer using Git:

```bash
git clone https://github.com/nilanjanlu07-dot/AI-Voice-Bot.git
cd AI-Voice-Bot
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Set your Gemini API key

For the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

To keep the key available in future PowerShell sessions:

```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key-here", "User")
```

### 5. Run the application

```powershell
.\.venv\Scripts\python.exe voicebot.py
```

## Security

**Never commit or upload your real Gemini API key to GitHub.**

Keep your API key in an environment variable or another local configuration method that is excluded from version control.

The repository includes `.env.example` as a reference for configuring the required environment variable without exposing the real credential.

## Example Prompts

Try asking VoiceBot:

* `"What is Python?"`
* `"What is Artificial Intelligence?"`
* `"Who made you?"`
* `"Tell me about machine learning"`
* `"Help"`

## Future Improvements

Some possible improvements for future versions include:

* 🌐 Web search integration
* 🎵 Music and media controls
* 🖥️ Improved GUI design
* 👁️ Visual AI responses
* 💾 Conversation history
* 🌍 Multi-language voice support
* ⚙️ Customizable voice and assistant settings

## Author

**Nilanjan Das**

BCA student interested in **Artificial Intelligence, Machine Learning, software development, and emerging technologies**.

---

If you find this project interesting, feel free to explore the repository and try it yourself.

**Built with Python, Tkinter, and Google Gemini.**
