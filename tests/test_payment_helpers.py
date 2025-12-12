"""Comprehensive tests for payment helper functions from utils/payment_helpers.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.fsm.context import FSMContext
from datetime import datetime


# ═════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_state():
    """Create a mock FSM state."""
    state = AsyncMock(spec=FSMContext)
    return state


@pytest.fixture
def mock_callback():
    """Create a mock callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 12345
    callback.from_user.first_name = "Test"
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def valid_order_data():
    """Fixture for valid order data."""
    return {
        'id': 1,
        'user_id': 12345,
        'product_id': 1,
        'quantity': 2,
        'total_price': 1000.50,
        'phone': '+380501234567',
        'email': 'test@example.com',
        'status': 'pending',
        'payment_status': 'unpaid',
        'created_at': datetime.now()
    }


@pytest.fixture
def valid_paid_order_data(valid_order_data):
    """Fixture for a paid order."""
    order = valid_order_data.copy()
    order['payment_status'] = 'paid'
    order['status'] = 'confirmed'
    return order


# ═════════════════════════════════════════════════════════════════════════════
# TEST VALIDATE_ORDER_ID
# ═════════════════════════════════════════════════════════════════════════════

class TestValidateOrderId:
    """Tests for validate_order_id() function."""
    
    @pytest.mark.asyncio
    async def test_validate_order_id_valid(self, mock_state):
        """Test case: Valid order ID in state."""
        from utils.payment_helpers import validate_order_id
        
        mock_state.get_data = AsyncMock(return_value={'order_id': 123})
        
        order_id, is_valid = await validate_order_id(mock_state)
        
        assert is_valid is True
        assert order_id == 123
        mock_state.get_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_order_id_missing(self, mock_state):
        """Test case: Missing order ID in state."""
        from utils.payment_helpers import validate_order_id
        
        mock_state.get_data = AsyncMock(return_value={})
        
        order_id, is_valid = await validate_order_id(mock_state)
        
        assert is_valid is False
        assert order_id is None
    
    @pytest.mark.asyncio
    async def test_validate_order_id_zero(self, mock_state):
        """Test case: Invalid order ID (zero)."""
        from utils.payment_helpers import validate_order_id
        
        mock_state.get_data = AsyncMock(return_value={'order_id': 0})
        
        order_id, is_valid = await validate_order_id(mock_state)
        
        assert is_valid is False
        assert order_id is None
    
    @pytest.mark.asyncio
    async def test_validate_order_id_negative(self, mock_state):
        """Test case: Invalid order ID (negative)."""
        from utils.payment_helpers import validate_order_id
        
        mock_state.get_data = AsyncMock(return_value={'order_id': -5})
        
        order_id, is_valid = await validate_order_id(mock_state)
        
        assert is_valid is False
        assert order_id is None
    
    @pytest.mark.asyncio
    async def test_validate_order_id_not_integer(self, mock_state):
        """Test case: Invalid order ID (not integer)."""
        from utils.payment_helpers import validate_order_id
        
        mock_state.get_data = AsyncMock(return_value={'order_id': "not_an_integer"})
        
        order_id, is_valid = await validate_order_id(mock_state)
        
        assert is_valid is False
        assert order_id is None
    
    @pytest.mark.asyncio
    async def test_validate_order_id_fsm_error(self, mock_state):
        """Test case: FSM state error handling."""
        from utils.payment_helpers import validate_order_id
        
        mock_state.get_data = AsyncMock(side_effect=RuntimeError("FSM Error"))
        
        order_id, is_valid = await validate_order_id(mock_state)
        
        assert is_valid is False
        assert order_id is None


# ═════════════════════════════════════════════════════════════════════════════
# TEST GET_AND_VALIDATE_ORDER
# ═════════════════════════════════════════════════════════════════════════════

