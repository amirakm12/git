"""
IGED GUI - Windows Interface
Main window for the IGED assistant
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IGEDGUI:
    def __init__(self, components):
        self.components = components
        self.root = tk.Tk()
        self.setup_gui()
        self.message_queue = queue.Queue()
        self.running = True
        
        # Start message processing thread
        self.message_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.message_thread.start()
    
    def setup_gui(self):
        """Setup the GUI interface"""
        self.root.title("IGED - Project Human Bot")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2b2b2b')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
        style.configure('TButton', background='#4a4a4a', foreground='#ffffff')
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="🤖 IGED - Sovereign AI Assistant", 
                              font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='#00ff00')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Main interface tab
        self.create_main_tab()
        
        # Memory tab
        self.create_memory_tab()
        
        # System status tab
        self.create_status_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_main_tab(self):
        """Create the main interface tab"""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="🎯 Main Interface")
        
        # Command input frame
        input_frame = ttk.Frame(main_tab)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Command input
        tk.Label(input_frame, text="Enter Command:", bg='#2b2b2b', fg='#ffffff').pack(anchor=tk.W)
        
        self.command_entry = tk.Entry(input_frame, font=('Arial', 12), bg='#3b3b3b', fg='#ffffff')
        self.command_entry.pack(fill=tk.X, pady=(5, 10))
        self.command_entry.bind('<Return>', self.execute_command)
        
        # Buttons frame
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X)
        
        # Execute button
        execute_btn = tk.Button(button_frame, text="🚀 Execute", command=self.execute_command,
                               bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        execute_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Voice toggle button
        self.voice_btn = tk.Button(button_frame, text="🎤 Start Voice", command=self.toggle_voice,
                                  bg='#2196F3', fg='white', font=('Arial', 10, 'bold'))
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = tk.Button(button_frame, text="🗑️ Clear", command=self.clear_output,
                             bg='#f44336', fg='white', font=('Arial', 10, 'bold'))
        clear_btn.pack(side=tk.LEFT)
        
        # Output frame
        output_frame = ttk.Frame(main_tab)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Output label
        tk.Label(output_frame, text="Output:", bg='#2b2b2b', fg='#ffffff').pack(anchor=tk.W)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, height=20, bg='#1e1e1e', 
                                                    fg='#00ff00', font=('Consolas', 10))
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status bar
        self.status_label = tk.Label(main_tab, text="Ready", bg='#2b2b2b', fg='#888888')
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def create_memory_tab(self):
        """Create the memory tab"""
        memory_tab = ttk.Frame(self.notebook)
        self.notebook.add(memory_tab, text="🧠 Memory")
        
        # Memory controls frame
        controls_frame = ttk.Frame(memory_tab)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Search frame
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="Search Memory:", bg='#2b2b2b', fg='#ffffff').pack(side=tk.LEFT)
        
        self.search_entry = tk.Entry(search_frame, bg='#3b3b3b', fg='#ffffff')
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        search_btn = tk.Button(search_frame, text="🔍 Search", command=self.search_memory,
                              bg='#2196F3', fg='white')
        search_btn.pack(side=tk.RIGHT)
        
        # Memory list frame
        list_frame = ttk.Frame(memory_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Memory list
        columns = ('Time', 'Command', 'Agent', 'Status')
        self.memory_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.memory_tree.heading(col, text=col)
            self.memory_tree.column(col, width=150)
        
        self.memory_tree.pack(fill=tk.BOTH, expand=True)
        
        # Memory details frame
        details_frame = ttk.Frame(memory_tab)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(details_frame, text="Memory Details:", bg='#2b2b2b', fg='#ffffff').pack(anchor=tk.W)
        
        self.memory_details = scrolledtext.ScrolledText(details_frame, height=10, bg='#1e1e1e', 
                                                       fg='#00ff00', font=('Consolas', 9))
        self.memory_details.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Bind selection event
        self.memory_tree.bind('<<TreeviewSelect>>', self.on_memory_select)
        
        # Load initial memory
        self.load_memory()
    
    def create_status_tab(self):
        """Create the system status tab"""
        status_tab = ttk.Frame(self.notebook)
        self.notebook.add(status_tab, text="📊 System Status")
        
        # Status frame
        status_frame = ttk.Frame(status_tab)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System info
        info_frame = ttk.LabelFrame(status_frame, text="System Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.system_info = scrolledtext.ScrolledText(info_frame, height=8, bg='#1e1e1e', 
                                                    fg='#00ff00', font=('Consolas', 9))
        self.system_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Agents status
        agents_frame = ttk.LabelFrame(status_frame, text="Agents Status")
        agents_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.agents_info = scrolledtext.ScrolledText(agents_frame, height=6, bg='#1e1e1e', 
                                                    fg='#00ff00', font=('Consolas', 9))
        self.agents_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Refresh button
        refresh_btn = tk.Button(status_frame, text="🔄 Refresh Status", command=self.refresh_status,
                               bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        refresh_btn.pack(pady=10)
        
        # Load initial status
        self.refresh_status()
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="⚙️ Settings")
        
        # Settings frame
        settings_frame = ttk.Frame(settings_tab)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Voice settings
        voice_frame = ttk.LabelFrame(settings_frame, text="Voice Settings")
        voice_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(voice_frame, text="Voice Sensitivity:", bg='#2b2b2b', fg='#ffffff').pack(anchor=tk.W)
        self.voice_sensitivity = tk.Scale(voice_frame, from_=0.1, to=1.0, resolution=0.1, 
                                         orient=tk.HORIZONTAL, bg='#2b2b2b', fg='#ffffff')
        self.voice_sensitivity.set(0.5)
        self.voice_sensitivity.pack(fill=tk.X, padx=10, pady=5)
        
        # Memory settings
        memory_frame = ttk.LabelFrame(settings_frame, text="Memory Settings")
        memory_frame.pack(fill=tk.X, pady=(0, 10))
        
        clear_memory_btn = tk.Button(memory_frame, text="🗑️ Clear All Memory", 
                                    command=self.clear_all_memory, bg='#f44336', fg='white')
        clear_memory_btn.pack(pady=10)
        
        export_memory_btn = tk.Button(memory_frame, text="📤 Export Memory", 
                                     command=self.export_memory, bg='#2196F3', fg='white')
        export_memory_btn.pack(pady=5)
        
        # System settings
        system_frame = ttk.LabelFrame(settings_frame, text="System Settings")
        system_frame.pack(fill=tk.X, pady=(0, 10))
        
        offline_mode_var = tk.BooleanVar()
        offline_check = tk.Checkbutton(system_frame, text="Offline Mode", 
                                      variable=offline_mode_var, bg='#2b2b2b', fg='#ffffff')
        offline_check.pack(anchor=tk.W, padx=10, pady=5)
    
    def execute_command(self, event=None):
        """Execute a command"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        self.log_output(f"🎯 Executing: {command}")
        self.command_entry.delete(0, tk.END)
        
        # Execute in separate thread
        threading.Thread(target=self._execute_command_thread, args=(command,), daemon=True).start()
    
    def _execute_command_thread(self, command):
        """Execute command in background thread"""
        try:
            # Process command through voice pipeline
            if 'voice' in self.components:
                self.components['voice'].process_text_command(command)
            else:
                self.log_output("❌ Voice pipeline not available")
                
        except Exception as e:
            self.log_output(f"❌ Command execution error: {e}")
    
    def toggle_voice(self):
        """Toggle voice listening"""
        try:
            if 'voice' in self.components:
                voice = self.components['voice']
                if voice.is_listening:
                    voice.stop_listening()
                    self.voice_btn.config(text="🎤 Start Voice", bg='#2196F3')
                    self.log_output("🛑 Voice listening stopped")
                else:
                    voice.start_listening()
                    self.voice_btn.config(text="🛑 Stop Voice", bg='#f44336')
                    self.log_output("🎤 Voice listening started")
            else:
                self.log_output("❌ Voice pipeline not available")
                
        except Exception as e:
            self.log_output(f"❌ Voice toggle error: {e}")
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.delete(1.0, tk.END)
    
    def log_output(self, message):
        """Add message to output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to queue for thread-safe update
        self.message_queue.put(formatted_message)
    
    def _process_messages(self):
        """Process messages from queue"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=1)
                self.output_text.insert(tk.END, message)
                self.output_text.see(tk.END)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Message processing error: {e}")
    
    def load_memory(self):
        """Load memory entries into tree view"""
        try:
            # Clear existing items
            for item in self.memory_tree.get_children():
                self.memory_tree.delete(item)
            
            if 'memory' in self.components:
                memory = self.components['memory']
                entries = memory.get_recent_entries(50)
                
                for entry in entries:
                    timestamp = entry.get('timestamp', '')[:19]  # Truncate to seconds
                    command = entry.get('command', '')[:50]  # Truncate long commands
                    agent = entry.get('agent', 'unknown')
                    success = "✅" if entry.get('success', False) else "❌"
                    
                    self.memory_tree.insert('', 'end', values=(timestamp, command, agent, success))
                    
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
    
    def search_memory(self):
        """Search memory entries"""
        query = self.search_entry.get().strip()
        if not query:
            self.load_memory()
            return
        
        try:
            # Clear existing items
            for item in self.memory_tree.get_children():
                self.memory_tree.delete(item)
            
            if 'memory' in self.components:
                memory = self.components['memory']
                entries = memory.search_entries(query, 20)
                
                for entry in entries:
                    timestamp = entry.get('timestamp', '')[:19]
                    command = entry.get('command', '')[:50]
                    agent = entry.get('agent', 'unknown')
                    success = "✅" if entry.get('success', False) else "❌"
                    
                    self.memory_tree.insert('', 'end', values=(timestamp, command, agent, success))
                    
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
    
    def on_memory_select(self, event):
        """Handle memory item selection"""
        selection = self.memory_tree.selection()
        if not selection:
            return
        
        try:
            item = self.memory_tree.item(selection[0])
            timestamp = item['values'][0]
            
            if 'memory' in self.components:
                memory = self.components['memory']
                entries = memory.get_recent_entries(100)
                
                for entry in entries:
                    if entry.get('timestamp', '')[:19] == timestamp:
                        details = f"Time: {entry.get('timestamp', '')}\n"
                        details += f"Command: {entry.get('command', '')}\n"
                        details += f"Agent: {entry.get('agent', '')}\n"
                        details += f"Success: {entry.get('success', '')}\n"
                        details += f"Result: {entry.get('result', '')}\n"
                        
                        self.memory_details.delete(1.0, tk.END)
                        self.memory_details.insert(1.0, details)
                        break
                        
        except Exception as e:
            logger.error(f"Failed to load memory details: {e}")
    
    def refresh_status(self):
        """Refresh system status"""
        try:
            # System info
            system_info = "IGED System Status\n"
            system_info += "=" * 50 + "\n"
            
            if 'voice' in self.components:
                voice_status = self.components['voice'].get_status()
                system_info += f"Voice Pipeline: {'Active' if voice_status['is_listening'] else 'Inactive'}\n"
                system_info += f"Whisper Model: {'Loaded' if voice_status['whisper_loaded'] else 'Not Loaded'}\n"
            
            if 'orchestrator' in self.components:
                orch_status = self.components['orchestrator'].get_system_status()
                system_info += f"Active Agents: {orch_status['total_agents']}\n"
                system_info += f"Active Plugins: {orch_status['total_plugins']}\n"
            
            self.system_info.delete(1.0, tk.END)
            self.system_info.insert(1.0, system_info)
            
            # Agents info
            agents_info = "Agent Status\n"
            agents_info += "=" * 30 + "\n"
            
            if 'orchestrator' in self.components:
                orch_status = self.components['orchestrator'].get_system_status()
                for agent_name, status in orch_status['agents'].items():
                    agents_info += f"{agent_name}: {status.get('status', 'unknown')}\n"
            
            self.agents_info.delete(1.0, tk.END)
            self.agents_info.insert(1.0, agents_info)
            
        except Exception as e:
            logger.error(f"Failed to refresh status: {e}")
    
    def clear_all_memory(self):
        """Clear all memory entries"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all memory?"):
            try:
                if 'memory' in self.components:
                    self.components['memory'].clear_memory()
                    self.load_memory()
                    self.log_output("🧹 All memory cleared")
            except Exception as e:
                self.log_output(f"❌ Failed to clear memory: {e}")
    
    def export_memory(self):
        """Export memory to file"""
        try:
            if 'memory' in self.components:
                memory = self.components['memory']
                filename = f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if memory.export_memory(filename):
                    self.log_output(f"📤 Memory exported to {filename}")
                else:
                    self.log_output("❌ Failed to export memory")
        except Exception as e:
            self.log_output(f"❌ Export error: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.root.destroy()
    
    def run(self):
        """Start the GUI"""
        try:
            self.log_output("🚀 IGED GUI started")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"GUI error: {e}") 