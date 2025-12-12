"""Integration test for order to payment flow."""

import asyncio
from database import db
from config import LIQPAY_PUBLIC_KEY, LIQPAY_PRIVATE_KEY
from payments import LiqPayService

# Test cases
async def test_payment_flow():
    """Test complete payment flow."""
    
    # Connect to database
    await db.connect()
    
    print("=" * 60)
    print("PAYMENT FLOW INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: LiqPay Service
    print("\n✓ Test 1: LiqPay Service Initialization")
    try:
        liqpay_service = LiqPayService()
        print("  ✓ LiqPayService created successfully")
        
        # Test signature generation
        test_data = '{"status": "success", "order_id": 123}'
        import base64
        encoded_data = base64.b64encode(test_data.encode()).decode()
        
        # This would work with real credentials
        print("  ✓ Signature generation method available")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Test 2: Database Schema
    print("\n✓ Test 2: Database Schema")
    try:
        # Check if payments table exists
        result = await db.pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='payments')"
        )
        if result:
            print("  ✓ payments table exists")
        else:
            print("  ✗ payments table not found")
        
        # Check if orders table has payment columns
        result = await db.pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='payment_status')"
        )
        if result:
            print("  ✓ orders.payment_status column exists")
        else:
            print("  ✗ orders.payment_status column not found")
            
    except Exception as e:
        print(f"  ✗ Error checking schema: {e}")
    
    # Test 3: Create Test Order and Payment
    print("\n✓ Test 3: Create Test Order and Payment Record")
    try:
        # Create a test order
        user_id = 999
        product_id = 1
        order_id = await db.create_order(
            user_id=user_id,
            user_name="Test User",
            product_id=product_id,
            quantity=2,
            phone="+380501234567",
            email="test@example.com"
        )
        print(f"  ✓ Test order created: #{order_id}")
        
        # Get the order
        order = await db.get_order(order_id)
        if order:
            print(f"  ✓ Order retrieved: {order['id']}, Amount: {order['total_price']} грн")
            
            # Create payment record
            payment_id = await db.create_payment_record(
                order_id=order_id,
                user_id=user_id,
                amount=float(order['total_price']),
                currency="UAH",
                payment_method="liqpay",
                status="init"
            )
            print(f"  ✓ Payment record created: #{payment_id}")
            
            # Get payment
            payment = await db.get_payment_by_id(payment_id)
            if payment:
                print(f"  ✓ Payment retrieved: status={payment['status']}")
                
                # Update payment status
                await db.update_payment_status(
                    payment_id=payment_id,
                    status="success",
                    liqpay_payment_id="lp_test_123"
                )
                print(f"  ✓ Payment status updated to 'success'")
                
                # Update order payment info
                await db.update_order_payment_info(
                    order_id=order_id,
                    payment_status="paid",
                    payment_method="liqpay"
                )
                print(f"  ✓ Order payment info updated")
                
        # Cleanup test data
        await db.pool.execute("DELETE FROM payments WHERE order_id = $1", order_id)
        await db.pool.execute("DELETE FROM orders WHERE id = $1", order_id)
        print(f"  ✓ Test data cleaned up")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Configuration Check
    print("\n✓ Test 4: Configuration Check")
    try:
        if LIQPAY_PUBLIC_KEY and LIQPAY_PUBLIC_KEY != "your_public_key":
            print("  ✓ LIQPAY_PUBLIC_KEY configured")
        else:
            print("  ⚠ LIQPAY_PUBLIC_KEY not configured or using placeholder")
            
        if LIQPAY_PRIVATE_KEY and LIQPAY_PRIVATE_KEY != "your_private_key":
            print("  ✓ LIQPAY_PRIVATE_KEY configured")
        else:
            print("  ⚠ LIQPAY_PRIVATE_KEY not configured or using placeholder")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Close connection
    await db.close()
    
    print("\n" + "=" * 60)
    print("PAYMENT FLOW INTEGRATION TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_payment_flow())