class TestGetAndValidateOrder:
    """Tests for get_and_validate_order() function."""
    
    @pytest.mark.asyncio
    async def test_get_and_validate_order_valid(self, valid_order_data):
        """Test case: Valid order owned by user."""
        from utils.payment_helpers import get_and_validate_order
        
        mock_db = AsyncMock()
        mock_db.get_order = AsyncMock(return_value=valid_order_data)
        
        with patch('utils.payment_helpers.db', mock_db):
            order_data, is_valid = await get_and_validate_order(
                order_id=1,
                user_id=12345
            )
        
        assert is_valid is True
        assert order_data == valid_order_data
        mock_db.get_order.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_and_validate_order_not_found(self):
        """Test case: Order not found."""
        from utils.payment_helpers import get_and_validate_order
        
        mock_db = AsyncMock()
        mock_db.get_order = AsyncMock(return_value=None)
        
        with patch('utils.payment_helpers.db', mock_db):
            order_data, is_valid = await get_and_validate_order(
                order_id=999,
                user_id=12345
            )
        
        assert is_valid is False
        assert order_data is None
    
    @pytest.mark.asyncio
    async def test_get_and_validate_order_different_user(self, valid_order_data):
        """Test case: Order belongs to different user."""
        from utils.payment_helpers import get_and_validate_order
        
        mock_db = AsyncMock()
        mock_db.get_order = AsyncMock(return_value=valid_order_data)
        
        with patch('utils.payment_helpers.db', mock_db):
            order_data, is_valid = await get_and_validate_order(
                order_id=1,
                user_id=99999
            )
        
        assert is_valid is False
        assert order_data is None
    
    @pytest.mark.asyncio
    async def test_get_and_validate_order_database_error(self):
        """Test case: Database error handling."""
        from utils.payment_helpers import get_and_validate_order
        
        mock_db = AsyncMock()
        mock_db.get_order = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('utils.payment_helpers.db', mock_db):
            order_data, is_valid = await get_and_validate_order(
                order_id=1,
                user_id=12345
            )
        
        assert is_valid is False
        assert order_data is None


# ═════════════════════════════════════════════════════════════════════════════
# TEST GET_ORDER_SUMMARY_TEXT
# ═════════════════════════════════════════════════════════════════════════════

class TestGetOrderSummaryText:
    """Tests for get_order_summary_text() function."""
    
    def test_get_order_summary_text_valid(self, valid_order_data):
        """Test case: Valid order data formatting."""
        from utils.payment_helpers import get_order_summary_text
        
        result = get_order_summary_text(valid_order_data)
        
        assert "#1" in result
        assert "1000.50" in result
        assert isinstance(result, str)
    
    def test_get_order_summary_text_missing_price(self):
        """Test case: Missing price data (graceful handling)."""
        from utils.payment_helpers import get_order_summary_text
        
        order_data = {
            'id': 1,
            'quantity': 2,
            'total_price': None
        }
        
        result = get_order_summary_text(order_data)
        
        assert isinstance(result, str)
        assert "❌ Помилка при форматуванні замовлення" in result
    
    def test_get_order_summary_text_invalid_types(self):
        """Test case: Invalid data types (error handling)."""
        from utils.payment_helpers import get_order_summary_text
        
        order_data = {
            'id': 'invalid',
            'quantity': 'two',
            'total_price': 'hundred'
        }
        
        result = get_order_summary_text(order_data)
        assert isinstance(result, str)


# ═════════════════════════════════════════════════════════════════════════════
# TEST HANDLE_PAYMENT_ERROR
# ═════════════════════════════════════════════════════════════════════════════

