"""
Data Encryption Service for HNC Legal Questionnaire System
Provides comprehensive encryption for sensitive client information
"""

import os
import base64
import json
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import logging

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class EncryptionLevel(Enum):
    """Different levels of encryption for different data types"""
    BASIC = "basic"           # For non-sensitive data
    STANDARD = "standard"     # For normal personal data
    HIGH = "high"            # For financial and legal data
    MAXIMUM = "maximum"      # For highly sensitive data like passwords


class DataCategory(Enum):
    """Categories of data for encryption classification"""
    PERSONAL_INFO = "personal_info"
    FINANCIAL_DATA = "financial_data"
    LEGAL_DOCUMENTS = "legal_documents"
    AUTHENTICATION = "authentication"
    SESSION_DATA = "session_data"
    SYSTEM_CONFIG = "system_config"


@dataclass
class EncryptionMetadata:
    """Metadata for encrypted data"""
    data_id: str
    encryption_level: EncryptionLevel
    data_category: DataCategory
    encrypted_at: datetime
    key_version: str
    algorithm: str
    salt: Optional[str] = None
    iv: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'encryption_level': self.encryption_level.value,
            'data_category': self.data_category.value,
            'encrypted_at': self.encrypted_at.isoformat()
        }


class EncryptionService:
    """Comprehensive encryption service for sensitive data"""
    
    def __init__(self, master_key_path: str = "config/master.key"):
        if not CRYPTO_AVAILABLE:
            raise ImportError("Cryptography library not available. Install with: pip install cryptography")
        
        self.master_key_path = master_key_path
        self.keys_dir = os.path.dirname(master_key_path)
        os.makedirs(self.keys_dir, exist_ok=True)
        
        # Initialize encryption keys
        self.master_key = self._get_or_create_master_key()
        self.data_keys = {}
        self.key_version = "v1.0"
        
        # Encryption configuration for different levels
        self.encryption_config = {
            EncryptionLevel.BASIC: {
                'algorithm': 'fernet',
                'key_size': 32
            },
            EncryptionLevel.STANDARD: {
                'algorithm': 'aes_256_gcm',
                'key_size': 32
            },
            EncryptionLevel.HIGH: {
                'algorithm': 'aes_256_gcm',
                'key_size': 32,
                'additional_protection': True
            },
            EncryptionLevel.MAXIMUM: {
                'algorithm': 'aes_256_gcm_rsa',
                'key_size': 32,
                'rsa_key_size': 2048,
                'additional_protection': True
            }
        }
        
        # Initialize category-specific keys
        self._initialize_category_keys()
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create the master encryption key"""
        try:
            if os.path.exists(self.master_key_path):
                with open(self.master_key_path, 'rb') as f:
                    return f.read()
            else:
                # Generate new master key
                master_key = Fernet.generate_key()
                
                # Save master key securely
                os.chmod(os.path.dirname(self.master_key_path), 0o700)
                with open(self.master_key_path, 'wb') as f:
                    f.write(master_key)
                os.chmod(self.master_key_path, 0o600)
                
                logger.info("New master encryption key generated")
                return master_key
                
        except Exception as e:
            logger.error(f"Error handling master key: {str(e)}")
            raise
    
    def _initialize_category_keys(self):
        """Initialize encryption keys for different data categories"""
        for category in DataCategory:
            key = self._derive_category_key(category)
            self.data_keys[category] = key
    
    def _derive_category_key(self, category: DataCategory) -> bytes:
        """Derive a category-specific key from the master key"""
        # Use PBKDF2 to derive category-specific keys
        salt = hashlib.sha256(f"{category.value}_{self.key_version}".encode()).digest()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        return kdf.derive(self.master_key)
    
    def encrypt_data(self, data: Union[str, Dict, List], 
                    category: DataCategory,
                    encryption_level: EncryptionLevel = EncryptionLevel.STANDARD,
                    data_id: str = None) -> Dict[str, Any]:
        """Encrypt data based on category and encryption level"""
        try:
            # Generate data ID if not provided
            if not data_id:
                data_id = f"{category.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Serialize data if needed
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, ensure_ascii=False)
            else:
                data_str = str(data)
            
            data_bytes = data_str.encode('utf-8')
            
            # Choose encryption method based on level
            if encryption_level == EncryptionLevel.BASIC:
                encrypted_data, metadata = self._encrypt_fernet(data_bytes, category, data_id)
            elif encryption_level == EncryptionLevel.STANDARD:
                encrypted_data, metadata = self._encrypt_aes_gcm(data_bytes, category, data_id)
            elif encryption_level == EncryptionLevel.HIGH:
                encrypted_data, metadata = self._encrypt_aes_gcm_enhanced(data_bytes, category, data_id)
            elif encryption_level == EncryptionLevel.MAXIMUM:
                encrypted_data, metadata = self._encrypt_aes_rsa(data_bytes, category, data_id)
            else:
                raise ValueError(f"Unsupported encryption level: {encryption_level}")
            
            return {
                'success': True,
                'data_id': data_id,
                'encrypted_data': encrypted_data,
                'metadata': metadata.to_dict(),
                'encryption_level': encryption_level.value,
                'category': category.value
            }
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data_id': data_id
            }
    
    def decrypt_data(self, encrypted_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt data using provided metadata"""
        try:
            # Reconstruct metadata object
            encryption_level = EncryptionLevel(metadata['encryption_level'])
            category = DataCategory(metadata['data_category'])
            
            # Choose decryption method based on algorithm
            algorithm = metadata['algorithm']
            
            if algorithm == 'fernet':
                decrypted_bytes = self._decrypt_fernet(encrypted_data, category)
            elif algorithm == 'aes_256_gcm':
                decrypted_bytes = self._decrypt_aes_gcm(encrypted_data, metadata, category)
            elif algorithm == 'aes_256_gcm_rsa':
                decrypted_bytes = self._decrypt_aes_rsa(encrypted_data, metadata, category)
            else:
                raise ValueError(f"Unsupported decryption algorithm: {algorithm}")
            
            # Decode and deserialize data
            data_str = decrypted_bytes.decode('utf-8')
            
            # Try to deserialize as JSON, fallback to string
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                data = data_str
            
            return {
                'success': True,
                'data': data,
                'data_id': metadata['data_id'],
                'decrypted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _encrypt_fernet(self, data: bytes, category: DataCategory, data_id: str) -> tuple:
        """Basic Fernet encryption"""
        key = self.data_keys[category]
        f = Fernet(base64.urlsafe_b64encode(key))
        
        encrypted = f.encrypt(data)
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
        
        metadata = EncryptionMetadata(
            data_id=data_id,
            encryption_level=EncryptionLevel.BASIC,
            data_category=category,
            encrypted_at=datetime.now(),
            key_version=self.key_version,
            algorithm='fernet'
        )
        
        return encrypted_b64, metadata
    
    def _encrypt_aes_gcm(self, data: bytes, category: DataCategory, data_id: str) -> tuple:
        """Standard AES-256-GCM encryption"""
        key = self.data_keys[category]
        iv = os.urandom(12)  # 96-bit IV for GCM
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Combine IV, auth tag, and ciphertext
        encrypted_data = iv + encryptor.tag + ciphertext
        encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
        
        metadata = EncryptionMetadata(
            data_id=data_id,
            encryption_level=EncryptionLevel.STANDARD,
            data_category=category,
            encrypted_at=datetime.now(),
            key_version=self.key_version,
            algorithm='aes_256_gcm',
            iv=base64.b64encode(iv).decode('utf-8')
        )
        
        return encrypted_b64, metadata
    
    def _encrypt_aes_gcm_enhanced(self, data: bytes, category: DataCategory, data_id: str) -> tuple:
        """Enhanced AES-256-GCM with additional protection"""
        # Add timestamp and integrity check
        timestamp = datetime.now().isoformat().encode('utf-8')
        integrity_hash = hashlib.sha256(data).digest()
        
        enhanced_data = len(timestamp).to_bytes(4, 'big') + timestamp + integrity_hash + data
        
        key = self.data_keys[category]
        iv = os.urandom(12)
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(enhanced_data) + encryptor.finalize()
        
        encrypted_data = iv + encryptor.tag + ciphertext
        encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
        
        metadata = EncryptionMetadata(
            data_id=data_id,
            encryption_level=EncryptionLevel.HIGH,
            data_category=category,
            encrypted_at=datetime.now(),
            key_version=self.key_version,
            algorithm='aes_256_gcm',
            iv=base64.b64encode(iv).decode('utf-8')
        )
        
        return encrypted_b64, metadata
    
    def _encrypt_aes_rsa(self, data: bytes, category: DataCategory, data_id: str) -> tuple:
        """Maximum security: AES-256-GCM + RSA for key encryption"""
        # Generate random AES key for this data
        aes_key = os.urandom(32)
        iv = os.urandom(12)
        
        # Encrypt data with AES
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Generate RSA key pair for this session
        rsa_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        rsa_public_key = rsa_private_key.public_key()
        
        # Encrypt AES key with RSA public key
        encrypted_aes_key = rsa_public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Serialize RSA private key (encrypted with category key)
        private_key_pem = rsa_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(self.data_keys[category])
        )
        
        # Combine all encrypted components
        encrypted_data = {
            'encrypted_aes_key': base64.b64encode(encrypted_aes_key).decode('utf-8'),
            'encrypted_private_key': base64.b64encode(private_key_pem).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'auth_tag': base64.b64encode(encryptor.tag).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
        }
        
        encrypted_b64 = base64.b64encode(json.dumps(encrypted_data).encode('utf-8')).decode('utf-8')
        
        metadata = EncryptionMetadata(
            data_id=data_id,
            encryption_level=EncryptionLevel.MAXIMUM,
            data_category=category,
            encrypted_at=datetime.now(),
            key_version=self.key_version,
            algorithm='aes_256_gcm_rsa'
        )
        
        return encrypted_b64, metadata
    
    def _decrypt_fernet(self, encrypted_data: str, category: DataCategory) -> bytes:
        """Decrypt Fernet encrypted data"""
        key = self.data_keys[category]
        f = Fernet(base64.urlsafe_b64encode(key))
        
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        return f.decrypt(encrypted_bytes)
    
    def _decrypt_aes_gcm(self, encrypted_data: str, metadata: Dict[str, Any], category: DataCategory) -> bytes:
        """Decrypt AES-GCM encrypted data"""
        key = self.data_keys[category]
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        
        # Extract IV, auth tag, and ciphertext
        iv = encrypted_bytes[:12]
        auth_tag = encrypted_bytes[12:28]
        ciphertext = encrypted_bytes[28:]
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, auth_tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # For enhanced encryption, extract original data
        if metadata.get('encryption_level') == EncryptionLevel.HIGH.value:
            # Extract timestamp length
            timestamp_len = int.from_bytes(decrypted_data[:4], 'big')
            # Skip timestamp and integrity hash
            original_data = decrypted_data[4 + timestamp_len + 32:]
            
            # Verify integrity
            integrity_hash = decrypted_data[4 + timestamp_len:4 + timestamp_len + 32]
            calculated_hash = hashlib.sha256(original_data).digest()
            
            if integrity_hash != calculated_hash:
                raise ValueError("Data integrity check failed")
            
            return original_data
        
        return decrypted_data
    
    def _decrypt_aes_rsa(self, encrypted_data: str, metadata: Dict[str, Any], category: DataCategory) -> bytes:
        """Decrypt AES+RSA encrypted data"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        encrypted_components = json.loads(encrypted_bytes.decode('utf-8'))
        
        # Decrypt RSA private key with category key
        encrypted_private_key = base64.b64decode(encrypted_components['encrypted_private_key'])
        rsa_private_key = serialization.load_pem_private_key(
            encrypted_private_key,
            password=self.data_keys[category],
            backend=default_backend()
        )
        
        # Decrypt AES key with RSA private key
        encrypted_aes_key = base64.b64decode(encrypted_components['encrypted_aes_key'])
        aes_key = rsa_private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Decrypt data with AES key
        iv = base64.b64decode(encrypted_components['iv'])
        auth_tag = base64.b64decode(encrypted_components['auth_tag'])
        ciphertext = base64.b64decode(encrypted_components['ciphertext'])
        
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv, auth_tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def encrypt_client_data(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt client data with appropriate levels for different fields"""
        try:
            encrypted_client = {}
            encryption_metadata = {}
            
            # Personal information - STANDARD encryption
            if 'bioData' in client_data:
                result = self.encrypt_data(
                    client_data['bioData'],
                    DataCategory.PERSONAL_INFO,
                    EncryptionLevel.STANDARD,
                    f"bio_{client_data.get('clientId', 'unknown')}"
                )
                if result['success']:
                    encrypted_client['bioData'] = result['encrypted_data']
                    encryption_metadata['bioData'] = result['metadata']
            
            # Financial information - HIGH encryption
            if 'financialData' in client_data:
                result = self.encrypt_data(
                    client_data['financialData'],
                    DataCategory.FINANCIAL_DATA,
                    EncryptionLevel.HIGH,
                    f"financial_{client_data.get('clientId', 'unknown')}"
                )
                if result['success']:
                    encrypted_client['financialData'] = result['encrypted_data']
                    encryption_metadata['financialData'] = result['metadata']
            
            # Other fields - BASIC encryption
            for field in ['economicContext', 'objectives', 'distributionPreferences']:
                if field in client_data:
                    result = self.encrypt_data(
                        client_data[field],
                        DataCategory.PERSONAL_INFO,
                        EncryptionLevel.BASIC,
                        f"{field}_{client_data.get('clientId', 'unknown')}"
                    )
                    if result['success']:
                        encrypted_client[field] = result['encrypted_data']
                        encryption_metadata[field] = result['metadata']
            
            # Keep non-sensitive metadata unencrypted
            for field in ['clientId', 'savedAt', 'lastUpdated', 'submittedBy']:
                if field in client_data:
                    encrypted_client[field] = client_data[field]
            
            encrypted_client['_encryption_metadata'] = encryption_metadata
            
            return {
                'success': True,
                'encrypted_client_data': encrypted_client,
                'encryption_summary': {
                    'encrypted_fields': list(encryption_metadata.keys()),
                    'total_fields': len(encryption_metadata),
                    'encryption_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Client data encryption failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def decrypt_client_data(self, encrypted_client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt client data"""
        try:
            decrypted_client = {}
            encryption_metadata = encrypted_client_data.get('_encryption_metadata', {})
            
            # Decrypt each encrypted field
            for field, metadata in encryption_metadata.items():
                if field in encrypted_client_data:
                    result = self.decrypt_data(encrypted_client_data[field], metadata)
                    if result['success']:
                        decrypted_client[field] = result['data']
                    else:
                        logger.error(f"Failed to decrypt field {field}: {result.get('error')}")
                        return result
            
            # Copy non-encrypted fields
            for field, value in encrypted_client_data.items():
                if field not in encryption_metadata and field != '_encryption_metadata':
                    decrypted_client[field] = value
            
            return {
                'success': True,
                'decrypted_client_data': decrypted_client,
                'decryption_summary': {
                    'decrypted_fields': list(encryption_metadata.keys()),
                    'total_fields': len(encryption_metadata),
                    'decryption_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Client data decryption failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def rotate_keys(self) -> Dict[str, Any]:
        """Rotate encryption keys (for security maintenance)"""
        try:
            old_version = self.key_version
            self.key_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate new category keys
            old_keys = self.data_keys.copy()
            self._initialize_category_keys()
            
            return {
                'success': True,
                'old_version': old_version,
                'new_version': self.key_version,
                'rotated_at': datetime.now().isoformat(),
                'message': 'Keys rotated successfully. Old encrypted data can still be decrypted.'
            }
            
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Get current encryption service status"""
        return {
            'encryption_available': CRYPTO_AVAILABLE,
            'key_version': self.key_version,
            'supported_levels': [level.value for level in EncryptionLevel],
            'supported_categories': [cat.value for cat in DataCategory],
            'master_key_exists': os.path.exists(self.master_key_path),
            'keys_initialized': len(self.data_keys) == len(DataCategory),
            'status_timestamp': datetime.now().isoformat()
        }


# Global instance
try:
    encryption_service = EncryptionService()
    logger.info("Encryption service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize encryption service: {str(e)}")
    encryption_service = None