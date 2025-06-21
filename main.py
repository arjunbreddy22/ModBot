import os
import discord
from dotenv import load_dotenv
from agent.agent_service import ModerationAgent

 

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

agent = ModerationAgent() 
@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    print(f"📩 {message.author}: {message.content}")

    #handles update_rules
    if message.content.startswith("!update_rules "):
        rules_text = message.content[len("!update_rules "):]
        agent.update_rules_text(rules_text)
        await message.channel.send("✅ Rules updated.")
        print(agent.rules_source)
        return
    # Ask the agent what to do
    action = agent.moderate_message(message.content)

    # Execute the action
    if action == "OK":
        print(action)
        return

    if action == "Warn":
        print(action)
        await message.channel.send("⚠️ Please watch your language.")

    elif action == "Delete":
        print(action)
        await message.delete()
        await message.channel.send("Message deleted.")

    elif action == "Ban":
        print(action)
        await message.author.ban(reason="Violation of rules")
        await message.channel.send("User banned.")

client.run(TOKEN)
