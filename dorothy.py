import asyncio
import edge_tts
import playsound
import speech_recognition as sr
import webbrowser
import wikipedia
import pygetwindow as gw
import pyautogui
import os
import time
import random
import tkinter as tk
from threading import Thread
from tkinter import Scrollbar, Text, END
from PIL import Image, ImageTk, ImageSequence
import sys
import re
import datetime
import google.generativeai as genai
import subprocess
import json
from responses4u import responses


try:
    genai.configure(api_key="AIzaSyASiPTqgBK60DFsXSHpLGtQJeQAtPv6h2w")
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    GEMINI_ENABLED = True
    print("✅ Gemini AI enabled!")
except Exception as e:
    GEMINI_ENABLED = False
    print(f"⚠️ Gemini configuration failed: {e}")
    print("⚠️ Using Wikipedia fallback.")

# ============================================
# REMINDER SYSTEM
# ============================================

class ReminderManager:
    """Manages reminders with persistent storage"""
    
    def __init__(self, storage_file="reminders.json"):
        self.storage_file = storage_file
        self.reminders = []
        self.load_reminders()
        self.check_thread = None
        self.running = False
    
    def load_reminders(self):
        """Load reminders from file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    self.reminders = json.load(f)
                print(f"✅ Loaded {len(self.reminders)} reminders")
        except Exception as e:
            print(f"⚠️ Error loading reminders: {e}")
            self.reminders = []
    
    def save_reminders(self):
        """Save reminders to file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving reminders: {e}")
    
    def add_reminder(self, task, trigger_time, action_type="notification"):
        """Add a new reminder"""
        reminder = {
            "id": int(time.time() * 1000),
            "task": task,
            "trigger_time": trigger_time.isoformat(),
            "action_type": action_type,
            "created_at": datetime.datetime.now().isoformat(),
            "completed": False
        }
        self.reminders.append(reminder)
        self.save_reminders()
        return reminder
    
    def get_active_reminders(self):
        """Get all non-completed reminders"""
        return [r for r in self.reminders if not r.get("completed", False)]
    
    def mark_completed(self, reminder_id):
        """Mark reminder as completed"""
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["completed"] = True
                reminder["completed_at"] = datetime.datetime.now().isoformat()
        self.save_reminders()
    
    def delete_reminder(self, reminder_id):
        """Delete a reminder"""
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
        self.save_reminders()
    
    async def check_reminders(self):
        """Background task to check reminders"""
        print("🔄 Reminder checker started!")
        while self.running:
            try:
                now = datetime.datetime.now()
                active_reminders = self.get_active_reminders()
                
                if active_reminders:
                    print(f"⏰ Checking {len(active_reminders)} reminder(s) at {now.strftime('%H:%M:%S')}")
                
                for reminder in active_reminders:
                    trigger_time = datetime.datetime.fromisoformat(reminder["trigger_time"])
                    time_left = (trigger_time - now).total_seconds()
                    
                    print(f"   • '{reminder['task']}' - {time_left:.0f}s remaining")
                    
                    # Check if reminder time has passed
                    if now >= trigger_time:
                        print(f"   🔔 TRIGGERING: {reminder['task']}")
                        await self.trigger_reminder(reminder)
                        self.mark_completed(reminder["id"])
                
                await asyncio.sleep(5)  # Check every 5 seconds for better responsiveness
            except Exception as e:
                print(f"❌ Error in reminder checker: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)
    
    async def trigger_reminder(self, reminder):
        """Execute the reminder action"""
        task = reminder["task"]
        action_type = reminder.get("action_type", "notification")
        
        print(f"\n🔔 REMINDER TRIGGERED: {task}")
        
        # Speak the reminder
        await speak(f"Reminder! {task}")
        
        # Perform action based on type
        if action_type == "open_website":
            # Extract website from task
            if "youtube" in task.lower():
                webbrowser.open("https://www.youtube.com")
            elif "google" in task.lower():
                webbrowser.open("https://www.google.com")
            elif "spotify" in task.lower():
                webbrowser.open("https://open.spotify.com")
            else:
                # Try to extract URL
                import re
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, task)
                if urls:
                    webbrowser.open(urls[0])
        
        elif action_type == "play_music":
            # Extract song name from task
            song = task.replace("play", "").replace("music", "").strip()
            webbrowser.open(f"https://open.spotify.com/search/{song}")
        
        elif action_type == "notification":
            # Just notify
            pass
    
    def start_monitoring(self):
        """Start the reminder monitoring thread"""
        if not self.running:
            self.running = True
            self.check_thread = Thread(target=lambda: asyncio.run(self.check_reminders()), daemon=True)
            self.check_thread.start()
            print("✅ Reminder monitoring started")
    
    def stop_monitoring(self):
        """Stop the reminder monitoring"""
        self.running = False