class TestHandlePaymentError:
    """Tests for handle_payment_error() function."""
    
    @pytest.mark.asyncio
    async def test_handle_payment_error_with_alert(self, mock_callback):
        """Test case: Error with alert."""
        from utils.payment_helpers import handle_payment_error
        
        error_message = "Payment processing failed"
        
        await handle_payment_error(
            callback=mock_callback,
            error_msg=error_message,
            show_alert=True
        )
        
        mock_callback.answer.assert_called_once()
        call_args = mock_callback.answer.call_args
        assert error_message in str(call_args)
    
    @pytest.mark.asyncio
    async def test_handle_payment_error_without_alert(self, mock_callback):
        """Test case: Error without alert."""
        from utils.payment_helpers import handle_payment_error
        
        error_message = "Payment processing failed"
        
        await handle_payment_error(
            callback=mock_callback,
            error_msg=error_message,
            show_alert=False
        )
        
        mock_callback.answer.assert_called_once()
        call_args = mock_callback.answer.call_args
        assert call_args[1].get('show_alert') is False
    
    @pytest.mark.asyncio
    async def test_handle_payment_error_user_logging(self, mock_callback):
        """Test case: User logging."""
        from utils.payment_helpers import handle_payment_error
        
        with patch('utils.payment_helpers.logger') as mock_logger:
            await handle_payment_error(
                callback=mock_callback,
                error_msg="Test error",
                show_alert=True
            )
            
            assert mock_logger.error.called


# ═════════════════════════════════════════════════════════════════════════════
# TEST VALIDATE_PAYMENT_STATE
# ═════════════════════════════════════════════════════════════════════════════

class TestValidatePaymentState:
    """Tests for validate_payment_state() function."""
    
    @pytest.mark.asyncio
    async def test_validate_payment_state_valid(self, mock_callback):
        """Test case: Valid payment state."""
        from utils.payment_helpers import validate_payment_state
        
        mock_callback.message.text = "Valid message"
        
        result = await validate_payment_state(
            callback=mock_callback,
            order_id=1
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_payment_state_missing_message(self, mock_callback):
        """Test case: Missing message in callback."""
        from utils.payment_helpers import validate_payment_state
        
        mock_callback.message = None
        
        result = await validate_payment_state(
            callback=mock_callback,
            order_id=1
        )
        
        assert result is False
        assert mock_callback.answer.called
    
    @pytest.mark.asyncio
    async def test_validate_payment_state_invalid_order_id(self, mock_callback):
        """Test case: Invalid order ID."""
        from utils.payment_helpers import validate_payment_state
        
        result = await validate_payment_state(
            callback=mock_callback,
            order_id=None
        )
        
        assert result is False
        assert mock_callback.answer.called
    
    @pytest.mark.asyncio
    async def test_validate_payment_state_zero_order_id(self, mock_callback):
        """Test case: Zero order ID."""
        from utils.payment_helpers import validate_payment_state
        
        result = await validate_payment_state(
            callback=mock_callback,
            order_id=0
        )
        
        assert result is False
        assert mock_callback.answer.called


# ═════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═════════════════════════════════════════════════════════════════════════════

class TestPaymentHelpersIntegration:
    """Integration tests for payment helper functions."""
    
    @pytest.mark.asyncio
    async def test_complete_payment_validation_flow(self, mock_state, valid_order_data):
        """Test complete payment validation flow."""
        from utils.payment_helpers import validate_order_id, get_and_validate_order
        
        mock_state.get_data = AsyncMock(return_value={'order_id': 1})
        
        mock_db = AsyncMock()
        mock_db.get_order = AsyncMock(return_value=valid_order_data)
        
        with patch('utils.payment_helpers.db', mock_db):
            # Validate order ID
            order_id, is_valid = await validate_order_id(mock_state)
            assert is_valid is True
            assert order_id == 1
            
            # Get and validate order
            order, is_valid = await get_and_validate_order(
                order_id=order_id,
                user_id=valid_order_data['user_id']
            )
            assert is_valid is True
            assert order is not None
    
    @pytest.mark.asyncio
    async def test_payment_error_handling_flow(self, mock_callback):
        """Test complete error handling flow."""
        from utils.payment_helpers import validate_payment_state
        
        # Test with invalid state
        result = await validate_payment_state(
            callback=mock_callback,
            order_id=None
        )
        
        assert result is False
        assert mock_callback.answer.called
