🌟 Dorothy AI — Intelligent Voice Assistant
Dorothy AI is a powerful desktop voice assistant built using Python.
It supports speech recognition, text-to-speech, reminders, timers, web search, music playback, fitness planning, and AI-powered responses using Google Gemini.
________________________________________
This project is proudly built by:

•	Akant Ratan

•	Vansh Sharma

•	Sai Raj Konduru

________________________________________
🚀 Features

🎤 Voice Interaction

•	Wake the assistant with F2

•	Natural speech recognition (Google Speech API)

•	High-quality TTS using Edge TTS


⏰ Reminder & Timer System

•	Set reminders using natural language

•	Time-based, action-based, and website-based reminders

•	Stores reminders in JSON (persistent)


🌐 Smart Web Search

•	Integrated Gemini AI for answering questions

•	Wikipedia fallback

•	Automatic browsing for sites like YouTube, Google, Spotify, Instagram, GitHub


🎶 Media Control

•	Plays songs or videos on YouTube/Spotify

•	Smart fallback between platforms


🏋️ Fitness Planner (AI Powered) 

•	Personalized fitness plan

•	BMI calculation

•	Workout + diet recommendations


🧠 Additional Capabilities

•	Small talk responses 

•	Application control (open/close apps)

•	GUI built with Tkinter

•	Animated AI avatar using GIF frames

________________________________________
📂 Project Structure

├── dorothy.py               
├── ai.gif               
├── reminders.json      
└── responses4u.py        
________________________________________
🛠️ Requirements

Install dependencies:

pip install edge_tts playsound SpeechRecognition wikipedia pygetwindow pyautogui pillow google-generativeai

You must also configure your Gemini API key:

genai.configure(api_key="YOUR_API_KEY")

________________________________________
▶️ How to Run

python dorothy.py

•	Press F2 to speak

•	Type in the text box to send commands

•	GUI launches automatically

________________________________________

🤝 Contributing

Pull requests are welcome! Feel free to open issues for feature requests or bugs.

________________________________________
📄 License

This project is open-source and available under the MIT License.

________________________________________