# Initialize global reminder manager
reminder_manager = ReminderManager()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

listener = sr.Recognizer()

def clean_text_for_speech(text):
    """Remove markdown formatting and symbols for better TTS"""
    import re
    
    # Remove markdown bold (**text** or __text__)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # Remove markdown italic (*text* or _text_)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove bullet points and list markers
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove extra asterisks and special characters
    text = text.replace('*', '')
    text = text.replace('#', '')
    text = text.replace('`', '')
    text = text.replace('~', '')
    
    # Clean up multiple spaces and newlines
    text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to single
    text = re.sub(r' +', ' ', text)  # Multiple spaces to single
    
    # Replace newlines with proper pauses for speech
    text = text.replace('\n', '. ')
    
    # Clean up multiple periods
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r'\.\s*\.', '.', text)
    
    return text.strip()

async def speak(text):
    """TTS with validation and robust playback fallbacks."""
    # Clean markdown and formatting before speaking
    clean_text = clean_text_for_speech(text)
    
    print("Dorothy:", clean_text)
    base = f"output_{int(time.time() * 1000)}"
    mp3_path = os.path.abspath(base + ".mp3")

    try:
        await edge_tts.Communicate(clean_text, voice="en-IN-NeerjaNeural", rate="-15%", pitch="+40Hz").save(mp3_path)
        
        # Validate file
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 500:
            print(f"Saved {mp3_path} size={os.path.getsize(mp3_path)}")
            
            # Try playback
            try:
                playsound.playsound(mp3_path)
            except Exception as e:
                print(f"playsound failed: {e}. Trying afplay.")
                subprocess.run(["afplay", mp3_path], check=True)
            
            # Cleanup
            try:
                os.remove(mp3_path)
            except:
                pass
        else:
            print("TTS file too small or missing, skipping playback.")
            
    except Exception as e:
        print(f"TTS error: {e}")

def listen_command():
    with sr.Microphone() as source:
        print("Listening...")
        listener.adjust_for_ambient_noise(source)
        audio = listener.listen(source, phrase_time_limit=5)
    try:
        command = listener.recognize_google(audio).lower()
        print("You:", command)
        return command
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "network error"

# ============================================
# FIXED: Gemini AI Integration
# ============================================

def ask_gemini(query, context=""):
    """Use Google Gemini to answer queries"""
    if not GEMINI_ENABLED:
        return "Gemini AI is not available. Please check your API key."
    
    try:
        # Add instruction to avoid markdown formatting
        system_prompt = """You are Dorothy, a helpful voice assistant. Provide concise answers under 200 words, suitable for text-to-speech.
IMPORTANT: Do not use markdown formatting like asterisks, bold, or bullet points. Use plain text only with simple punctuation."""
        
        if context:
            full_query = f"{system_prompt}\n\nContext: {context}\n\nQuery: {query}"
        else:
            full_query = f"{system_prompt}\n\nQuery: {query}"
        
        response = model.generate_content(full_query)
        
        # Check if blocked
        if hasattr(response, 'prompt_feedback'):
            if hasattr(response.prompt_feedback, 'block_reason'):
                if response.prompt_feedback.block_reason:
                    return "Sorry, I couldn't generate a response for that."
        
        return response.text
        
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "Sorry, I encountered an error processing your request."

async def search_with_gemini(query):
    """Handle general searches using Gemini"""
    await speak(f"Searching for {query}")
    answer = ask_gemini(query)
    print(f"\n{'='*50}")
    print(f"QUERY: {query}")
    print(f"{'='*50}")
    print(answer)
    print(f"{'='*50}\n")
    await speak(answer)
    return True

async def search_about_person_gemini(person_name):
    """Search for person information"""
    await speak(f"Searching for {person_name}")
    query = f"Provide a brief summary about {person_name} in 3-4 sentences."
    answer = ask_gemini(query)
    print(f"\nPERSON: {person_name}\n{answer}\n")
    await speak(answer)
    return True

async def search_about_event_gemini(event_query):
    """Search for events"""
    await speak(f"Searching for {event_query}")
    query = f"Provide key information about: {event_query}"
    answer = ask_gemini(query)
    print(f"\nEVENT: {event_query}\n{answer}\n")
    await speak(answer)
    return True

# ============================================
# FITNESS FEATURE
# ============================================

async def get_number_from_speech(prompt_text):
    await speak(prompt_text)
    response = listen_command()
    match = re.search(r'\d+\.?\d*', response)
    if match:
        return float(match.group())
    return None

async def get_yes_no_response(prompt_text):
    await speak(prompt_text)
    response = listen_command()
    return "yes" in response or "yeah" in response or "yep" in response

