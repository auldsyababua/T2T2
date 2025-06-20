#!/usr/bin/env python3
"""
Wrapper for Supabase client that handles both old and new API key formats
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseClientWrapper:
    """Wrapper to handle new Supabase API key format"""

    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client: Optional[Client] = None

        logger.info("Initializing Supabase client wrapper")
        logger.info(f"URL: {url}")
        logger.info(
            f"Key type: {'New format (sb_secret_)' if key.startswith('sb_secret_') else 'Legacy JWT format'}"
        )

    def get_client(self) -> Client:
        """Get or create Supabase client with proper headers"""
        if self.client:
            return self.client

        try:
            # For new key format, we might need to set custom headers
            if self.key.startswith("sb_secret_"):
                logger.info("Using new secret key format")

                # Create custom headers
                headers = {
                    "Authorization": f"Bearer {self.key}",
                    "apikey": self.key,
                }

                # Create Supabase client with custom headers
                # Note: This approach might need adjustment based on the actual API
                self.client = create_client(
                    self.url,
                    self.key,
                    options={
                        "headers": headers,
                        "auto_refresh_token": False,
                        "persist_session": False,
                    },
                )
            else:
                # Legacy JWT format
                logger.info("Using legacy JWT key format")
                self.client = create_client(self.url, self.key)

            logger.info("✅ Supabase client created successfully")
            return self.client

        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")

            # Try alternative approach for new format
            if self.key.startswith("sb_secret_"):
                logger.info("Trying alternative initialization for new key format")

                try:
                    # Sometimes the new format needs to be passed differently
                    self.client = create_client(
                        supabase_url=self.url,
                        supabase_key=self.key,
                        options={
                            "schema": "public",
                            "auto_refresh_token": False,
                            "persist_session": False,
                        },
                    )
                    logger.info("✅ Alternative initialization successful")
                    return self.client
                except Exception as e2:
                    logger.error(f"Alternative initialization also failed: {e2}")

            raise e

    def test_connection(self) -> bool:
        """Test if the connection works"""
        try:
            client = self.get_client()

            # Try a simple operation
            result = client.table("documents").select("id").limit(1).execute()
            logger.info("✅ Connection test successful")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection test failed: {error_msg}")

            if "does not exist" in error_msg:
                logger.info("Note: Table doesn't exist yet, but connection seems OK")
                return True
            elif "Invalid API key" in error_msg:
                logger.error("API key is invalid or incompatible")
                return False
            else:
                logger.error(f"Unexpected error: {error_msg}")
                return False


# Test function
if __name__ == "__main__":
    from dotenv import load_dotenv

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load environment
    load_dotenv(".env.supabase_bot")

    # Get config
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        exit(1)

    # Test wrapper
    print("Testing Supabase client wrapper...")
    wrapper = SupabaseClientWrapper(url, key)

    if wrapper.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")

        # Additional debugging
        print("\nDebugging suggestions:")
        print("1. Try disabling JWT-based API keys in Supabase dashboard")
        print("2. Ensure you're using the 'secret' key from the new API keys section")
        print("3. Check if your Supabase project URL is correct")
