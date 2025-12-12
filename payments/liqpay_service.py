"""LiqPay payment gateway integration service."""

import hashlib
import base64
import json
from typing import Optional, Dict, Any
import aiohttp

from config import (
    LIQPAY_PUBLIC_KEY,
    LIQPAY_PRIVATE_KEY,
    LIQPAY_API_URL,
    LIQPAY_CURRENCY,
    LIQPAY_CALLBACK_URL
)
from logger_config import get_logger

logger = get_logger("aiogram.payments.liqpay")


class LiqPayService:
    """Service for LiqPay payment integration."""
    
    def __init__(self):
        self.public_key = LIQPAY_PUBLIC_KEY
        self.private_key = LIQPAY_PRIVATE_KEY
        self.api_url = LIQPAY_API_URL
        self.currency = LIQPAY_CURRENCY
        self.callback_url = LIQPAY_CALLBACK_URL
    
    def _generate_signature(self, data: str) -> str:
        """Generate SHA1 signature for LiqPay request."""
        combined = self.private_key + data + self.private_key
        signature = hashlib.sha1(combined.encode()).digest()
        return base64.b64encode(signature).decode()
    
    def generate_payment_url(self, order_id: int, amount: float, 
                           user_id: int, description: str) -> Optional[str]:
        """
        Generate LiqPay payment URL for redirect-based checkout.
        
        Args:
            order_id: Order ID in database
            amount: Payment amount
            user_id: Telegram user ID
            description: Order description
        
        Returns:
            Payment URL for redirect or None if error
        """
        try:
            if not self.public_key or not self.private_key:
                logger.error("LiqPay credentials not configured")
                return None
            
            # Prepare payment data
            payment_data = {
                "public_key": self.public_key,
                "version": "3",
                "action": "pay",
                "amount": str(amount),
                "currency": self.currency,
                "description": description,
                "order_id": str(order_id),
                "server_url": self.callback_url,
                "result_url": "https://t.me/",  # Will be replaced with bot mention
                "language": "uk",
                "paytypes": "card,liqpay",  # Accept cards and LiqPay wallet
            }
            
            # Encode data to base64
            data_json = json.dumps(payment_data)
            data_encoded = base64.b64encode(data_json.encode()).decode()
            
            # Generate signature
            signature = self._generate_signature(data_encoded)
            
            # Build form data
            form_data = {
                "data": data_encoded,
                "signature": signature
            }
            
            # Return checkout URL (user will POST form to this URL)
            checkout_url = f"{self.api_url}checkout"
            
            logger.info(f"Payment URL generated - Order: {order_id}, Amount: {amount} {self.currency}")
            
            return checkout_url
        except Exception as e:
            logger.error(f"Error generating payment URL: {e}", exc_info=True)
            return None
    
    def verify_callback(self, data: str, signature: str) -> Optional[Dict[str, Any]]:
        """
        Verify LiqPay webhook callback signature and decode data.
        
        Args:
            data: Base64 encoded data from LiqPay
            signature: Signature from LiqPay
        
        Returns:
            Decoded payment data if signature valid, None otherwise
        """
        try:
            # Generate signature from received data
            expected_signature = self._generate_signature(data)
            
            # Compare signatures (constant-time comparison)
            if not self._constant_time_compare(signature, expected_signature):
                logger.warning(f"Invalid LiqPay callback signature")
                return None
            
            # Decode base64 data
            decoded_data = base64.b64decode(data).decode()
            payment_data = json.loads(decoded_data)
            
            logger.info(f"LiqPay callback verified - Order: {payment_data.get('order_id')}, "
                       f"Status: {payment_data.get('status')}")
            
            return payment_data
        except Exception as e:
            logger.error(f"Error verifying LiqPay callback: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """Compare strings in constant time to prevent timing attacks."""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    async def check_payment_status(self, liqpay_order_id: str) -> Optional[Dict[str, Any]]:
        """
        Query payment status from LiqPay API (optional - for advanced use).
        
        Note: This requires additional API calls. Webhook is the primary method.
        
        Args:
            liqpay_order_id: Order ID sent to LiqPay
        
        Returns:
            Payment status data or None if error
        """
        try:
            if not self.public_key or not self.private_key:
                return None
            
            # Prepare request data
            request_data = {
                "public_key": self.public_key,
                "version": "3",
                "action": "status",
                "order_id": liqpay_order_id
            }
            
            data_json = json.dumps(request_data)
            data_encoded = base64.b64encode(data_json.encode()).decode()
            signature = self._generate_signature(data_encoded)
            
            # Send request to LiqPay API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}request",
                    data={"data": data_encoded, "signature": signature},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Payment status checked - Order: {liqpay_order_id}")
                        return result
                    else:
                        logger.error(f"LiqPay API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error checking payment status: {e}", exc_info=True)
            return None


# Global instance
liqpay_service = LiqPayService()
