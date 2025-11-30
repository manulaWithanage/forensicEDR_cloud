"""AES-256-GCM encryption and decryption utilities"""
import json
from Crypto.Cipher import AES
from .config import settings


def decrypt_evidence(encrypted_data: bytes) -> dict:
    """
    Decrypt AES-256-GCM encrypted evidence file
    
    File format:
    - Bytes 0-11: Nonce (12 bytes)
    - Bytes 12-27: Authentication tag (16 bytes)
    - Bytes 28+: Ciphertext
    
    Args:
        encrypted_data: Raw encrypted bytes from .bin file
        
    Returns:
        dict: Decrypted crash event data
        
    Raises:
        ValueError: If decryption fails or data is invalid
    """
    try:
        # Extract components
        if len(encrypted_data) < 28:
            raise ValueError("Encrypted data too short (minimum 28 bytes required)")
        
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]
        
        # Get AES key from settings
        aes_key = settings.get_aes_key_bytes()
        
        # Decrypt
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        
        # Parse JSON
        event_data = json.loads(plaintext.decode('utf-8'))
        
        return event_data
        
    except ValueError as e:
        raise ValueError(f"Decryption failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in decrypted data: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error during decryption: {str(e)}")


def encrypt_evidence(data: dict) -> bytes:
    """
    Encrypt evidence data with AES-256-GCM
    
    Args:
        data: Dictionary to encrypt
        
    Returns:
        bytes: Encrypted data (nonce + tag + ciphertext)
    """
    try:
        # Convert to JSON
        plaintext = json.dumps(data).encode('utf-8')
        
        # Get AES key
        aes_key = settings.get_aes_key_bytes()
        
        # Create cipher
        cipher = AES.new(aes_key, AES.MODE_GCM)
        
        # Encrypt and get tag
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        
        # Combine: nonce (12) + tag (16) + ciphertext
        encrypted_data = cipher.nonce + tag + ciphertext
        
        return encrypted_data
        
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")
