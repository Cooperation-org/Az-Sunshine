import anthropic
import os
from django.conf import settings

def get_claude_client():
    """Initialize Claude client"""
    api_key = settings.ANTHROPIC_API_KEY or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in settings or environment")
    return anthropic.Anthropic(api_key=api_key)

def ask_claude(prompt, max_tokens=4096):
    """Simple helper to ask Claude a question"""
    client = get_claude_client()
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
