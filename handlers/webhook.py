"""Webhook handlers for payment callbacks."""

from aiogram import Router, F, html
from aiogram.types import Message
from aiohttp import web
import json
import logging

from database import db
from payments import LiqPayService
from config import LIQPAY_CALLBACK_URL
from logger_config import get_logger

logger = get_logger("aiogram.handlers.webhook")

# Note: This router is for documentation only.
# The actual webhook is registered in bot.py using aiohttp app


async def handle_liqpay_webhook(request: web.Request) -> web.Response:
    """Handle LiqPay webhook callback."""
    try:
        # Get POST data
        post_data = await request.post()
        
        data = post_data.get('data')
        signature = post_data.get('signature')
        
        if not data or not signature:
            logger.warning("Invalid webhook request - missing data or signature")
            return web.Response(status=400, text="Invalid request")
        
        # Verify signature
        liqpay_service = LiqPayService()
        if not liqpay_service.verify_callback(data, signature):
            logger.warning(f"Invalid signature for webhook data: {data}")
            return web.Response(status=401, text="Invalid signature")
        
        # Decode the callback data
        import base64
        decoded_data = json.loads(base64.b64decode(data).decode('utf-8'))
        
        logger.info(f"Valid LiqPay webhook received: {decoded_data}")
        
        # Extract payment information
        status = decoded_data.get('status')
        order_id = decoded_data.get('order_id')
        liqpay_payment_id = decoded_data.get('payment_id')
        amount = decoded_data.get('amount')
        currency = decoded_data.get('currency')
        
        if not order_id:
            logger.error("Webhook data missing order_id")
            return web.Response(status=400, text="Missing order_id")
        
        # Get payment record
        payment = await db.get_payment_by_order(order_id)
        
        if not payment:
            logger.warning(f"No payment record found for order_id: {order_id}")
            # Create one if it doesn't exist (failsafe)
            payment_id = await db.create_payment_record(
                order_id=order_id,
                user_id=None,  # Will be retrieved from order
                amount=float(amount),
                currency=currency,
                payment_method="liqpay",
                status=status
            )
            logger.info(f"Created payment record #{payment_id} for order #{order_id}")
        else:
            # Update existing payment
            await db.update_payment_status(
                payment_id=payment['id'],
                status=status,
                liqpay_payment_id=liqpay_payment_id
            )
            logger.info(f"Updated payment #{payment['id']} status to {status}")
        
        # Handle different payment statuses
        if status == "success":
            # Update order status to paid
            order = await db.get_order(order_id)
            if order:
                await db.update_order_payment_info(
                    order_id=order_id,
                    payment_status="paid",
                    payment_method="liqpay"
                )
                logger.info(f"Order #{order_id} marked as paid")
                
                # TODO: Send confirmation message to user
                # This would require storing user_id in payment record
                # or retrieving it from order
        
        elif status == "failure":
            logger.warning(f"Payment failed for order #{order_id}")
            # Update order status to failed
            await db.update_order_payment_info(
                order_id=order_id,
                payment_status="failed",
                payment_method="liqpay"
            )
            # TODO: Notify user about failed payment
        
        elif status in ["init", "processing"]:
            logger.info(f"Payment processing for order #{order_id}, status: {status}")
        
        # Return 200 OK to acknowledge receipt
        return web.Response(status=200, text="OK")
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {e}", exc_info=True)
        return web.Response(status=400, text="Invalid JSON")
    
    except Exception as e:
        logger.error(f"Error handling LiqPay webhook: {e}", exc_info=True)
        return web.Response(status=500, text="Internal server error")


async def webhook_test(request: web.Request) -> web.Response:
    """Test webhook configuration - admin only."""
    try:
        # Simple test endpoint
        return web.json_response({
            "status": "ok",
            "message": "Webhook endpoint is working",
            "callback_url": LIQPAY_CALLBACK_URL
        })
    except Exception as e:
        logger.error(f"Error in webhook_test: {e}", exc_info=True)
        return web.json_response(
            {"error": str(e)},
            status=500
        )
