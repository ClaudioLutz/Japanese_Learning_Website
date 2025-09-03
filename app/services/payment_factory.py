# app/services/payment_factory.py
"""
Unified Payment Service Factory
This module provides a single entry point for payment service selection with comprehensive debugging.
"""

import os
import logging
from flask import current_app

class PaymentServiceFactory:
    """Factory class for creating the appropriate payment service instance"""
    
    @staticmethod
    def get_service():
        """
        Get the appropriate payment service based on configuration
        Returns either MockPaymentService or PostFinanceService
        """
        logger = logging.getLogger(__name__)
        
        # Add comprehensive debugging
        logger.info("=== PAYMENT SERVICE SELECTION DEBUG ===")
        
        # Check environment variables directly
        env_mock_enabled = os.environ.get('MOCK_PAYMENTS_ENABLED', 'not_set')
        env_pf_space_id = os.environ.get('POSTFINANCE_SPACE_ID', 'not_set')
        env_pf_user_id = os.environ.get('POSTFINANCE_USER_ID', 'not_set')  
        env_pf_api_secret = os.environ.get('POSTFINANCE_API_SECRET', 'not_set')
        
        logger.info(f"Environment Variables:")
        logger.info(f"  MOCK_PAYMENTS_ENABLED = '{env_mock_enabled}'")
        logger.info(f"  POSTFINANCE_SPACE_ID = '{env_pf_space_id[:10]}...' (truncated)" if env_pf_space_id != 'not_set' else f"  POSTFINANCE_SPACE_ID = '{env_pf_space_id}'")
        logger.info(f"  POSTFINANCE_USER_ID = '{env_pf_user_id[:10]}...' (truncated)" if env_pf_user_id != 'not_set' else f"  POSTFINANCE_USER_ID = '{env_pf_user_id}'")
        logger.info(f"  POSTFINANCE_API_SECRET = '{'SET' if env_pf_api_secret != 'not_set' else 'NOT_SET'}'")
        
        # Check Flask app config
        try:
            config_mock_enabled = current_app.config.get('MOCK_PAYMENTS_ENABLED', 'not_in_config')
            config_pf_space_id = current_app.config.get('POSTFINANCE_SPACE_ID', 'not_in_config')
            config_pf_user_id = current_app.config.get('POSTFINANCE_USER_ID', 'not_in_config')
            config_pf_api_secret = current_app.config.get('POSTFINANCE_API_SECRET', 'not_in_config')
            
            logger.info(f"Flask Config:")
            logger.info(f"  MOCK_PAYMENTS_ENABLED = '{config_mock_enabled}'")
            logger.info(f"  POSTFINANCE_SPACE_ID = '{config_pf_space_id[:10]}...' (truncated)" if config_pf_space_id != 'not_in_config' else f"  POSTFINANCE_SPACE_ID = '{config_pf_space_id}'")
            logger.info(f"  POSTFINANCE_USER_ID = '{config_pf_user_id[:10]}...' (truncated)" if config_pf_user_id != 'not_in_config' else f"  POSTFINANCE_USER_ID = '{config_pf_user_id}'")
            logger.info(f"  POSTFINANCE_API_SECRET = '{'SET' if config_pf_api_secret != 'not_in_config' else 'NOT_SET'}'")
            
        except Exception as e:
            logger.error(f"Error accessing Flask config: {e}")
            config_mock_enabled = 'config_error'
            config_pf_space_id = 'config_error'
            config_pf_user_id = 'config_error' 
            config_pf_api_secret = 'config_error'
        
        # Decision logic with detailed logging
        logger.info("=== DECISION LOGIC ===")
        
        # Check if we're explicitly in mock mode
        mock_enabled_by_env = env_mock_enabled.lower() == 'true'
        mock_enabled_by_config = config_mock_enabled is True or (isinstance(config_mock_enabled, str) and config_mock_enabled.lower() == 'true')
        
        logger.info(f"Mock enabled by environment: {mock_enabled_by_env}")
        logger.info(f"Mock enabled by config: {mock_enabled_by_config}")
        
        force_mock_mode = mock_enabled_by_env or mock_enabled_by_config
        logger.info(f"Force mock mode: {force_mock_mode}")
        
        # Check if PostFinance credentials are configured
        postfinance_env_configured = all([
            env_pf_space_id != 'not_set',
            env_pf_user_id != 'not_set', 
            env_pf_api_secret != 'not_set'
        ])
        
        postfinance_config_configured = all([
            config_pf_space_id != 'not_in_config' and config_pf_space_id is not None,
            config_pf_user_id != 'not_in_config' and config_pf_user_id is not None,
            config_pf_api_secret != 'not_in_config' and config_pf_api_secret is not None
        ])
        
        logger.info(f"PostFinance configured via environment: {postfinance_env_configured}")
        logger.info(f"PostFinance configured via config: {postfinance_config_configured}")
        
        postfinance_configured = postfinance_env_configured or postfinance_config_configured
        logger.info(f"PostFinance overall configured: {postfinance_configured}")
        
        # Make the decision
        if force_mock_mode:
            logger.info("DECISION: Using MockPaymentService (explicitly enabled)")
            from app.services.mock_payment_service import MockPaymentService
            return MockPaymentService()
        elif not postfinance_configured:
            logger.info("DECISION: Using MockPaymentService (PostFinance not configured)")
            from app.services.mock_payment_service import MockPaymentService
            return MockPaymentService()
        else:
            logger.info("DECISION: Attempting PostFinanceService (credentials configured)")
            try:
                from app.services.payment_service import EnhancedPostFinanceService
                service = EnhancedPostFinanceService()
                logger.info("PostFinanceService initialized successfully")
                return service
            except Exception as e:
                logger.error(f"PostFinanceService initialization failed: {e}")
                logger.info("FALLBACK: Using MockPaymentService")
                from app.services.mock_payment_service import MockPaymentService
                return MockPaymentService()


def get_payment_service():
    """
    Main entry point for getting payment service
    """
    return PaymentServiceFactory.get_service()
