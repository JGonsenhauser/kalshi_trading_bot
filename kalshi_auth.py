"""
Kalshi Authentication Module
Handles cryptographic key-based authentication for Kalshi API
Uses RSA-PSS signing for request authentication
"""
import time
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class KalshiAuth:
    """Handle Kalshi API authentication with private key signing"""
    
    def __init__(self, api_key: str, private_key_path: str):
        self.api_key = api_key
        self.private_key_path = Path(private_key_path)
        self.private_key = None
        self._load_private_key()
    
    def _load_private_key(self):
        """Load private key from PEM file"""
        try:
            if not self.private_key_path.exists():
                raise FileNotFoundError(f"Private key file not found: {self.private_key_path}")
            
            with open(self.private_key_path, "rb") as key_file:
                self.private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,  # Add password parameter if key is encrypted
                    backend=default_backend()
                )
            
            logger.info(f"✅ Private key loaded from {self.private_key_path}")
        
        except FileNotFoundError as e:
            logger.error(f"❌ Private key file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load private key: {e}")
            raise
    
    def _sign_pss_text(self, text: str) -> str:
        """Sign text with RSA-PSS and return base64 signature"""
        if not self.private_key:
            raise ValueError("Private key not loaded")
        
        message = text.encode("utf-8")
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")
    
    def get_auth_headers(self, method: str, path: str) -> dict:
        """
        Get authentication headers for Kalshi API request
        The signature is based on: timestamp + method + path (no query params)
        """
        if not self.private_key:
            raise ValueError("Private key not loaded")
        
        # Use milliseconds timestamp
        timestamp_ms = str(int(time.time() * 1000))
        path_without_query = path.split("?")[0]
        message = f"{timestamp_ms}{method.upper()}{path_without_query}"
        signature = self._sign_pss_text(message)
        
        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
            "Content-Type": "application/json",
        }


def load_private_key_from_file(file_path: str):
    """
    Standalone helper to load private key from PEM file
    For debugging or manual testing
    """
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key