async def get_comprehensive_fitness_plan():
    """Comprehensive fitness plan with Gemini"""
    await speak("I'll create a fitness plan for you. Let me ask some questions.")
    
    weight = await get_number_from_speech("Please tell me your weight in kilograms.")
    if not weight:
        await speak("I couldn't understand your weight.")
        return
    
    height = await get_number_from_speech("Please tell me your height in centimeters.")
    if not height:
        await speak("I couldn't understand your height.")
        return
    
    age = await get_number_from_speech("Please tell me your age.")
    if not age:
        age = 30
    
    # Calculate BMI
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    await speak(f"Your BMI is {bmi:.1f}.")
    print(f"\n📊 BMI: {bmi:.1f}")
    
    # Ask about conditions
    await speak("Do you have any medical conditions? Say yes or no.")
    has_conditions = await get_yes_no_response("")
    
    conditions = "None"
    if has_conditions:
        await speak("Please briefly describe your condition.")
        conditions = listen_command()
        if not conditions:
            conditions = "Not specified"
    
    # Ask about disabilities
    await speak("Do you have any physical disabilities? Say yes or no.")
    has_disability = await get_yes_no_response("")
    
    disability = "None"
    if has_disability:
        await speak("Please briefly describe it.")
        disability = listen_command()
        if not disability:
            disability = "Not specified"
    
    # Ask about restrictions
    await speak("Are there movements you cannot perform? Say yes or no.")
    has_restrictions = await get_yes_no_response("")
    
    restrictions = "None"
    if has_restrictions:
        await speak("Please tell me which movements.")
        restrictions = listen_command()
        if not restrictions:
            restrictions = "Not specified"
    
    # Fitness level
    await speak("What is your fitness level? Beginner, intermediate, or advanced?")
    fitness_level = listen_command()
    if not fitness_level or fitness_level not in ['beginner', 'intermediate', 'advanced']:
        fitness_level = "beginner"
    
    # Calculate water intake
    water_intake = round(weight * 0.033, 1)
    
    # Build fitness query
    fitness_query = f"""Create a personalized fitness plan for someone with:
- Age: {age}, Weight: {weight}kg, Height: {height}cm, BMI: {bmi:.1f}
- Medical conditions: {conditions}
- Physical limitations: {disability}
- Movement restrictions: {restrictions}
- Fitness level: {fitness_level}

Please provide:
1. 5-6 specific exercises with reps and sets
2. A simple weekly workout schedule
3. A basic diet plan with meal examples
4. Any important safety notes

IMPORTANT: Use plain text only, no markdown formatting, no asterisks, no bullet points. Write in simple sentences suitable for text-to-speech."""
    
    await speak("Creating your personalized plan. Please wait.")
    print("\n⏳ Generating fitness plan with AI...")
    
    if GEMINI_ENABLED:
        fitness_plan = ask_gemini(fitness_query)
        
        # Add water intake
        full_plan = f"Your daily water intake should be {water_intake} liters.\n\n{fitness_plan}"
        
        print(f"\n{'='*60}")
        print("💪 AI-POWERED FITNESS PLAN")
        print(f"{'='*60}")
        print(full_plan)
        print(f"{'='*60}\n")
        
        await speak(full_plan)
    else:
        # Fallback basic plan
        if bmi < 18.5:
            plan = f"You're underweight. Focus on: Strength training 3x per week, Push-ups 3 sets of 10, Squats 3 sets of 15, Eat protein-rich foods. Water: {water_intake} liters daily."
        elif 18.5 <= bmi < 25:
            plan = f"You have a healthy weight. Maintain with: Cardio 30 min 4x per week, Strength training 3x per week, Push-ups 3 sets of 15, Squats 3 sets of 20, Balanced diet. Water: {water_intake} liters daily."
        elif 25 <= bmi < 30:
            plan = f"Focus on weight management: Cardio 40 min 5x per week, Walking, Cycling, Light strength training 3x per week, Calorie deficit diet. Water: {water_intake} liters daily."
        else:
            plan = f"Focus on gradual weight loss: Walking 30 min daily, Low-impact exercises, Avoid high-impact activities, Consult a doctor. Water: {water_intake} liters daily."
        
        if conditions != "None" or disability != "None":
            plan += " Please consult with a healthcare provider before starting."
        
        print(f"\n{'='*60}")
        print("💪 BASIC FITNESS PLAN")
        print(f"{'='*60}")
        print(plan)
        print(f"{'='*60}\n")
        
        await speak(plan)

# ============================================
# OTHER FUNCTIONS
# ============================================

