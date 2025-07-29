"""
Discord Notification Plugin for IGED
Sends notifications to Discord webhook
"""

import requests
import json
from datetime import datetime

class Plugin:
    def __init__(self):
        self.name = "Discord Notifier"
        self.version = "1.0.0"
        self.description = "Sends notifications to Discord webhook"
        self.webhook_url = None
    
    def run(self, input_text):
        """Run the plugin with input text"""
        try:
            # Check if webhook URL is configured
            if not self.webhook_url:
                return "❌ Discord webhook URL not configured. Set webhook_url in plugin."
            
            # Create Discord message
            message = {
                "content": f"🤖 IGED Notification: {input_text}",
                "embeds": [{
                    "title": "IGED Command Executed",
                    "description": input_text,
                    "color": 0x00ff00,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {
                        "text": "IGED - Sovereign AI Assistant"
                    }
                }]
            }
            
            # Send to Discord
            response = requests.post(self.webhook_url, json=message)
            
            if response.status_code == 204:
                return f"✅ Discord notification sent: {input_text}"
            else:
                return f"❌ Failed to send Discord notification: {response.status_code}"
                
        except Exception as e:
            return f"❌ Discord notification error: {str(e)}"
    
    def configure(self, webhook_url):
        """Configure the webhook URL"""
        self.webhook_url = webhook_url
        return f"✅ Discord webhook configured: {webhook_url[:50]}..."
    
    def get_info(self):
        """Get plugin information"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'configured': self.webhook_url is not None
        } 