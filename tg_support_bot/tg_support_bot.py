import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from TGdb_session import global_init, create_session
from TGClasses import Question, User
from os import makedirs


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

QUESTIONS_CHAT_ID = -1003238008855
makedirs('db_bot', exist_ok=True)
global_init(True, "db_bot/bot_database.db")


class QuestionBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_answer, pattern="^answer_"))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            "Я бот для вопросов и ответов. Просто напиши свой вопрос, "
            "и я передам его нашей команде. Когда будет готов ответ, "
            "я пришлю его тебе!"
        )

        self.save_user(user.id, user.username, is_admin=False)

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if update.effective_chat.id != QUESTIONS_CHAT_ID:
            return

        if context.args:
            try:
                target_user_id = int(context.args[0])
                self.make_admin(target_user_id)
                await update.message.reply_text(f"✅ Пользователь {target_user_id} назначен администратором")
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
        else:
            self.save_user(user.id, user.username, is_admin=True)
            await update.message.reply_text("✅ Вы назначены администратором")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat_id = update.effective_chat.id
        if chat_id == QUESTIONS_CHAT_ID:
            await self.handle_admin_reply(update, context)
        else:
            await self.handle_question(update, context)

    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        question_text = update.message.text
        self.save_user(user.id, user.username, is_admin=False)

        question_id = self.save_question(user.id, question_text)

        if question_id == -1:
            await update.message.reply_text("❌ Произошла ошибка при сохранении вопроса. Попробуйте позже.")
            return

        keyboard = [
            [InlineKeyboardButton("📝 Ответить на вопрос", callback_data=f"answer_{question_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = (
            f"❓ Новый вопрос от @{user.username or 'пользователя'} (ID: {user.id}):\n\n"
            f"{question_text}\n\n"
            f"ID вопроса: {question_id}"
        )

        try:
            await context.bot.send_message(
                chat_id=QUESTIONS_CHAT_ID,
                text=message_text,
                reply_markup=reply_markup
            )

            await update.message.reply_text(
                "✅ Ваш вопрос отправлен! Ожидайте ответа от нашей команды."
            )

        except Exception as e:
            logger.error(f"Ошибка при отправке вопроса в админ-чат: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при отправке вопроса. Попробуйте позже."
            )

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user = query.from_user

        if not self.is_admin(user.id):
            await query.answer("❌ Только администраторы могут отвечать на вопросы", show_alert=True)
            return

        await query.answer()

        question_id = int(query.data.split('_')[1])

        context.user_data['waiting_for_answer'] = True
        context.user_data['question_id'] = question_id

        session = create_session()
        question = session.query(Question).filter_by(id=question_id).first()
        session.close()

        await query.edit_message_text(
            f"📝 Вы отвечаете на вопрос ID: {question_id}\n\n"
            f"Вопрос: {question.question_text}\n\n"
            "Пожалуйста, введите ваш ответ:"
        )

    async def handle_admin_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if not self.is_admin(user.id):
            await update.message.reply_text("❌ У вас нет прав для ответа на вопросы")
            return

        if context.user_data.get('waiting_for_answer'):
            question_id = context.user_data['question_id']
            admin_reply = update.message.text

            session = create_session()
            try:
                question = session.query(Question).filter(Question.id == question_id).first()
                if question:
                    question.admin_reply = admin_reply
                    question.answered = True
                    session.commit()

                    try:
                        await context.bot.send_message(
                            chat_id=question.user_id,
                            text=f"📨 Ответ на ваш вопрос: {question.question_text}\n\nОтвет: {admin_reply}\n\n"
                                 f"Если у вас есть дополнительные вопросы, просто напишите их мне!"
                        )

                        await update.message.reply_text("✅ Ответ отправлен пользователю!")

                        try:
                            await context.bot.edit_message_text(
                                chat_id=QUESTIONS_CHAT_ID,
                                message_id=update.message.message_id - 1,  # Предыдущее сообщение с вопросом
                                text=f"✅ ОТВЕЧЕНО: {update.message.text}"
                            )
                        except:
                            pass

                    except Exception as e:
                        logger.error(f"Ошибка при отправке ответа пользователю: {e}")
                        await update.message.reply_text(
                            "❌ Не удалось отправить ответ пользователю. "
                            "Возможно, он заблокировал бота."
                        )

                else:
                    await update.message.reply_text("❌ Вопрос не найден!")

            finally:
                session.close()

            context.user_data['waiting_for_answer'] = False
            context.user_data['question_id'] = None
        else:
            await update.message.reply_text(
                "ℹ️ Чтобы ответить на вопрос, нажмите кнопку 'Ответить на вопрос' под соответствующим сообщением."
            )

    def save_user(self, user_id: int, username: str, is_admin: bool = False):
        session = create_session()
        try:
            existing_user = session.query(User).filter(User.id == user_id).first()
            if existing_user:
                existing_user.tg_username = username or "unknown"
                existing_user.is_admin = is_admin
            else:
                user = User(
                    id=user_id,
                    tg_username=username or "unknown",
                    is_admin=is_admin
                )
                session.add(user)
            session.commit()
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователя: {e}")
            session.rollback()
        finally:
            session.close()

    def make_admin(self, user_id: int):
        session = create_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.is_admin = True
            else:
                user = User(
                    id=user_id,
                    tg_username="unknown",
                    is_admin=True
                )
                session.add(user)
            session.commit()
        except Exception as e:
            logger.error(f"Ошибка при назначении администратора: {e}")
            session.rollback()
        finally:
            session.close()

    def is_admin(self, user_id: int) -> bool:
        session = create_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            return user.is_admin if user else False
        except Exception as e:
            logger.error(f"Ошибка при проверке прав администратора: {e}")
            return False
        finally:
            session.close()

    def save_question(self, user_id: int, question_text: str) -> int:
        session = create_session()
        try:
            question = Question(
                user_id=user_id,
                question_text=question_text,
                answered=False
            )
            session.add(question)
            session.commit()
            return question.id
        except Exception as e:
            logger.error(f"Ошибка при сохранении вопроса: {e}")
            session.rollback()
            return -1
        finally:
            session.close()

    def run(self):
        self.application.run_polling()


if __name__ == "__main__":
    BOT_TOKEN = "8337323494:AAHievSga4n-28tzYqtIbFellut7GxBAgDk"

    bot = QuestionBot(BOT_TOKEN)
    bot.run()