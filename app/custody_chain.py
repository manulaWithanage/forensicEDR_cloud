"""SHA-256 hash chain manager for evidence custody"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase


class CustodyChainManager:
    """Manages blockchain-style custody chain with SHA-256 hashing"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.evidence_custody_logs
    
    def generate_entry_hash(self, entry: Dict[str, Any]) -> str:
        """
        Generate SHA-256 hash of custody entry
        
        Args:
            entry: Custody log entry dict
            
        Returns:
            str: SHA-256 hash (64 hex characters)
        """
        # Create a copy without the entry_hash and _id fields
        entry_for_hash = dict(entry)
        entry_for_hash.pop('entry_hash', None)
        entry_for_hash.pop('_id', None)
        entry_for_hash.pop('created_at', None)
        entry_for_hash.pop('verified', None)
        
        # Convert datetime objects to ISO strings for deterministic hashing
        if 'timestamp' in entry_for_hash and isinstance(entry_for_hash['timestamp'], datetime):
            entry_for_hash['timestamp'] = entry_for_hash['timestamp'].isoformat()
        
        # Sort keys for deterministic JSON
        entry_json = json.dumps(entry_for_hash, sort_keys=True)
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(entry_json.encode('utf-8'))
        return hash_obj.hexdigest()
    
    async def get_last_hash(self, event_id: Optional[str] = None) -> str:
        """
        Get the hash of the last custody entry
        
        Args:
            event_id: Optional event ID to filter by
            
        Returns:
            str: Hash of last entry, or "GENESIS" if no entries exist
        """
        query = {}
        if event_id:
            query['event_id'] = event_id
        
        last_entry = await self.collection.find_one(
            query,
            sort=[('timestamp', -1)]
        )
        
        if last_entry:
            return last_entry['entry_hash']
        return "GENESIS"
    
    async def add_custody_entry(
        self,
        event_id: str,
        action: str,
        actor: str,
        location: str,
        details: Dict[str, Any],
        actor_type: str = "AUTOMATED_SYSTEM",
        actor_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add new custody log entry with hash chain linkage
        
        Args:
            event_id: Event identifier
            action: Custody action type
            actor: Who performed the action
            location: Where action occurred
            details: Additional details about the action
            actor_type: Type of actor (AUTOMATED_SYSTEM, HUMAN_OPERATOR, etc.)
            actor_details: Optional additional actor information
            
        Returns:
            dict: Created custody entry
        """
        timestamp = datetime.utcnow()
        previous_hash = await self.get_last_hash(event_id)
        
        # Generate unique entry ID
        entry_id = f"custody_{timestamp.strftime('%Y%m%d%H%M%S%f')}"
        
        entry = {
            'entry_id': entry_id,
            'timestamp': timestamp,
            'event_id': event_id,
            'action': action,
            'actor': actor,
            'actor_type': actor_type,
            'location': location,
            'details': details,
            'previous_hash': previous_hash,
            'entry_hash': None,  # Will be computed
            'hash_algorithm': 'SHA-256',
            'verified': True,
            'created_at': timestamp
        }
        
        if actor_details:
            entry['actor_details'] = actor_details
        
        # Compute hash
        entry['entry_hash'] = self.generate_entry_hash(entry)
        
        # Insert into database
        await self.collection.insert_one(entry)
        
        return entry
    
    async def verify_chain(self, event_id: str) -> Dict[str, Any]:
        """
        Verify integrity of complete custody chain for an event
        
        Args:
            event_id: Event identifier
            
        Returns:
            dict: Verification result with status and details
        """
        # Get all logs for this event, sorted by timestamp
        cursor = self.collection.find({'event_id': event_id}).sort('timestamp', 1)
        logs = await cursor.to_list(length=None)
        
        if not logs:
            return {
                'valid': False,
                'error': 'No custody logs found for this event',
                'chain_length': 0
            }
        
        for i, entry in enumerate(logs):
            # Check first entry links to GENESIS
            if i == 0:
                if entry['previous_hash'] != "GENESIS":
                    return {
                        'valid': False,
                        'error': 'First entry must link to GENESIS',
                        'entry_id': entry['entry_id'],
                        'chain_length': len(logs)
                    }
            else:
                # Check hash linkage to previous entry
                prev_entry = logs[i - 1]
                if entry['previous_hash'] != prev_entry['entry_hash']:
                    return {
                        'valid': False,
                        'error': f'Hash chain broken at entry {i}: previous_hash mismatch',
                        'entry_id': entry['entry_id'],
                        'expected': prev_entry['entry_hash'],
                        'found': entry['previous_hash'],
                        'chain_length': len(logs)
                    }
            
            # Verify hash of current entry
            computed_hash = self.generate_entry_hash(entry)
            if computed_hash != entry['entry_hash']:
                return {
                    'valid': False,
                    'error': f'Hash mismatch at entry {i}: entry has been tampered',
                    'entry_id': entry['entry_id'],
                    'expected': computed_hash,
                    'found': entry['entry_hash'],
                    'chain_length': len(logs)
                }
        
        return {
            'valid': True,
            'chain_length': len(logs),
            'message': 'Chain integrity verified successfully'
        }
    
    async def get_custody_chain(self, event_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve complete custody chain for an event
        
        Args:
            event_id: Event identifier
            
        Returns:
            list: All custody log entries sorted by timestamp
        """
        cursor = self.collection.find({'event_id': event_id}).sort('timestamp', 1)
        return await cursor.to_list(length=None)
