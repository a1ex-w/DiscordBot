import discord
import os
import pyttsx3
import requests
import asyncio
import random
import datetime
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# List of sarcastic comments
SARCASTIC_MESSAGES = [
    "Oh boy, {name} is in another match. This should be *interesting*... 🙃",
    "And here we go again! Can't wait to hear the excuses, {name}!",
    "Ah yes, another match. Surely this time, it's *not* the team's fault, right {name}? 😏",
    "Breaking news: {name} has entered the Rift! Time for the classic *'my team is trolling'* speech!",
    "Everyone stay back, {name} is about to put on a masterclass... or at least, that's what they'll say later. 🤡",
]

# Get API keys from .env
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Riot API Key (store this in your .env file)
RIOT_API_KEY = os.getenv("RIOT_API_KEY")

# Your friend's Riot account details (Replace with their actual summoner name and tag)
SUMMONER_NAME = "PostNutClarity"
SUMMONER_TAG = "HELP"

# Riot API URLs
PUUID_URL = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{}/{}"
MATCH_HISTORY_URL = "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?start=0&count=1"

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.voice_states = True      # Enable tracking voice channel changes
intents.presences = True         # Enable tracking user presence and activities

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize TTS engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)  # Adjust speech speed

# Replace with your friend's Discord user ID
TARGET_USER_ID = 177911196266004480  # Use your own for testing

def generate_greeting(user_name):
    """Generates a static humorous greeting message."""
    return f"Oh great, {user_name} has arrived. Everyone, act natural."

async def speak(vc, text):
    """Converts text to speech, plays it in the voice channel, and deletes the output file afterward."""
    # Generate TTS output file
    tts_engine.save_to_file(text, "tts_output.mp3")
    tts_engine.runAndWait()
    
    # Play the audio in the voice channel
    vc.play(discord.FFmpegPCMAudio("tts_output.mp3"), after=lambda e: cleanup("tts_output.mp3"))

def cleanup(file_path):
    """Deletes the specified file after playback."""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    else:
        print(f"File not found: {file_path}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')

# Global variable to track last seen League of Legends match 
last_match_id = None

async def fetch_puuid():
    """Fetches PUUID using summoner name and tag."""
    url = PUUID_URL.format(SUMMONER_NAME, SUMMONER_TAG)
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["puuid"]
    else:
        print(f"Failed to fetch PUUID: {response.json()}")
        return None

async def check_for_new_match():
    """Checks if a new match has started and announces it in voice chat, with debug logging."""
    global last_match_id
    puuid = await fetch_puuid()
    
    if not puuid:
        print("[DEBUG] Failed to retrieve PUUID.")
        return
    
    url = MATCH_HISTORY_URL.format(puuid)
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    print(f"[{datetime.datetime.now()}] [DEBUG] Fetching match history for {SUMMONER_NAME} (PUUID: {puuid})...")
    
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        matches = response.json()
        
        if matches:
            latest_match = matches[0]  # Latest match ID
            
            print(f"[{datetime.datetime.now()}] [DEBUG] Latest match ID: {latest_match}")
            
            if latest_match != last_match_id:
                print(f"[{datetime.datetime.now()}] [DEBUG] New match detected! Previous: {last_match_id}, New: {latest_match}")
                last_match_id = latest_match
                
                # Check if bot is in a voice channel
                vc = discord.utils.get(bot.voice_clients, guild=bot.guilds[0])  # Assuming one guild
                if vc and vc.is_connected():
                    sarcastic_message = random.choice(SARCASTIC_MESSAGES).format(name=SUMMONER_NAME)
                    print(f"[{datetime.datetime.now()}] [DEBUG] Sending TTS message: {sarcastic_message}")
                    await speak(vc, sarcastic_message)  # Use the existing TTS function
            else:
                print(f"[{datetime.datetime.now()}] [DEBUG] No new match detected. Last match remains: {last_match_id}")
    else:
        print(f"[DEBUG] Failed to fetch match history: {response.status_code} - {response.text}")

async def monitor_matches():
    """Runs the match checker every 60 seconds."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await check_for_new_match()
        await asyncio.sleep(60)  # Check every 60 seconds

# Start monitoring when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    bot.loop.create_task(monitor_matches())

@bot.event
async def on_voice_state_update(member, before, after):
    """Automatically joins a target user's channel and greets them with TTS."""
    if member.id == TARGET_USER_ID:
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)

        if after.channel:  # If the user joined a channel
            if vc:
                if vc.channel != after.channel:  # Move to the new channel
                    await vc.move_to(after.channel)
            else:  # If the bot is not connected, join the new channel
                vc = await after.channel.connect()

            # Generate a greeting for the user
            greeting = generate_greeting(member.name)  
            await speak(vc, greeting)  # Speak the greeting
        else:  # If the user leaves the channel
            if vc and vc.channel == before.channel:  # If bot is in the same channel
                if len(before.channel.members) == 1:  # If no other members are present
                    await vc.disconnect()
@bot.command(name="testmatch")
async def test_match(ctx):
    """Manually trigger a fake match detection for testing."""
    global last_match_id
    last_match_id = None  # Reset last match to force a new detection
    await check_for_new_match()
    await ctx.send("Test match triggered!")
@bot.command(name="testdebug")
async def test_debug(ctx):
    """Manually trigger a match check with debug logging."""
    global last_match_id
    last_match_id = None  # Reset last match to force a new detection
    await check_for_new_match()
    await ctx.send("Debug test triggered! Check console for logs.")
# Run the bot
bot.run(DISCORD_BOT_TOKEN)
