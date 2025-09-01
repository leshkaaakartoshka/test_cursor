"""Telegram service for sending PDFs."""

import asyncio
from pathlib import Path
from typing import Optional

import httpx

from app.core.config import Settings


class TelegramService:
    """Service for sending PDFs via Telegram Bot API."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bot_token = settings.tg_bot_token
        self.chat_id = settings.tg_manager_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_pdf(
        self,
        file_path: str,
        caption: str,
        lead_id: str
    ) -> bool:
        """
        Send PDF file to Telegram chat.
        
        Args:
            file_path: Path to the PDF file
            caption: Caption for the message
            lead_id: Lead ID for logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Prepare the file for upload
            files = {
                'document': (
                    file_path_obj.name,
                    open(file_path, 'rb'),
                    'application/pdf'
                )
            }
            
            data = {
                'chat_id': self.chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/sendDocument",
                    data=data,
                    files=files
                )
                
                # Close the file
                files['document'][1].close()
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('ok', False)
                else:
                    print(f"Telegram API error for lead {lead_id}: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Failed to send PDF to Telegram for lead {lead_id}: {e}")
            return False
    
    async def send_message(
        self,
        message: str,
        lead_id: str
    ) -> bool:
        """
        Send a text message to Telegram chat.
        
        Args:
            message: Message text
            lead_id: Lead ID for logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('ok', False)
                else:
                    print(f"Telegram API error for lead {lead_id}: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Failed to send message to Telegram for lead {lead_id}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Telegram Bot API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_url}/getMe")
                return response.status_code == 200
        except Exception:
            return False