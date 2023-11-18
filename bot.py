import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from api.instagram import InstagramAPI
from api.vtt import VideoToText
from api.chatgpt import GPTConversation
import api.constants as constants
from langdetect import detect
from config import TELEGRAM_BOT_TOKEN

RUSSIAN_FLAG = "\U0001F1F7\U0001F1FA"
AMERICAN_FLAG = "\U0001F1FA\U0001F1F8"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=logging.INFO
)

# Constants for translation
TRANSLATE_TO_RUSSIAN, TRANSLATE_TO_ENGLISH = "translate_to_ru", "translate_to_en"

instagram_api = InstagramAPI()
vtt_api = VideoToText()
gpt_api = GPTConversation()

# Cache for recipies to avoid redundant translations
recipes = {
    "ru": {},
    "en": {},
}

# Processing status for translations by reel link
processing = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=constants.START_MESSAGE)


def is_reel(text):
    return "instagram.com/reel/" in text


async def handle_message(update, context):
    if not is_reel(update.message.text):
        # In  personal chats, send an error message.
        if update.message.chat.type == "private":
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=constants.INVALID_MESSAGE
            )
        # Otherwise, skip
        return
    await process_reel(update, context)


# Function to send recipe with inline keyboard
async def send_recipe_with_translation_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE, recipe, language
):
    language_label = "Russian" if language == "en" else "English"
    flag = RUSSIAN_FLAG if language == "en" else AMERICAN_FLAG
    callback_data = TRANSLATE_TO_RUSSIAN if language == "en" else TRANSLATE_TO_ENGLISH

    keyboard = [
        [InlineKeyboardButton(f"Translate to {language_label} {flag}", callback_data=callback_data)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=recipe, reply_markup=reply_markup, parse_mode="HTML"
    )


async def process_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if "instagram.com/reel/" not in message.text:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=constants.INVALID_MESSAGE
        )
        return

    processing_message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Processing..."
    )

    # Update message to "Watching the video..."
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=processing_message.message_id,
        text="Watching the video...",
    )
    reel_info = instagram_api.get_reel_info(message.text)

    if not reel_info:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
            text=constants.ERROR_MESSAGE,
        )
        return

    # Determine language of the reel
    lang = detect(reel_info["description"])
    logging.info(f"Determined language: {lang}")

    if lang not in ["en", "ru"]:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
            text=constants.ERROR_MESSAGE,
        )
        return

    # Update message to "Transcribing..."
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=processing_message.message_id,
        text="Transcribing...",
    )
    vtt_api.set_language(lang)
    transcription = vtt_api.transcribe_video(reel_info["video_url"])

    if not transcription:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
            text=constants.ERROR_MESSAGE,
        )
        return

    # Update message to "Compiling recipe..."
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=processing_message.message_id,
        text="Compiling recipe...",
    )
    gpt_api.set_language(lang)
    recipe = gpt_api.assemble_recipe(reel_info["description"], transcription)

    if not recipe:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
            text=constants.ERROR_MESSAGE,
        )
        return

    # Delete the "Processing..." message
    await processing_message.delete()

    reel_link = message.text
    # Cache the recipe by instagram link
    recipes[lang][reel_link] = recipe
    logging.info(f"Cached recipe with link: {hash(recipe)} for language: {lang}")

    # Save reel link to the context of the user data
    context.user_data["reel_link"] = reel_link

    # Send final recipe
    await send_recipe_with_translation_button(update, context, recipe, lang)


# Callback query handler
async def handle_translation_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    # Handle ghost clicks
    if query.data == "none":
        return

    reel_link = context.user_data.get("reel_link")

    # Skip request if recipe translation is already processing
    if processing.get(reel_link, False):
        logging.info(f"Recipe translation for {reel_link} is already processing.")
        return
    else:
        processing[reel_link] = True

    # Temporary keyboard with loading symbol
    loading_keyboard = [[InlineKeyboardButton("Loading...", callback_data="none")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(loading_keyboard))

    source_language = "en" if query.data == TRANSLATE_TO_RUSSIAN else "ru"
    target_language = "ru" if query.data == TRANSLATE_TO_RUSSIAN else "en"

    # Check the cache for existance of translation for this recipe
    if reel_link in recipes[target_language]:
        logging.info(f"Found recipe with link: {reel_link}")
        translated_text = recipes[target_language][reel_link]
    else:
        logging.info(f"Recipe translation with link {reel_link} for {target_language} not found!")
        translated_text = gpt_api.translate(query.message.text, source_language, target_language)
        recipes[target_language][reel_link] = translated_text

    language_label = "Russian" if source_language == "ru" else "English"
    flag = RUSSIAN_FLAG if source_language == "ru" else AMERICAN_FLAG
    callback_data = TRANSLATE_TO_RUSSIAN if source_language == "ru" else TRANSLATE_TO_ENGLISH
    keyboard = [
        [
            InlineKeyboardButton(
                f"Translate to {language_label} {flag}",
                callback_data=callback_data,
            )
        ]
    ]
    await query.edit_message_text(
        text=translated_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
    )

    processing[reel_link] = False


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).concurrent_updates(True).build()

    start_handler = CommandHandler("start", start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    translation_handler = CallbackQueryHandler(handle_translation_button)
    application.add_handler(translation_handler)

    application.run_polling()
