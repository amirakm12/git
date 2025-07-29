"""
Memory Engine for IGED
Handles persistent encrypted storage of commands and results
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MemoryEngine:
    def __init__(self, encryption_manager):
        self.encryption = encryption_manager
        self.memory_file = Path("memory/memory_log.json")
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_data = self.load_memory()
    
    def load_memory(self) -> List[Dict[str, Any]]:
        """Load memory from encrypted file"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = f.read()
                    if data.strip():
                        # Try to decrypt if encrypted
                        try:
                            decrypted = self.encryption.decrypt(data)
                            return json.loads(decrypted)
                        except:
                            # If decryption fails, try as plain JSON
                            return json.loads(data)
            return []
        except Exception as e:
            logger.error(f"❌ Failed to load memory: {e}")
            return []
    
    def save_memory(self):
        """Save memory to encrypted file"""
        try:
            data = json.dumps(self.memory_data, indent=2, ensure_ascii=False)
            encrypted_data = self.encryption.encrypt(data)
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            
            logger.debug("💾 Memory saved successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to save memory: {e}")
    
    def add_entry(self, command: str, result: str, agent: str = "unknown", 
                  success: bool = True, metadata: Optional[Dict] = None) -> Optional[str]:
        """Add a new memory entry"""
        try:
            entry = {
                "id": self.generate_id(),
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "result": result,
                "agent": agent,
                "success": success,
                "metadata": metadata or {}
            }
            
            self.memory_data.append(entry)
            self.save_memory()
            
            logger.info(f"📝 Added memory entry: {entry['id']}")
            return entry['id']
            
        except Exception as e:
            logger.error(f"❌ Failed to add memory entry: {e}")
            return None
    
    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory entry"""
        for entry in self.memory_data:
            if entry.get('id') == entry_id:
                return entry
        return None
    
    def search_entries(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory entries by command or result"""
        results = []
        query_lower = query.lower()
        
        for entry in reversed(self.memory_data):
            if (query_lower in entry.get('command', '').lower() or 
                query_lower in entry.get('result', '').lower()):
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memory entries"""
        return self.memory_data[-limit:] if self.memory_data else []
    
    def get_entries_by_agent(self, agent: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get entries by specific agent"""
        results = []
        for entry in reversed(self.memory_data):
            if entry.get('agent') == agent:
                results.append(entry)
                if len(results) >= limit:
                    break
        return results
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a memory entry"""
        try:
            for i, entry in enumerate(self.memory_data):
                if entry.get('id') == entry_id:
                    del self.memory_data[i]
                    self.save_memory()
                    logger.info(f"🗑️ Deleted memory entry: {entry_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete memory entry: {e}")
            return False
    
    def clear_memory(self):
        """Clear all memory entries"""
        try:
            self.memory_data = []
            self.save_memory()
            logger.info("🧹 Memory cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear memory: {e}")
    
    def export_memory(self, file_path: str) -> bool:
        """Export memory to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory_data, f, indent=2, ensure_ascii=False)
            logger.info(f"📤 Memory exported to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to export memory: {e}")
            return False
    
    def import_memory(self, file_path: str) -> bool:
        """Import memory from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            if isinstance(imported_data, list):
                self.memory_data.extend(imported_data)
                self.save_memory()
                logger.info(f"📥 Memory imported from: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to import memory: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            total_entries = len(self.memory_data)
            successful_entries = sum(1 for entry in self.memory_data if entry.get('success', False))
            failed_entries = total_entries - successful_entries
            
            agents = {}
            for entry in self.memory_data:
                agent = entry.get('agent', 'unknown')
                agents[agent] = agents.get(agent, 0) + 1
            
            return {
                "total_entries": total_entries,
                "successful_entries": successful_entries,
                "failed_entries": failed_entries,
                "success_rate": (successful_entries / total_entries * 100) if total_entries > 0 else 0,
                "agents": agents,
                "oldest_entry": self.memory_data[0]['timestamp'] if self.memory_data else None,
                "newest_entry": self.memory_data[-1]['timestamp'] if self.memory_data else None
            }
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}
    
    def generate_id(self) -> str:
        """Generate unique ID for memory entry"""
        return f"mem_{int(time.time() * 1000)}_{len(self.memory_data)}" 