# test_agent.py

from agent_service import ModerationAgent

# Example server rules text (could also pull from #server-rules channel)
server_rules = """
1. No hate speech or harassment.
2. No spamming or flooding chat.
3. Be respectful — no personal attacks.
4. Mild profanity allowed, but no directed insults.
5. Follow Discord terms of service.
"""

# Create the agent with server rules
agent = ModerationAgent(server_rules=server_rules)

# Example context (previous messages)
context = [
    "User1: hey guys what's up",
    "User2: all good here!",
    "User3: welcome to the server!",
]

# agent.update_rules_text("If the user swears = warn. If the user attacks someone on a personal level = delete the message.")

# Example message to moderate
new_message = "hi"


# Call the moderation agent
action = agent.moderate_message(message=new_message, context=context)

# Print the result
print(f"Moderation Action: {action}")
