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
    
    # Use the updated API call
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

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
    if member.id == TARGET_USER_ID and after.channel is not None:  # If the user joins a channel
        channel = after.channel
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)

        if vc and vc.channel != channel:  # If bot is in a different channel, move it
            await vc.move_to(channel)
        elif not vc:  # If bot is not in a channel, join
            vc = await channel.connect()

        # Use a static greeting for testing TTS functionality
        greeting = f"Welcome, {member.name}! Ready to play some games?"  # Static greeting
        await speak(vc, greeting)  # Speak the greeting

@bot.command()
async def join(ctx):
    """Makes the bot join the user's voice channel."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel.name}! 🔊")
    else:
        await ctx.send("You need to be in a voice channel first! 🚫")

@bot.command()
async def leave(ctx):
    """Makes the bot leave the voice channel."""
    vc = ctx.guild.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("Left the voice channel! 👋")
    else:
        await ctx.send("I'm not in a voice channel! 🤷")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)