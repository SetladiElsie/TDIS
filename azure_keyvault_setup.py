"""
Azure Key Vault Integration for TDIS
====================================

This module provides secure secret management using Azure Key Vault.
Use this for production deployments instead of .env files.

Setup Instructions:
------------------
1. Install dependencies:
   pip install azure-keyvault-secrets azure-identity

2. Create Azure Key Vault:
   az keyvault create --name tdis-keyvault-prod \
       --resource-group tdis-rg \
       --location southafricanorth

3. Store secrets:
   az keyvault secret set --vault-name tdis-keyvault-prod --name "SECRET-KEY" --value "your-secret"
   az keyvault secret set --vault-name tdis-keyvault-prod --name "DB-PASSWORD" --value "your-password"
   az keyvault secret set --vault-name tdis-keyvault-prod --name "MAIL-PASSWORD" --value "your-mail-pass"

4. Grant access to your app:
   az keyvault set-policy --name tdis-keyvault-prod \
       --object-id <your-app-service-principal-id> \
       --secret-permissions get list

5. Set environment variable:
   AZURE_KEY_VAULT_URL=https://tdis-keyvault-prod.vault.azure.net/
"""

import os
from functools import lru_cache
from typing import Optional


class KeyVaultClient:
    """Azure Key Vault client for retrieving secrets"""
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Initialize Key Vault client
        
        Args:
            vault_url: Azure Key Vault URL. If not provided, reads from AZURE_KEY_VAULT_URL env var
        """
        self.vault_url = vault_url or os.getenv('AZURE_KEY_VAULT_URL')
        self.client = None
        
        # Only initialize in production or when explicitly configured
        if self.vault_url and os.getenv('FLASK_ENV') == 'production':
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure Key Vault client with managed identity"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            print(f"✅ Connected to Azure Key Vault: {self.vault_url}")
        except ImportError:
            print("⚠️  Azure SDK not installed. Install with: pip install azure-keyvault-secrets azure-identity")
            self.client = None
        except Exception as e:
            print(f"❌ Failed to connect to Azure Key Vault: {str(e)}")
            self.client = None
    
    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> str:
        """
        Retrieve secret from Key Vault or fall back to environment variable
        
        Args:
            secret_name: Name of the secret (use dashes, e.g., 'SECRET-KEY')
            default: Default value if secret not found
            
        Returns:
            Secret value as string
        """
        # Try Key Vault first (production)
        if self.client:
            try:
                secret = self.client.get_secret(secret_name)
                return secret.value
            except Exception as e:
                print(f"⚠️  Failed to retrieve {secret_name} from Key Vault: {str(e)}")
        
        # Fall back to environment variable (development)
        env_name = secret_name.replace('-', '_')
        value = os.getenv(env_name, default)
        
        if value is None:
            raise ValueError(f"Secret {secret_name} not found in Key Vault or environment")
        
        return value


# Global Key Vault client instance
_kv_client = None


def get_keyvault_client() -> KeyVaultClient:
    """Get or create the global Key Vault client instance"""
    global _kv_client
    if _kv_client is None:
        _kv_client = KeyVaultClient()
    return _kv_client


def get_secret(secret_name: str, default: Optional[str] = None) -> str:
    """
    Convenience function to retrieve a secret
    
    Usage:
        from azure_keyvault_setup import get_secret
        
        SECRET_KEY = get_secret('SECRET-KEY')
        DB_PASSWORD = get_secret('DB-PASSWORD')
    
    Args:
        secret_name: Name of the secret in Key Vault (use dashes)
        default: Default value if secret not found
        
    Returns:
        Secret value as string
    """
    client = get_keyvault_client()
    return client.get_secret(secret_name, default)


# ─────────────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    """Test Key Vault connection and secret retrieval"""
    
    print("🔒 TDIS Azure Key Vault Setup Test\n")
    
    # Check environment
    env = os.getenv('FLASK_ENV', 'development')
    vault_url = os.getenv('AZURE_KEY_VAULT_URL')
    
    print(f"Environment: {env}")
    print(f"Key Vault URL: {vault_url or 'Not configured'}\n")
    
    if not vault_url:
        print("⚠️  AZURE_KEY_VAULT_URL not set. Key Vault integration disabled.")
        print("   Secrets will be read from environment variables (.env file)\n")
    
    # Test secret retrieval
    try:
        print("Testing secret retrieval:\n")
        
        # These will fall back to environment variables in development
        test_secrets = [
            ('SECRET-KEY', 'SECRET_KEY'),
            ('DB-PASSWORD', 'DATABASE_URL'),
            ('MAIL-PASSWORD', 'MAIL_PASSWORD'),
        ]
        
        for kv_name, env_name in test_secrets:
            try:
                value = get_secret(kv_name)
                masked = value[:8] + '...' if len(value) > 8 else '***'
                print(f"  ✅ {kv_name}: {masked}")
            except Exception as e:
                print(f"  ❌ {kv_name}: {str(e)}")
        
        print("\n✅ Key Vault setup test complete!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Ensure AZURE_KEY_VAULT_URL is set")
        print("  2. Verify Azure CLI is installed: az --version")
        print("  3. Login to Azure: az login")
        print("  4. Check Key Vault access policy")
        print("  5. Verify secrets exist: az keyvault secret list --vault-name <vault-name>")


# ─────────────────────────────────────────────────────────────────────────────
# Integration with config.py
# ─────────────────────────────────────────────────────────────────────────────
"""
To integrate with config.py, update your Config class:

from azure_keyvault_setup import get_secret

class Config:
    # Development: reads from .env
    # Production: reads from Azure Key Vault
    SECRET_KEY = get_secret('SECRET-KEY', 'dev-secret-key-change-in-production')
    
    # Database URL with password from Key Vault
    DB_PASSWORD = get_secret('DB-PASSWORD', None)
    if DB_PASSWORD:
        SQLALCHEMY_DATABASE_URI = f"postgresql://tdis_user:{DB_PASSWORD}@localhost:5432/tdis_db"
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/tender.db')
    
    # Email password from Key Vault
    MAIL_PASSWORD = get_secret('MAIL-PASSWORD', os.getenv('MAIL_PASSWORD'))
"""
