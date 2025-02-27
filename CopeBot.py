import discord
import os
import openai
import pyttsx3
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from .env
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.voice_states = True      # Enable tracking voice channel changes
intents.presences = True         # Enable tracking user presence and activities

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

# Initialize TTS engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)  # Adjust speech speed

# Replace with your friend's Discord user ID
TARGET_USER_ID = 177911196266004480  # Use your own for testing

async def generate_greeting(user_name):
    """Fetches a greeting message from GPT-4 based on the user's name."""
    prompt = f"Create a series of informal, humorous, and slightly sarcastic remarks for {user_name} when they join a voice chat. The tone should be playful yet critical, incorporating regional slang or accents."

    # Check if API key is set
    if not OPENAI_API_KEY:
        return "API key is not set. Please configure it."

    try:
        # Updated API call
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating greeting: {str(e)}"


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
            greeting = await generate_greeting(member.name)  
            await speak(vc, greeting)  # Speak the greeting
        else:  # If the user leaves the channel
            if vc and vc.channel == before.channel:  # If bot is in the same channel
                if len(before.channel.members) == 1:  # If no other members are present
                    await vc.disconnect()

# Run the bot
bot.run(DISCORD_BOT_TOKEN)