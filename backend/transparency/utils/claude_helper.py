import os
from anthropic import Anthropic
from django.conf import settings

class ClaudeHelper:
    """Helper class for Claude API interactions"""
    
    def __init__(self):
        api_key = os.environ.get('ANTHROPIC_API_KEY') or settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def chat(self, messages, max_tokens=2048):
        """Send messages to Claude and get response"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_text(self, text, prompt):
        """Analyze text with a prompt"""
        full_prompt = f"{prompt}\n\n{text}" if text else prompt
        return self.chat([{"role": "user", "content": full_prompt}])

# Singleton instance
_instance = None

def get_claude():
    global _instance
    if _instance is None:
        _instance = ClaudeHelper()
    return _instance