async def open_any_website(command):
    known_sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "instagram": "https://www.instagram.com",
        "chatgpt": "https://chat.openai.com",
        "github": "https://github.com",
        "spotify": "https://open.spotify.com"
    }
    for name, url in known_sites.items():
        if name in command:
            await speak(f"Opening {name}")
            await asyncio.to_thread(webbrowser.open, url)
            return True
    if "open" in command:
        site = command.split("open")[-1].strip().replace(" ", "")
        url = f"https://www.{site}.com"
        await speak(f"Opening {site}")
        await asyncio.to_thread(webbrowser.open, url)
        return True
    return False

async def close_application(command):
    keyword = command.replace("close", "").replace("app", "").strip().lower()
    found = False
    for title in gw.getAllTitles():
        if keyword in title.lower():
            window = gw.getWindowsWithTitle(title)[0]
            try:
                window.close()
                await speak(f"Closed {keyword}")
                found = True
                break
            except:
                continue
    if not found:
        await speak(f"No window found with {keyword}")

async def search_anything(command):
    if "search" in command:
        query = command.replace("search", "").replace("for", "").strip()
        if "youtube" in command:
            query = query.replace("on youtube", "").strip()
            await speak(f"Searching YouTube for {query}")
            await asyncio.to_thread(webbrowser.open, f"https://www.youtube.com/results?search_query={query}")
        else:
            await search_with_gemini(query)

async def repeat_after_me(command):
    if "repeat after me" in command:
        to_repeat = command.split("repeat after me")[-1].strip()
    elif "say" in command:
        to_repeat = command.split("say")[-1].strip()
    else:
        return False
    if to_repeat:
        await speak(to_repeat)
        return True
    return False

