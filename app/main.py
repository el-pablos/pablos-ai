"""
Main entry point for Pablos Telegram bot.
Supports both polling and webhook modes.
"""

import os
import sys
import logging
from typing import Optional

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.ai_client import create_ai_client, EndpointConfig
from app.memory import ConversationMemory
from app.file_storage import FileStorage
from app.utils import RateLimiter, SimpleCache
from app.handlers import BotHandlers

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pablos_bot.log')
    ]
)
logger = logging.getLogger(__name__)


class PablosBot:
    """Main bot application class."""
    
    def __init__(self):
        """Initialize the bot with configuration from environment variables."""
        # Load configuration
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '400'))
        self.cooldown = int(os.getenv('COOLDOWN', '2'))
        self.webhook_url = os.getenv('WEBHOOK_URL')
        self.port = int(os.getenv('PORT', '8443'))
        self.endpoint_cooldown = int(os.getenv('ENDPOINT_COOLDOWN', '300'))  # 5 minutes default

        # Validate required configuration
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        # Load endpoint configurations
        self.endpoints = self._load_endpoints()
        if not self.endpoints:
            raise ValueError("At least one endpoint configuration is required")

        logger.info("Configuration loaded successfully")
        logger.info(f"Loaded {len(self.endpoints)} endpoint(s)")
        logger.info(f"Max tokens: {self.max_tokens}")
        logger.info(f"Cooldown: {self.cooldown}s")
        logger.info(f"Endpoint cooldown: {self.endpoint_cooldown}s")

        # Initialize components
        self._init_components()

    def _load_endpoints(self) -> list:
        """Load endpoint configurations from environment variables."""
        endpoints = []

        # Try to load up to 3 endpoints (can be extended)
        for i in range(1, 4):
            suffix = "" if i == 1 else f"_{i}"

            access_key = os.getenv(f'MODEL_ACCESS_KEY{suffix}')
            base_url = os.getenv(f'MODEL_BASE_URL{suffix}')
            model_chat = os.getenv(f'MODEL_CHAT{suffix}')
            model_image = os.getenv(f'MODEL_IMAGE{suffix}')

            # Skip if access key is not provided
            if not access_key:
                continue

            # Use defaults if not specified
            if not base_url:
                base_url = "https://ai.megallm.io/v1"
            if not model_chat:
                model_chat = "gpt-4.1"
            if not model_image:
                model_image = "stability-image-1"

            endpoint = EndpointConfig(
                base_url=base_url,
                access_key=access_key,
                model_chat=model_chat,
                model_image=model_image,
                name=f"endpoint-{i}" if i > 1 else "primary"
            )

            endpoints.append(endpoint)
            logger.info(f"Loaded {endpoint.name}: {base_url} (chat: {model_chat})")

        return endpoints

    def _init_components(self):
        """Initialize bot components."""
        # Initialize AI client with multi-endpoint support
        logger.info("Initializing AI client with multi-endpoint failover...")
        self.ai_client = create_ai_client(
            endpoints=self.endpoints,
            max_tokens=self.max_tokens,
            use_mock=False,  # Set to True for testing without API calls
            enable_fallback=True,
            endpoint_cooldown=self.endpoint_cooldown
        )
        
        # Initialize memory
        logger.info("Initializing conversation memory...")
        redis_url = os.getenv('REDIS_URL')
        redis_host = os.getenv('REDIS_HOST')
        redis_port = os.getenv('REDIS_PORT')
        redis_password = os.getenv('REDIS_PASSWORD')
        redis_username = os.getenv('REDIS_USERNAME')
        
        self.memory = ConversationMemory(
            redis_url=redis_url,
            redis_host=redis_host,
            redis_port=int(redis_port) if redis_port else None,
            redis_password=redis_password,
            redis_username=redis_username
        )
        
        # Initialize rate limiter and cache
        logger.info("Initializing rate limiter and cache...")
        self.rate_limiter = RateLimiter(cooldown_seconds=self.cooldown)
        self.cache = SimpleCache(ttl_seconds=3600)  # 1 hour cache

        # Initialize file storage
        logger.info("Initializing file storage...")
        self.file_storage = FileStorage(storage_dir="user_files")

        # Initialize handlers
        logger.info("Initializing handlers...")
        self.handlers = BotHandlers(
            ai_client=self.ai_client,
            memory=self.memory,
            rate_limiter=self.rate_limiter,
            cache=self.cache,
            file_storage=self.file_storage
        )
    
    def _setup_handlers(self, application: Application):
        """Set up command and message handlers."""
        # Command handlers
        application.add_handler(CommandHandler("start", self.handlers.start_command))
        application.add_handler(CommandHandler("help", self.handlers.help_command))
        application.add_handler(CommandHandler("clear", self.handlers.clear_command))
        application.add_handler(CommandHandler("vent", self.handlers.vent_command))
        application.add_handler(CommandHandler("image", self.handlers.image_command))
        application.add_handler(CommandHandler("files", self.handlers.files_command))
        application.add_handler(CommandHandler("clearfiles", self.handlers.clearfiles_command))

        # File/media handlers
        application.add_handler(MessageHandler(filters.PHOTO, self.handlers.handle_photo))
        application.add_handler(MessageHandler(filters.Document.ALL, self.handlers.handle_document))
        application.add_handler(MessageHandler(filters.VIDEO, self.handlers.handle_video))
        application.add_handler(MessageHandler(filters.AUDIO, self.handlers.handle_audio))
        application.add_handler(MessageHandler(filters.VOICE, self.handlers.handle_voice))

        # Message handler (for regular text messages)
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message)
        )

        logger.info("Handlers registered successfully")
    
    async def post_init(self, application: Application):
        """Post-initialization hook."""
        logger.info("Bot initialized and ready!")
    
    async def post_shutdown(self, application: Application):
        """Post-shutdown hook."""
        logger.info("Shutting down bot...")
        if hasattr(self.ai_client, 'close'):
            self.ai_client.close()
        logger.info("Bot shutdown complete")
    
    def run_polling(self):
        """Run the bot in polling mode."""
        logger.info("Starting bot in polling mode...")
        
        # Create application
        application = Application.builder().token(self.telegram_token).build()
        
        # Set up handlers
        self._setup_handlers(application)
        
        # Set up lifecycle hooks
        application.post_init = self.post_init
        application.post_shutdown = self.post_shutdown
        
        # Start polling
        logger.info("Bot is now polling for updates...")
        application.run_polling(allowed_updates=["message", "callback_query"])
    
    def run_webhook(self):
        """Run the bot in webhook mode."""
        if not self.webhook_url:
            raise ValueError("WEBHOOK_URL is required for webhook mode")
        
        logger.info(f"Starting bot in webhook mode on {self.webhook_url}...")
        
        # Create application
        application = Application.builder().token(self.telegram_token).build()
        
        # Set up handlers
        self._setup_handlers(application)
        
        # Set up lifecycle hooks
        application.post_init = self.post_init
        application.post_shutdown = self.post_shutdown
        
        # Start webhook
        logger.info(f"Bot is now listening for webhooks on port {self.port}...")
        application.run_webhook(
            listen="0.0.0.0",
            port=self.port,
            url_path="webhook",
            webhook_url=f"{self.webhook_url}/webhook"
        )


def main():
    """Main entry point."""
    try:
        # Create and run bot
        bot = PablosBot()
        
        # Check if webhook mode is requested
        webhook_url = os.getenv('WEBHOOK_URL')
        
        if webhook_url:
            logger.info("Webhook URL detected, running in webhook mode")
            bot.run_webhook()
        else:
            logger.info("No webhook URL, running in polling mode")
            bot.run_polling()
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

