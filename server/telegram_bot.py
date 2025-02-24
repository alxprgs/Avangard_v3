import os
import httpx
from datetime import datetime
import telegram
from telegram import Update, Bot, ChatMember
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from .database import database
from .functions import get_next_id
from .logging import logger

class TelegramUser:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.nickname = None
        self.common_chats = []
        self.registration_step = 0 

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.users = {}
        self.app = Application.builder().token(self.token).build()
        
        handlers = [
            CommandHandler("start", self.handle_start),
            CommandHandler("group", self.handle_group),
            CommandHandler("update", self.handle_update),
            CommandHandler("reset_key", self.handle_reset_key),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        ]
        
        for handler in handlers:
            self.app.add_handler(handler)
    
    async def handle_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        try:
            common_chats = await self.get_common_chats(user.id)
            users_col = database["users"]
            result = await users_col.update_one(
                {"tg_id": user.id},
                {"$set": {"chats": common_chats}},
                upsert=False
            )
            
            if result.modified_count > 0:
                await update.message.reply_text("✅ Список чатов успешно обновлен!")
            else:
                await update.message.reply_text("ℹ️ Нет изменений для обновления")
                
        except Exception as e:
            logger.error(f"Ошибка обновления чатов: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Ошибка обновления чатов")

    async def handle_reset_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:{os.getenv('PORT')}/v1/reset_key",
                    headers={"X-API-Key": os.getenv("API_KEY")},
                    json={"tg_id": user.id}
                )
            
            if response.status_code == 200:
                new_key = response.json().get("key", "не получен")
                await update.message.reply_text(f"✅ Новый ключ доступа: {new_key}")
            else:
                await update.message.reply_text(f"❌ Ошибка: {response.text}")
                
        except Exception as e:
            logger.error(f"Ошибка при сбросе ключа: {e}")
            await update.message.reply_text("⚠️ Произошла ошибка при сбросе ключа")

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        tg_user = TelegramUser(user.id)
        
        try:
            common_chats = await self.get_common_chats(user.id)
            tg_user.common_chats = common_chats
        except Exception as e:
            logger.error(f"Ошибка получения чатов: {e}")
            await update.message.reply_text("Ошибка получения данных о чатах")
            return

        self.users[user.id] = tg_user
        tg_user.registration_step = 1
        
        await update.message.reply_text(
            "📝 Введите желаемый никнейм (3-32 символа):"
        )

    async def get_common_chats(self, user_id: int) -> list:
        groups_col = database["groups"]
        return await groups_col.distinct(
            "chat_id", 
            {"members.user_id": user_id}
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.message
        
        if user.id in self.users and self.users[user.id].registration_step == 1:
            await self.process_registration(update)
            return
            
        await self.save_message(update)

    async def process_registration(self, update: Update):
        user = update.effective_user
        tg_user = self.users[user.id]
        nickname = update.message.text.strip()
        
        if 3 <= len(nickname) <= 32:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://localhost:{os.getenv("PORT")}/v1/create_user",
                        json={
                            "tg_id": user.id,
                            "nickname": nickname,
                            "chats": tg_user.common_chats
                        },
                        headers={"X-API-Key": os.getenv("API_KEY")}
                    )
                    
                if response.status_code == 200:
                    del self.users[user.id]
                    await update.message.reply_text(
                        f"✅ Регистрация завершена!\nКлюч доступа: `{response.json()['key']}`",
                        parse_mode="MarkdownV2"
                    )
                else:
                    await update.message.reply_text(f"❌ Ошибка: {response.text}")
                    
            except Exception as e:
                logger.error(f"Ошибка регистрации: {e}")
                await update.message.reply_text("⚠️ Ошибка связи с сервером")
        else:
            await update.message.reply_text("❌ Некорректная длина ника (3-32 символа)")

    async def save_message(self, update: Update):
        try:
            message = update.message
            user = update.effective_user
            messages_col = database["messages"]
            
            await messages_col.insert_one({
                "_id": await get_next_id(messages_col),
                "message_id": message.message_id,
                "user_id": user.id,
                "chat_id": message.chat.id,
                "text": message.text,
                "timestamp": datetime.utcnow()
            })
            
            logger.info(f"Сообщение от {user.id} сохранено")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения: {e}")
            await update.message.reply_text("⚠️ Ошибка сохранения сообщения")

    async def handle_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat = update.effective_chat
            user = update.effective_user

            if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
                await update.message.reply_text("ℹ️ Команда доступна только в группах!")
                return

            admin_status = await context.bot.get_chat_member(chat.id, user.id)
            if admin_status.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                await update.message.reply_text("⛔ Требуются права администратора!")
                return

            administrators = await context.bot.get_chat_administrators(chat.id)
            
            members = []
            for admin in administrators:
                member = admin.user
                if not member.is_bot:
                    members.append({
                        "user_id": member.id,
                        "username": member.username or member.full_name,
                        "full_name": member.full_name
                    })

            group_data = {
                "chat_id": chat.id,
                "title": chat.title,
                "members": members,
                "updated_at": datetime.utcnow()
            }

            groups_col = database["groups"]
            result = await groups_col.update_one(
                {"chat_id": chat.id},
                {"$set": group_data},
                upsert=True
            )

            action = "добавлена" if result.upserted_id else "обновлена"
            await update.message.reply_text(
                f"✅ Группа {action}!\n"
                f"🏷 Название: {chat.title}\n"
                f"👥 Администраторов: {len(members)}"
            )

        except Exception as e:
            logger.error(f"Ошибка обработки группы: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Ошибка обработки группы")

    async def start(self):
        await self.app.initialize()
        await self.app.start()
        logger.info("Telegram бот запущен")
        await self.app.updater.start_polling()

    async def stop(self):
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("Telegram бот остановлен.")