#!/usr/bin/env python3
"""
Client Service for HNC Legal Questionnaire System
Handles client data operations including CRUD operations, validation, and search
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import time

logger = logging.getLogger(__name__)


class ClientService:
    """Service for managing client data operations"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.clients_dir = self.data_dir / "clients"
        self.clients_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file for quick client lookups
        self.index_file = self.data_dir / "client_index.json"
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Ensure client index file exists"""
        if not self.index_file.exists():
            self._rebuild_index()
    
    def _rebuild_index(self):
        """Rebuild the client index from existing files"""
        index = {}
        
        try:
            for client_file in self.clients_dir.glob("client_*.json"):
                try:
                    with open(client_file, 'r', encoding='utf-8') as f:
                        client_data = json.load(f)
                        client_id = client_data.get('clientId')
                        if client_id:
                            index[client_id] = {
                                "filename": client_file.name,
                                "fullName": client_data.get('bioData', {}).get('fullName', 'Unknown'),
                                "createdAt": client_data.get('savedAt', datetime.now().isoformat()),
                                "lastUpdated": client_data.get('lastUpdated', datetime.now().isoformat())
                            }
                except Exception as e:
                    logger.warning(f"Failed to index client file {client_file}: {e}")
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2)
                
            logger.info(f"Rebuilt client index with {len(index)} clients")
            
        except Exception as e:
            logger.error(f"Failed to rebuild client index: {e}")
    
    def generate_client_id(self, full_name: str) -> str:
        """Generate unique client ID"""
        unique_string = f"{full_name.lower().replace(' ', '_')}_{int(time.time())}"
        hash_obj = hashlib.md5(unique_string.encode())
        return f"client_{hash_obj.hexdigest()[:8]}"
    
    def validate_client_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate client data"""
        errors = []
        
        # Required bio data
        bio_data = data.get('bioData', {})
        if not bio_data.get('fullName', '').strip():
            errors.append("Full name is required")
        
        # Marital status validation
        if bio_data.get('maritalStatus') == 'Married':
            if not bio_data.get('spouseName', '').strip():
                errors.append("Spouse name is required for married clients")
        
        # Financial data validation
        financial_data = data.get('financialData', {})
        assets = financial_data.get('assets', [])
        if not assets:
            errors.append("At least one asset must be specified")
        
        # Objective validation
        objectives = data.get('objectives', {})
        if not objectives.get('objective', '').strip():
            errors.append("Primary objective is required")
        
        return len(errors) == 0, errors
    
    def save_client_data(self, data: Dict[str, Any], client_id: Optional[str] = None) -> Tuple[bool, str, str]:
        """Save client data to file"""
        try:
            # Validate data
            is_valid, errors = self.validate_client_data(data)
            if not is_valid:
                return False, f"Validation failed: {'; '.join(errors)}", ""
            
            # Generate client ID if not provided
            if not client_id:
                client_id = self.generate_client_id(data.get('bioData', {}).get('fullName', 'unknown'))
            
            # Prepare data with metadata
            client_data = {
                **data,
                'clientId': client_id,
                'savedAt': datetime.now().isoformat(),
                'lastUpdated': datetime.now().isoformat()
            }
            
            # Save to file
            filename = f"client_{client_id}_{int(time.time())}.json"
            file_path = self.clients_dir / filename
            
            # Atomic write
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(client_data, f, ensure_ascii=False, indent=2)
            
            temp_path.rename(file_path)
            
            # Update index
            self._update_index(client_id, filename, client_data)
            
            logger.info(f"Client data saved: {client_id}")
            return True, f"Client saved successfully: {client_id}", str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save client data: {e}")
            return False, f"Failed to save client: {str(e)}", ""
    
    def _update_index(self, client_id: str, filename: str, client_data: Dict[str, Any]):
        """Update client index"""
        try:
            # Load existing index
            index = {}
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            
            # Update index entry
            index[client_id] = {
                "filename": filename,
                "fullName": client_data.get('bioData', {}).get('fullName', 'Unknown'),
                "createdAt": client_data.get('savedAt'),
                "lastUpdated": client_data.get('lastUpdated')
            }
            
            # Save updated index
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update client index: {e}")
    
    def load_client_data(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Load client data by ID"""
        try:
            # Check index first
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                    
                client_info = index.get(client_id)
                if client_info:
                    file_path = self.clients_dir / client_info['filename']
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
            
            # Fallback: search all client files
            for client_file in self.clients_dir.glob("client_*.json"):
                try:
                    with open(client_file, 'r', encoding='utf-8') as f:
                        client_data = json.load(f)
                        if client_data.get('clientId') == client_id:
                            return client_data
                except Exception as e:
                    logger.warning(f"Failed to read client file {client_file}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load client {client_id}: {e}")
            return None
    
    def get_all_clients(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all clients with pagination"""
        try:
            clients = []
            
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                # Sort by last updated (most recent first)
                sorted_clients = sorted(
                    index.items(),
                    key=lambda x: x[1].get('lastUpdated', ''),
                    reverse=True
                )
                
                for client_id, client_info in sorted_clients[:limit]:
                    client_data = self.load_client_data(client_id)
                    if client_data:
                        clients.append(client_data)
            
            return clients
            
        except Exception as e:
            logger.error(f"Failed to get all clients: {e}")
            return []
    
    def search_clients(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search clients by name, ID, or other criteria"""
        try:
            results = []
            query_lower = query.lower()
            
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                matching_clients = []
                for client_id, client_info in index.items():
                    full_name = client_info.get('fullName', '').lower()
                    
                    if (query_lower in full_name or 
                        query_lower in client_id.lower()):
                        matching_clients.append(client_id)
                
                # Load full data for matches
                for client_id in matching_clients[:limit]:
                    client_data = self.load_client_data(client_id)
                    if client_data:
                        results.append(client_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search clients: {e}")
            return []
    
    def delete_client(self, client_id: str) -> Tuple[bool, str]:
        """Delete client data"""
        try:
            # Find and delete file
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                client_info = index.get(client_id)
                if client_info:
                    file_path = self.clients_dir / client_info['filename']
                    if file_path.exists():
                        file_path.unlink()
                    
                    # Remove from index
                    del index[client_id]
                    with open(self.index_file, 'w', encoding='utf-8') as f:
                        json.dump(index, f, indent=2)
                    
                    logger.info(f"Client deleted: {client_id}")
                    return True, f"Client {client_id} deleted successfully"
                else:
                    return False, f"Client {client_id} not found"
            
            return False, "Client index not available"
            
        except Exception as e:
            logger.error(f"Failed to delete client {client_id}: {e}")
            return False, f"Failed to delete client: {str(e)}"
    
    def get_client_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        try:
            stats = {
                "total_clients": 0,
                "clients_by_status": {},
                "clients_by_objective": {},
                "recent_clients": 0
            }
            
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                stats["total_clients"] = len(index)
                
                # Recent clients (last 30 days)
                from datetime import timedelta
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                
                for client_id in index:
                    client_data = self.load_client_data(client_id)
                    if client_data:
                        # Count by objective
                        objective = client_data.get('objectives', {}).get('objective', 'Unknown')
                        stats["clients_by_objective"][objective] = stats["clients_by_objective"].get(objective, 0) + 1
                        
                        # Count recent clients
                        created_at = client_data.get('savedAt', '')
                        if created_at > thirty_days_ago:
                            stats["recent_clients"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get client statistics: {e}")
            return {"total_clients": 0, "error": str(e)}


# Global client service instance
client_service = ClientService()


# Convenience functions for backwards compatibility
def save_client_data(data: dict, client_id: str = None) -> tuple[bool, str]:
    """Save client data (backwards compatible)"""
    success, message, _ = client_service.save_client_data(data, client_id)
    return success, client_id if success else ""


def load_client_data(client_id: str) -> dict:
    """Load client data (backwards compatible)"""
    return client_service.load_client_data(client_id) or {}


def get_all_clients() -> list:
    """Get all clients (backwards compatible)"""
    return client_service.get_all_clients()


def search_clients(query: str) -> list:
    """Search clients (backwards compatible)"""
    return client_service.search_clients(query)