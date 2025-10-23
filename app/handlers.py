"""
Telegram command and message handlers for Pablos bot.
"""

import logging
from typing import Optional
from io import BytesIO

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.ai_client import GradientAIClient
from app.memory import ConversationMemory
from app.file_storage import FileStorage
from app.utils import (
    RateLimiter, SimpleCache, chunk_message, hash_prompt,
    detect_code_block, is_explain_request, extract_explain_content,
    sanitize_user_input
)
from app.prompts import (
    build_chat_prompt, build_code_help_prompt, build_image_prompt,
    get_empathy_prompt, get_system_prompt
)

logger = logging.getLogger(__name__)


class BotHandlers:
    """Container for all bot command and message handlers."""

    def __init__(self, ai_client: GradientAIClient, memory: ConversationMemory,
                 rate_limiter: RateLimiter, cache: SimpleCache, file_storage: FileStorage):
        """
        Initialize handlers.

        Args:
            ai_client: Gradient AI client
            memory: Conversation memory manager
            rate_limiter: Rate limiter instance
            cache: Cache instance
            file_storage: File storage instance
        """
        self.ai_client = ai_client
        self.memory = memory
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.file_storage = file_storage
        self.vent_mode_users = set()  # Track users in vent mode
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        welcome_message = (
            f"Halo {user.first_name}! 👋\n\n"
            "Gue Pablos, temen chatbot lu yang santai dan asik! "
            "Gue bisa bantuin lu buat:\n\n"
            "💬 Ngobrol santai (multi-turn conversation)\n"
            "🎨 Bikin gambar - pakai /image <deskripsi>\n"
            "💻 Bantuin ngoding - kirim kode atau pakai 'explain:'\n"
            "❤️ Dengerin curhat - pakai /vent\n\n"
            "Langsung aja chat gue, gak usah formal! 😎"
        )
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "📚 *Cara Pakai Pablos Bot:*\n\n"
            "*Ngobrol Biasa:*\n"
            "Langsung chat aja, gue bakal inget percakapan kita!\n\n"
            "*Generate Gambar:*\n"
            "`/image <deskripsi gambar>`\n"
            "Contoh: `/image sunset di pantai dengan burung camar`\n\n"
            "*Bantuan Coding:*\n"
            "- Kirim kode dalam format markdown (```kode```)\n"
            "- Atau pakai: `explain: <kode lu>`\n\n"
            "*Mode Curhat:*\n"
            "`/vent` - Gue bakal dengerin dengan empati\n\n"
            "*File & Media:*\n"
            "- Kirim foto, video, audio, atau dokumen - gue bakal simpen!\n"
            "`/files` - Liat semua file yang udah lu upload\n"
            "`/clearfiles` - Hapus semua file lu\n\n"
            "*Perintah Lain:*\n"
            "`/clear` - Hapus history percakapan\n"
            "`/help` - Tampilkan pesan ini\n\n"
            "Santai aja, gue di sini buat bantuin lu! 🤙"
        )

        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear command to clear conversation history."""
        user_id = update.effective_user.id
        self.memory.clear_history(user_id)
        
        # Also remove from vent mode if active
        if user_id in self.vent_mode_users:
            self.vent_mode_users.remove(user_id)
        
        logger.info(f"Cleared history for user {user_id}")
        await update.message.reply_text(
            "Oke bro, history percakapan kita udah gue hapus! "
            "Kita mulai dari awal lagi ya 🔄"
        )
    
    async def vent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /vent command to enter empathy mode."""
        user_id = update.effective_user.id
        self.vent_mode_users.add(user_id)
        
        logger.info(f"User {user_id} entered vent mode")
        await update.message.reply_text(
            "Oke bro, gue dengerin kok. Ceritain aja apa yang lu rasain, "
            "gue di sini buat lu 💙\n\n"
            "Kalau udah selesai, pakai /clear buat keluar dari mode ini."
        )
    
    async def image_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /image command to generate images."""
        user_id = update.effective_user.id
        
        # Check rate limit
        allowed, remaining = self.rate_limiter.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(
                f"Santai bro, tunggu {remaining:.1f} detik lagi ya! ⏳"
            )
            return
        
        # Get the description
        if not context.args:
            await update.message.reply_text(
                "Kasih deskripsi gambar yang lu mau dong!\n"
                "Contoh: `/image sunset di pantai dengan burung camar`",
                parse_mode='Markdown'
            )
            return
        
        description = ' '.join(context.args)
        description = sanitize_user_input(description, max_length=500)
        
        logger.info(f"User {user_id} requested image: {description[:50]}...")
        
        # Show typing indicator
        await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
        
        try:
            # Generate image prompt
            prompt_query = build_image_prompt(description)
            image_prompt = self.ai_client.generate_chat_response(prompt_query, temperature=0.8)
            
            if not image_prompt:
                await update.message.reply_text(
                    "Waduh, gue gagal bikin prompt gambarnya nih. Coba lagi ya! 😅"
                )
                return
            
            logger.info(f"Generated image prompt: {image_prompt[:100]}...")
            
            # Generate image
            await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
            image_bytes = self.ai_client.generate_image(image_prompt)
            
            if image_bytes:
                # Send the image
                await update.message.reply_photo(
                    photo=BytesIO(image_bytes),
                    caption=f"Nih gambarnya! 🎨\n\nPrompt: {description}"
                )
                logger.info(f"Successfully sent image to user {user_id}")
            else:
                await update.message.reply_text(
                    "Waduh, gagal generate gambarnya nih. Coba lagi nanti ya! 😅"
                )
        
        except Exception as e:
            logger.error(f"Error in image generation: {e}", exc_info=True)
            await update.message.reply_text(
                "Anjir, ada error nih. Coba lagi nanti ya! 🙏"
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages."""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if not user_message:
            return
        
        # Check rate limit
        allowed, remaining = self.rate_limiter.check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(
                f"Tunggu {remaining:.1f} detik lagi ya bro! ⏳"
            )
            return
        
        user_message = sanitize_user_input(user_message)
        logger.info(f"User {user_id} sent message: {user_message[:50]}...")
        
        # Show typing indicator
        await update.message.chat.send_action(ChatAction.TYPING)
        
        try:
            # Check if it's a code help request
            code_block = detect_code_block(user_message)
            is_explain = is_explain_request(user_message)
            
            if code_block or is_explain:
                await self._handle_code_help(update, user_id, user_message, code_block, is_explain)
            else:
                await self._handle_chat(update, user_id, user_message)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "Waduh, ada error nih. Coba lagi ya! 🙏"
            )
    
    async def _handle_code_help(self, update: Update, user_id: int, 
                                user_message: str, code_block: Optional[str], 
                                is_explain: bool) -> None:
        """Handle code help requests."""
        if is_explain:
            code = extract_explain_content(user_message)
        else:
            code = code_block
        
        logger.info(f"Code help request from user {user_id}")
        
        # Build code help prompt
        prompt = build_code_help_prompt(code)
        
        # Check cache
        cache_key = hash_prompt(prompt)
        cached_response = self.cache.get(cache_key)
        
        if cached_response:
            response = cached_response
            logger.info("Using cached code help response")
        else:
            response = self.ai_client.generate_chat_response(prompt, temperature=0.5)
            if response:
                self.cache.set(cache_key, response)
        
        if response:
            # Send response in chunks if needed
            chunks = chunk_message(response)
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(
                "Waduh, gue gagal analisis kode lu nih. Coba lagi ya! 😅"
            )
    
    async def _handle_chat(self, update: Update, user_id: int, user_message: str) -> None:
        """Handle regular chat messages."""
        # Add user message to history
        self.memory.add_user_message(user_id, user_message)
        
        # Get conversation history
        history = self.memory.format_history_for_prompt(user_id, max_messages=8)
        
        # Choose system prompt based on mode
        if user_id in self.vent_mode_users:
            system_prompt = get_empathy_prompt()
        else:
            system_prompt = get_system_prompt()
        
        # Build prompt
        prompt = build_chat_prompt(system_prompt, history, user_message)
        
        # Check cache
        cache_key = hash_prompt(prompt)
        cached_response = self.cache.get(cache_key)
        
        if cached_response:
            response = cached_response
            logger.info("Using cached chat response")
        else:
            response = self.ai_client.generate_chat_response(prompt, temperature=0.8)
            if response:
                self.cache.set(cache_key, response)

        if response:
            # Add assistant response to history
            self.memory.add_assistant_message(user_id, response)

            # Send response in chunks if needed
            chunks = chunk_message(response)
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(
                "Waduh, gue lagi error nih. Coba lagi ya! 😅"
            )

    async def files_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /files command - list user's uploaded files."""
        user_id = update.effective_user.id

        files = self.file_storage.get_recent_files(user_id, limit=20)
        message = self.file_storage.format_file_list(files)

        await update.message.reply_text(message)

    async def clearfiles_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clearfiles command - clear user's uploaded files."""
        user_id = update.effective_user.id

        count = self.file_storage.get_file_count(user_id)
        if count == 0:
            await update.message.reply_text("Lu gak punya file yang tersimpan jir wkwk")
            return

        self.file_storage.clear_user_files(user_id)
        await update.message.reply_text(f"Oke, {count} file lu udah gue hapus semua! 🗑️")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo uploads."""
        user_id = update.effective_user.id
        photo = update.message.photo[-1]  # Get highest resolution
        caption = update.message.caption or ""

        # Store photo metadata
        self.file_storage.add_file(
            user_id=user_id,
            file_id=photo.file_id,
            file_type='photo',
            file_name=f"photo_{photo.file_unique_id}.jpg",
            file_size=photo.file_size,
            description=caption
        )

        count = self.file_storage.get_file_count(user_id)
        await update.message.reply_text(
            f"Oke jir, foto lu udah gue simpen! 📸\n"
            f"Total file lu sekarang: {count}\n\n"
            f"Ketik /files buat liat semua file lu"
        )

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle document uploads."""
        user_id = update.effective_user.id
        document = update.message.document
        caption = update.message.caption or ""

        # Store document metadata
        self.file_storage.add_file(
            user_id=user_id,
            file_id=document.file_id,
            file_type='document',
            file_name=document.file_name or f"document_{document.file_unique_id}",
            file_size=document.file_size,
            description=caption
        )

        count = self.file_storage.get_file_count(user_id)
        await update.message.reply_text(
            f"Oke, file lu udah gue simpen! 📄\n"
            f"Total file lu sekarang: {count}\n\n"
            f"Ketik /files buat liat semua file lu"
        )

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle video uploads."""
        user_id = update.effective_user.id
        video = update.message.video
        caption = update.message.caption or ""

        # Store video metadata
        self.file_storage.add_file(
            user_id=user_id,
            file_id=video.file_id,
            file_type='video',
            file_name=f"video_{video.file_unique_id}.mp4",
            file_size=video.file_size,
            description=caption
        )

        count = self.file_storage.get_file_count(user_id)
        await update.message.reply_text(
            f"Oke jir, video lu udah gue simpen! 🎥\n"
            f"Total file lu sekarang: {count}\n\n"
            f"Ketik /files buat liat semua file lu"
        )

    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle audio uploads."""
        user_id = update.effective_user.id
        audio = update.message.audio
        caption = update.message.caption or ""

        # Store audio metadata
        self.file_storage.add_file(
            user_id=user_id,
            file_id=audio.file_id,
            file_type='audio',
            file_name=audio.file_name or f"audio_{audio.file_unique_id}.mp3",
            file_size=audio.file_size,
            description=caption
        )

        count = self.file_storage.get_file_count(user_id)
        await update.message.reply_text(
            f"Oke, audio lu udah gue simpen! 🎵\n"
            f"Total file lu sekarang: {count}\n\n"
            f"Ketik /files buat liat semua file lu"
        )

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle voice message uploads."""
        user_id = update.effective_user.id
        voice = update.message.voice

        # Store voice metadata
        self.file_storage.add_file(
            user_id=user_id,
            file_id=voice.file_id,
            file_type='voice',
            file_name=f"voice_{voice.file_unique_id}.ogg",
            file_size=voice.file_size,
            description="Voice message"
        )

        count = self.file_storage.get_file_count(user_id)
        await update.message.reply_text(
            f"Oke jir, voice message lu udah gue simpen! 🎤\n"
            f"Total file lu sekarang: {count}\n\n"
            f"Ketik /files buat liat semua file lu"
        )