async def set_timer(command):
    pattern = r"timer for (\d+)\s*(seconds|second|minutes|minute)"
    match = re.search(pattern, command.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        seconds = value if "second" in unit else value * 60
        await speak(f"Timer set for {value} {unit}")
        await asyncio.sleep(seconds)
        await speak(f"Time's up! Your timer has finished.")

async def set_reminder(command):
    """Parse and set a reminder"""
    try:
        print(f"\n🔍 DEBUG: Processing reminder command: '{command}'")
        
        # Parse time patterns
        now = datetime.datetime.now()
        
        # Pattern 1: "remind me to [task] in/after [X] [seconds/minutes/hours/days]"
        pattern1 = r"remind me to (.+?) (?:in|after) (\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days)"
        match1 = re.search(pattern1, command.lower())
        print(f"   Pattern 1 match: {match1.groups() if match1 else 'No match'}")
        
        # Pattern 2: "remind me to [task] at [time]"
        pattern2 = r"remind me to (.+?) at (\d{1,2}):?(\d{2})?\s*(am|pm)?"
        match2 = re.search(pattern2, command.lower())
        print(f"   Pattern 2 match: {match2.groups() if match2 else 'No match'}")
        
        # Pattern 3: "set reminder for [task] in/after [X] [seconds/minutes/hours]"
        pattern3 = r"set reminder (?:for|to) (.+?) (?:in|after) (\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days)"
        match3 = re.search(pattern3, command.lower())
        print(f"   Pattern 3 match: {match3.groups() if match3 else 'No match'}")
        
        # Pattern 4: "remind me in/after [X] [seconds/minutes/hours] to [task]"
        pattern4 = r"remind me (?:in|after) (\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days) to (.+)"
        match4 = re.search(pattern4, command.lower())
        print(f"   Pattern 4 match: {match4.groups() if match4 else 'No match'}")
        
        # Pattern 5: "remind [task] in/after [X] [time unit]" OR "remind to [task] after [X]"
        pattern5 = r"remind (?:me )?(?:to )?(.+?) (?:in|after) (\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days)"
        match5 = re.search(pattern5, command.lower())
        print(f"   Pattern 5 match: {match5.groups() if match5 else 'No match'}")
        
        task = None
        trigger_time = None
        
        if match1:
            print("   ✓ Using Pattern 1")
            task = match1.group(1).strip()
            value = int(match1.group(2))
            unit = match1.group(3)
            
            if "second" in unit:
                trigger_time = now + datetime.timedelta(seconds=value)
            elif "minute" in unit:
                trigger_time = now + datetime.timedelta(minutes=value)
            elif "hour" in unit:
                trigger_time = now + datetime.timedelta(hours=value)
            elif "day" in unit:
                trigger_time = now + datetime.timedelta(days=value)
        
        elif match2:
            print("   ✓ Using Pattern 2")
            task = match2.group(1).strip()
            hour = int(match2.group(2))
            minute = int(match2.group(3)) if match2.group(3) else 0
            period = match2.group(4)
            
            # Convert to 24-hour format
            if period and period.lower() == "pm" and hour != 12:
                hour += 12
            elif period and period.lower() == "am" and hour == 12:
                hour = 0
            
            trigger_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, set for tomorrow
            if trigger_time <= now:
                trigger_time += datetime.timedelta(days=1)
        
        elif match3:
            print("   ✓ Using Pattern 3")
            task = match3.group(1).strip()
            value = int(match3.group(2))
            unit = match3.group(3)
            
            if "second" in unit:
                trigger_time = now + datetime.timedelta(seconds=value)
            elif "minute" in unit:
                trigger_time = now + datetime.timedelta(minutes=value)
            elif "hour" in unit:
                trigger_time = now + datetime.timedelta(hours=value)
            elif "day" in unit:
                trigger_time = now + datetime.timedelta(days=value)
        
        elif match4:
            print("   ✓ Using Pattern 4")
            value = int(match4.group(1))
            unit = match4.group(2)
            task = match4.group(3).strip()
            
            if "second" in unit:
                trigger_time = now + datetime.timedelta(seconds=value)
            elif "minute" in unit:
                trigger_time = now + datetime.timedelta(minutes=value)
            elif "hour" in unit:
                trigger_time = now + datetime.timedelta(hours=value)
            elif "day" in unit:
                trigger_time = now + datetime.timedelta(days=value)
        
        elif match5:
            print("   ✓ Using Pattern 5")
            task = match5.group(1).strip()
            value = int(match5.group(2))
            unit = match5.group(3)
            
            if "second" in unit:
                trigger_time = now + datetime.timedelta(seconds=value)
            elif "minute" in unit:
                trigger_time = now + datetime.timedelta(minutes=value)
            elif "hour" in unit:
                trigger_time = now + datetime.timedelta(hours=value)
            elif "day" in unit:
                trigger_time = now + datetime.timedelta(days=value)
        
        print(f"   Extracted task: '{task}'")
        print(f"   Trigger time: {trigger_time}")
        
        if task and trigger_time:
            # Determine action type based on task
            action_type = "notification"
            if any(word in task.lower() for word in ["open", "website", "youtube", "google", "spotify"]):
                action_type = "open_website"
            elif any(word in task.lower() for word in ["play", "music", "song"]):
                action_type = "play_music"
            
            reminder = reminder_manager.add_reminder(task, trigger_time, action_type)
            
            # Format the time for speech
            time_diff = trigger_time - now
            if time_diff.total_seconds() < 60:  # Less than 1 minute
                seconds = int(time_diff.total_seconds())
                time_str = f"{seconds} second{'s' if seconds != 1 else ''}"
            elif time_diff.total_seconds() < 3600:  # Less than 1 hour
                minutes = int(time_diff.total_seconds() / 60)
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            elif time_diff.total_seconds() < 86400:  # Less than 1 day
                hours = int(time_diff.total_seconds() / 3600)
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                days = int(time_diff.total_seconds() / 86400)
                time_str = f"{days} day{'s' if days != 1 else ''}"
            
            await speak(f"Reminder set! I'll remind you to {task} in {time_str}.")
            print(f"\n✅ Reminder created:")
            print(f"   Task: {task}")
            print(f"   Time: {trigger_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Type: {action_type}")
            print(f"   Will trigger in {time_diff.total_seconds():.0f} seconds")
            return True
        else:
            print("   ❌ No pattern matched or task/time extraction failed")
            await speak("I couldn't understand the reminder format. Try saying: remind me to call John in 30 seconds, or remind me to drink water after 5 minutes.")
            return False
    
    except Exception as e:
        print(f"❌ Error setting reminder: {e}")
        import traceback
        traceback.print_exc()
        await speak("Sorry, I had trouble setting that reminder.")
        return False

async def list_reminders():
    """List all active reminders"""
    active = reminder_manager.get_active_reminders()
    
    if not active:
        await speak("You have no active reminders.")
        return
    
    await speak(f"You have {len(active)} active reminder{'s' if len(active) != 1 else ''}.")
    
    for i, reminder in enumerate(active[:5], 1):  # Limit to 5 reminders
        task = reminder["task"]
        trigger_time = datetime.datetime.fromisoformat(reminder["trigger_time"])
        time_left = trigger_time - datetime.datetime.now()
        
        if time_left.total_seconds() < 3600:
            minutes = int(time_left.total_seconds() / 60)
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = int(time_left.total_seconds() / 3600)
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"
        
        await speak(f"{i}. {task}, in {time_str}.")
    
    if len(active) > 5:
        await speak(f"And {len(active) - 5} more reminders.")

async def cancel_reminders():
    """Cancel all reminders"""
    active = reminder_manager.get_active_reminders()
    
    if not active:
        await speak("You have no active reminders to cancel.")
        return
    
    for reminder in active:
        reminder_manager.mark_completed(reminder["id"])
    
    await speak(f"Cancelled {len(active)} reminder{'s' if len(active) != 1 else ''}.")

async def time_based_greeting():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        await speak("Good morning! I'm Dorothy. How can I help?")
    elif 12 <= hour < 17:
        await speak("Good afternoon! I'm Dorothy. Do you Need any help?")
    elif 17 <= hour < 22:
        await speak("Good evening! I'm Dorothy.")
    else:
        await speak("Hello! I'm Dorothy.")

async def handle_small_talk(command):
    for key in responses:
        if key in command:
            await speak(random.choice(responses[key]))
            return True
    return False

async def play_media_anywhere(command):
    trigger_phrases = [
        "play video", "play on youtube", "watch video", "watch on youtube", 
        "youtube play", "show me video", "find video", "play song", "play music",
        "play on spotify", "spotify play", "play", "listen to"
    ]
    
    is_play_command = any(phrase in command.lower() for phrase in trigger_phrases)
    
    if is_play_command:
        media_query = command.lower()
        for phrase in trigger_phrases:
            media_query = media_query.replace(phrase, "")
        
        filler_words = ["of", "the", "a", "an", "by", "from", "on"]
        query_words = media_query.split()
        cleaned_query = " ".join([word for word in query_words if word not in filler_words]).strip()
        
        if not cleaned_query:
            await speak("What would you like me to play?")
            return True
            
        prefer_spotify = any(word in command.lower() for word in ["spotify", "song", "music", "listen"])
        prefer_youtube = any(word in command.lower() for word in ["youtube", "video", "watch", "show"])
        
        await speak(f"Playing {cleaned_query}")
        
        success = False
        if prefer_spotify or not prefer_youtube:
            success = await try_spotify_play(cleaned_query)
            if not success:
                await speak("Spotify didn't work, trying YouTube")
                success = await try_youtube_play(cleaned_query)
        else:
            success = await try_youtube_play(cleaned_query)
            if not success:
                await speak("YouTube didn't work, trying Spotify")
                success = await try_spotify_play(cleaned_query)
        
        if not success:
            await speak("Let me open both platforms for you to choose")
            await try_spotify_play(cleaned_query)
            await asyncio.sleep(2)
            await try_youtube_play(cleaned_query)
        
        return True
    return False

async def try_youtube_play(query):
    try:
        search_query = query.replace(" ", "+")
        youtube_url = f"https://www.youtube.com/results?search_query={search_query}"
        print(f"Opening YouTube: {youtube_url}")
        await asyncio.to_thread(webbrowser.open, youtube_url)
        await asyncio.sleep(7)
        try:
            pyautogui.moveTo(600, 600, duration=0.1)
            pyautogui.click(600, 600)
            await asyncio.sleep(1)
            return True
        except:
            pass
        return False
    except Exception as e:
        print(f"YouTube play failed: {e}")
        return False

async def try_spotify_play(query):
    try:
        search_query = query.replace(" ", "%20")
        spotify_url = f"https://open.spotify.com/search/{search_query}"
        print(f"Opening Spotify: {spotify_url}")
        await asyncio.to_thread(webbrowser.open, spotify_url)
        await asyncio.sleep(7)
        try:
            pyautogui.moveTo(800, 475, duration=0.1)
            pyautogui.click(800, 475)
            await asyncio.sleep(1)
            return True
        except:
            pass
        return False
    except Exception as e:
        print(f"Spotify play failed: {e}")
        return False

async def play_song_on_spotify(command):
    if "play" in command and "spotify" in command:
        song = command.replace("play", "").replace("on spotify", "").strip()
        await speak(f"Playing {song} on Spotify")
        await asyncio.to_thread(webbrowser.open, f"https://open.spotify.com/search/{song}")
        await asyncio.sleep(5)
        pyautogui.moveTo(800, 475, duration=0.1)
        pyautogui.click(800, 475)

async def play_song_on_youtube(command):
    if "play" in command and "youtube" in command:
        song = command.replace("play", "").replace("on youtube", "").strip()
        await speak(f"Playing {song} on YouTube")
        await asyncio.to_thread(webbrowser.open, f"https://www.youtube.com/results?search_query={song}")
        await asyncio.sleep(5)
        pyautogui.moveTo(600,600, duration=0.1)
        pyautogui.click(600, 600)

async def set_reminder(command):
    """Parse and set a reminder"""
    try:
        # Parse time patterns
        now = datetime.datetime.now()
        
        # Pattern 1: "remind me to [task] in [X] [minutes/hours/days]"
        pattern1 = r"remind me to (.+?) in (\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days)"
        match1 = re.search(pattern1, command.lower())
        
        # Pattern 2: "remind me to [task] at [time]"
        pattern2 = r"remind me to (.+?) at (\d{1,2}):?(\d{2})?\s*(am|pm)?"
        match2 = re.search(pattern2, command.lower())
        
        # Pattern 3: "set reminder for [task] in [X] [minutes/hours]"
        pattern3 = r"set reminder for (.+?) in (\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days)"
        match3 = re.search(pattern3, command.lower())
        
        # Pattern 4: "remind me in [X] [minutes/hours] to [task]"
        pattern4 = r"remind me in (\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days) to (.+)"
        match4 = re.search(pattern4, command.lower())
        
        task = None
        trigger_time = None
        
        if match1:
            task = match1.group(1).strip()
            value = int(match1.group(2))
            unit = match1.group(3)
            
            if "minute" in unit:
                trigger_time = now + datetime.timedelta(minutes=value)
            elif "hour" in unit:
                trigger_time = now + datetime.timedelta(hours=value)
            elif "day" in unit:
                trigger_time = now + datetime.timedelta(days=value)
            elif "second" in unit:
                trigger_time = now + datetime.timedelta(seconds=value)
        
        elif match2:
            task = match2.group(1).strip()
            hour = int(match2.group(2))
            minute = int(match2.group(3)) if match2.group(3) else 0
            period = match2.group(4)
            
            # Convert to 24-hour format
            if period and period.lower() == "pm" and hour != 12:
                hour += 12
            elif period and period.lower() == "am" and hour == 12:
                hour = 0
            
            trigger_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, set for tomorrow
            if trigger_time <= now:
                trigger_time += datetime.timedelta(days=1)
        
        elif match3:
            task = match3.group(1).strip()
            value = int(match3.group(2))
            unit = match3.group(3)
            
            if "minute" in unit:
                trigger_time = now + datetime.timedelta(minutes=value)
            elif "hour" in unit:
                trigger_time = now + datetime.timedelta(hours=value)
            elif "day" in unit:
                trigger_time = now + datetime.timedelta(days=value)
            elif "second" in unit:
                trigger_time = now + datetime.timedelta(seconds=value)
        
        elif match4:
            value = int(match4.group(1))
            unit = match4.group(2)
            task = match4.group(3).strip()
            
            if "minute" in unit:
                trigger_time = now + datetime.timedelta(minutes=value)
            elif "hour" in unit:
                trigger_time = now + datetime.timedelta(hours=value)
            elif "day" in unit:
                trigger_time = now + datetime.timedelta(days=value)
            elif "second" in unit:
                trigger_time = now + datetime.timedelta(seconds=value)
        
        if task and trigger_time:
            # Determine action type based on task
            action_type = "notification"
            if any(word in task.lower() for word in ["open", "website", "youtube", "google", "spotify"]):
                action_type = "open_website"
            elif any(word in task.lower() for word in ["play", "music", "song"]):
                action_type = "play_music"
            
            reminder = reminder_manager.add_reminder(task, trigger_time, action_type)
            
            # Format the time for speech
            time_diff = trigger_time - now
            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                minutes = int(time_diff.total_seconds() / 60)
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            elif time_diff.total_seconds() < 86400:  # Less than 1 day
                hours = int(time_diff.total_seconds() / 3600)
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"
            elif time_diff.total_seconds() < 60:  # Less than 1 minute
                seconds = int(time_diff.total_seconds())
                time_str = f"{seconds} second{'s' if seconds != 1 else ''}"
            else:
                days = int(time_diff.total_seconds() / 86400)
                time_str = f"{days} day{'s' if days != 1 else ''}"
            
            await speak(f"Reminder set! I'll remind you to {task} in {time_str}.")
            print(f"\n✅ Reminder created:")
            print(f"   Task: {task}")
            print(f"   Time: {trigger_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Type: {action_type}")
            return True
        else:
            await speak("I couldn't understand the reminder format. Try saying: remind me to call John in 30 minutes.")
            return False
    
    except Exception as e:
        print(f"Error setting reminder: {e}")
        await speak("Sorry, I had trouble setting that reminder.")
        return False

async def list_reminders():
    """List all active reminders"""
    active = reminder_manager.get_active_reminders()
    
    if not active:
        await speak("You have no active reminders.")
        return
    
    await speak(f"You have {len(active)} active reminder{'s' if len(active) != 1 else ''}.")
    
    for i, reminder in enumerate(active[:5], 1):  # Limit to 5 reminders
        task = reminder["task"]
        trigger_time = datetime.datetime.fromisoformat(reminder["trigger_time"])
        time_left = trigger_time - datetime.datetime.now()
        
        if time_left.total_seconds() < 3600:
            minutes = int(time_left.total_seconds() / 60)
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = int(time_left.total_seconds() / 3600)
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"
        
        await speak(f"{i}. {task}, in {time_str}.")
    
    if len(active) > 5:
        await speak(f"And {len(active) - 5} more reminders.")

async def cancel_reminders():
    """Cancel all reminders"""
    active = reminder_manager.get_active_reminders()
    
    if not active:
        await speak("You have no active reminders to cancel.")
        return
    
    for reminder in active:
        reminder_manager.mark_completed(reminder["id"])
    
    await speak(f"Cancelled {len(active)} reminder{'s' if len(active) != 1 else ''}.")

# ============================================
# GUI CLASS
# ============================================

class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DOROTHY AI")
        self.root.geometry("800x700")
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)

        self.canvas = tk.Canvas(self.root, width=800, height=700, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        gif = Image.open(resource_path("ai.gif"))
        frame_size = (800, 700)
        self.frames = [ImageTk.PhotoImage(img.resize(frame_size, Image.LANCZOS).convert('RGBA'))
                       for img in ImageSequence.Iterator(gif)]
        self.gif_index = 0
        self.bg_image = self.canvas.create_image(0, 0, anchor='nw', image=self.frames[0])
        self.animate()

        self.chat_log = Text(self.root, bg="#000000", fg="sky blue", font=("Consolas", 10), wrap='word', bd=0)
        self.chat_log.place(x=0, y=600, width=800, height=100)
        self.chat_log.insert(END, "[System] Type or press F2 to speak.\n")
        self.chat_log.config(state=tk.DISABLED)

        scrollbar = Scrollbar(self.root, command=self.chat_log.yview)
        scrollbar.place(x=780, y=600, height=100)
        self.chat_log.config(yscrollcommand=scrollbar.set)

        self.entry = tk.Entry(self.root, font=("Segoe UI", 13), bg="#1a1a1a", fg="white", bd=3, insertbackground='white')
        self.entry.place(x=20, y=670, width=700, height=30)
        self.entry.bind("<Return>", self.send_text)

        send_button = tk.Button(self.root, text="Send", command=self.send_text, bg="#222222", fg="white", relief='flat')
        send_button.place(x=730, y=670, width=50, height=30)

        self.root.bind("<F2>", lambda e: Thread(target=self.listen_voice).start())
        Thread(target=lambda: asyncio.run(time_based_greeting())).start()

    def animate(self):
        self.canvas.itemconfig(self.bg_image, image=self.frames[self.gif_index])
        self.gif_index = (self.gif_index + 1) % len(self.frames)
        self.root.after(100, self.animate)

    def send_text(self, event=None):
        user_input = self.entry.get()
        self.entry.delete(0, END)
        if user_input:
            self.add_text("You: " + user_input)
            Thread(target=lambda: asyncio.run(self.handle_command(user_input))).start()

    def add_text(self, text):
        self.chat_log.config(state=tk.NORMAL)
        self.chat_log.insert(END, text + "\n")
        self.chat_log.config(state=tk.DISABLED)
        self.chat_log.see(END)

    def listen_voice(self):
        self.add_text("[System] Listening...")
        command = listen_command()
        if command:
            self.add_text("You: " + command)
            Thread(target=lambda: asyncio.run(self.handle_command(command))).start()

    async def handle_command(self, command):
        if command == "network error":
            await speak("Network error.")
            return

        if await handle_small_talk(command):
            return

        if "open" in command:
            if await open_any_website(command):
                return

        if "close" in command:
            await close_application(command)
            return
        
        # Timer commands
        if "timer" in command and "remind" not in command:
            await set_timer(command)
            return
        
        # Reminder commands
        if "remind" in command or "reminder" in command:
            if "list" in command or "show" in command or "what are" in command:
                await list_reminders()
                return
            elif "cancel" in command or "delete" in command or "clear" in command:
                await cancel_reminders()
                return
            else:
                await set_reminder(command)
                return

        if await repeat_after_me(command):
            return

        if "who is" in command or "who was" in command:
            person = command.replace("who is", "").replace("who was", "").strip()
            if person:
                await search_about_person_gemini(person)
                return

        if "fitness" in command or "exercise" in command or "workout" in command:
            await get_comprehensive_fitness_plan()
            return

        if "search" in command:
            await search_anything(command)
            return

        if "play" in command:
            if await play_media_anywhere(command):
                return

        if "exit" in command or "quit" in command or "bye" in command:
            await speak("Goodbye!")
            reminder_manager.stop_monitoring()
            self.root.quit()
            return

        # Default: use Gemini
        await search_with_gemini(command)

def main():
    # Start reminder monitoring
    reminder_manager.start_monitoring()
    
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()
    
    # Stop reminder monitoring on exit
    reminder_manager.stop_monitoring()

if __name__ == "__main__":
    main()