from keep_alive import keep_alive
import discord
from discord import app_commands
import asyncio
import datetime
import os

TOKEN = os.environ['key']

class TimelineBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.current_date = None
        self.timer_running = False
        self.pause_timer = False
        self.message_reference = None

    async def setup_hook(self):
        # Sync commands globally
        await self.tree.sync(guild=None)
        print("Commands synced!")

client = TimelineBot()

def get_date_string(date, hour=0):
    return f"# {date.day} {date.strftime('%b')} {date.year}, {hour:02d}:00"

@client.tree.command(name="start", description="Start the timeline from January 1st, 1939")
async def start(interaction: discord.Interaction):
    if client.timer_running:
        await interaction.response.send_message("Stop the previous timer first")
        return

    client.current_date = datetime.date(1939, 1, 1)
    client.timer_running = True
    await interaction.response.send_message(get_date_string(client.current_date))
    client.message_reference = await interaction.original_response()
    await start_timer()

@client.tree.command(name="customstart", description="Start the timeline from a custom date")
async def customstart(interaction: discord.Interaction):
    if client.timer_running:
        await interaction.response.send_message("Stop the previous timer first")
        return

    await interaction.response.send_message("Enter the starting date in DD/MM/YYYY format (between 01/01/1939 and 31/12/1953).")

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        user_input = await client.wait_for('message', check=check, timeout=60)
        day, month, year = map(int, user_input.content.split('/'))
        if 1939 <= year <= 1953 and 1 <= month <= 12 and 1 <= day <= 31:
            client.current_date = datetime.date(year, month, day)
            client.timer_running = True
            message = await interaction.channel.send(get_date_string(client.current_date))
            client.message_reference = message
            await start_timer()
        else:
            await interaction.channel.send("Invalid date. Enter in DD/MM/YYYY format within the allowed range.")
    except asyncio.TimeoutError:
        await interaction.channel.send("You took too long to respond. Please try again.")
    except ValueError:
        await interaction.channel.send("Invalid format. Use DD/MM/YYYY.")

@client.tree.command(name="pause", description="Pause the timeline")
async def pause(interaction: discord.Interaction):
    if client.timer_running:
        client.pause_timer = True
        client.timer_running = False
        await interaction.response.send_message(f"Timer paused at {get_date_string(client.current_date)}")
    else:
        await interaction.response.send_message("Start the timer first before pausing.")

@client.tree.command(name="resume", description="Resume the timeline")
async def resume(interaction: discord.Interaction):
    if client.pause_timer:
        client.pause_timer = False
        client.timer_running = True
        await interaction.response.send_message("Timer resumed!")
        await start_timer()
    elif client.timer_running:
        await interaction.response.send_message("The timer is already running. Use /stop first if needed.")
    else:
        await interaction.response.send_message("Start a new timer first.")

@client.tree.command(name="stop", description="Stop the timeline")
async def stop(interaction: discord.Interaction):
    if client.timer_running or client.pause_timer:
        client.timer_running = False
        client.pause_timer = False
        await interaction.response.send_message(f"The counter has been stopped. Last count: {get_date_string(client.current_date)}")
    else:
        await interaction.response.send_message("Start the timer first.")

async def start_timer():
    current_hour = 0
    while client.timer_running:
        try:
            if not client.pause_timer:
                await client.message_reference.edit(content=get_date_string(client.current_date, current_hour))
                await asyncio.sleep(40)  # 40 seconds = 1 hour in-game
                
                current_hour += 1
                if current_hour >= 24:
                    current_hour = 0
                    client.current_date += datetime.timedelta(days=1)
                
                if client.current_date >= datetime.date(1954, 1, 1):
                    await client.message_reference.edit(content="Your timer has been stopped at 1st January 1954. World War II has ended.")
                    client.timer_running = False
            else:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Failed to update message: {e}")
            client.timer_running = False

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
keep_alive()
client.run(TOKEN)
