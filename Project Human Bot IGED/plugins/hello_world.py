"""
Hello World Plugin for IGED
Sample plugin demonstrating the plugin system
"""

class Plugin:
    def __init__(self):
        self.name = "Hello World"
        self.version = "1.0.0"
        self.description = "A simple hello world plugin"
    
    def run(self, input_text):
        """Run the plugin with input text"""
        return f"Hello, {input_text}! This is the Hello World plugin speaking."
    
    def get_info(self):
        """Get plugin information"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description
        } 