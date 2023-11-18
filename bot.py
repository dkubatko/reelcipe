import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from api.instagram import InstagramAPI
from api.vtt import VideoToText
from api.chatgpt import GPTConversation
import api.constants as constants
from langdetect import detect
from config import TELEGRAM_BOT_TOKEN

RUSSIAN_FLAG = '\U0001F1F7\U0001F1FA'
AMERICAN_FLAG = '\U0001F1FA\U0001F1F8'

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO
)

# Constants for translation
TRANSLATE_TO_RUSSIAN, TRANSLATE_TO_ENGLISH = 'translate_to_ru', 'translate_to_en'

instagram_api = InstagramAPI()
vtt_api = VideoToText()
gpt_api = GPTConversation()

# Cache for recipies to avoid redundant translations
recipes = {
   'ru': {},
   'en': {},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=constants.START_MESSAGE)

# Function to send recipe with inline keyboard
async def send_recipe_with_translation_button(update: Update, context: ContextTypes.DEFAULT_TYPE, recipe, language):
    if language == 'en':
      keyboard = [[InlineKeyboardButton(f"Translate to Russian {RUSSIAN_FLAG}", callback_data=TRANSLATE_TO_RUSSIAN)]]
    else:
      keyboard = [[InlineKeyboardButton(f"Translate to English {AMERICAN_FLAG}", callback_data=TRANSLATE_TO_ENGLISH)]]
       
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=recipe, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def process_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if "instagram.com/reel/" not in message.text:
      await context.bot.send_message(chat_id=update.effective_chat.id, text=constants.INVALID_MESSAGE)
      return

    processing_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing...")

    # Update message to "Watching the video..."
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_message.message_id, text="Watching the video...")
    reel_info = instagram_api.get_reel_info(message.text)

    if not reel_info:
      await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_message.message_id, text=constants.ERROR_MESSAGE)
      return
    
    # Determine language of the reel
    lang = detect(reel_info['description'])
    logging.info(f"Determined language: {lang}")

    if lang not in ['en', 'ru']:
      await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_message.message_id, text=constants.ERROR_MESSAGE)
      return

    # Update message to "Transcribing..."
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_message.message_id, text="Transcribing...")
    vtt_api.set_language(lang)
    transcription = vtt_api.transcribe_video(reel_info['video_url'])

    if not transcription:
      await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_message.message_id, text=constants.ERROR_MESSAGE)
      return

    # Update message to "Compiling recipe..."
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_message.message_id, text="Compiling recipe...")
    gpt_api.set_language(lang)
    recipe = gpt_api.assemble_recipe(reel_info['description'], transcription)

    if not recipe:
      await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=processing_message.message_id, text=constants.ERROR_MESSAGE)
      return

    # Delete the "Processing..." message
    await processing_message.delete()

    reel_link = message.text
    # Cache the recipe by instagram link
    recipes[lang][reel_link] = recipe
    logging.info(f"Cached recipe with link: {hash(recipe)} for language: {lang}")

    # Save reel link to the context of the user data
    context.user_data['reel_link'] = reel_link

    # Send final recipe
    await send_recipe_with_translation_button(update, context, recipe, lang)


# Callback query handler
async def handle_translation_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    reel_link = context.user_data.get('reel_link')

    # Temporary keyboard with loading symbol
    loading_keyboard = [[InlineKeyboardButton("Loading...", callback_data="none")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(loading_keyboard))
    
    if query.data == TRANSLATE_TO_RUSSIAN:
        # Check the cache for existance of translation for this recipe
        if (reel_link in recipes['ru']):
          logging.info(f"Found recipe with link: {reel_link}")
          translated_text = recipes['ru'][reel_link]
        else:
          logging.info(f"Recipe with link: {reel_link} not found!")
          translated_text = gpt_api.translate(query.message.text, 'English', 'Russian')
          recipes['ru'][reel_link] = translated_text

        keyboard = [[InlineKeyboardButton(f"Translate to English {AMERICAN_FLAG}", callback_data=TRANSLATE_TO_ENGLISH)]]
        await query.edit_message_text(text=translated_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='MarkdownV2')

    elif query.data == TRANSLATE_TO_ENGLISH:
        # Check the cache for existance of translation for this recipe
        if (reel_link in recipes['en']):
          logging.info(f"Found recipe with link: {reel_link}")
          translated_text = recipes['en'][reel_link]
        else:       
          logging.info(f"Recipe with link: {reel_link} not found!")
          translated_text = gpt_api.translate(query.message.text, 'Russian', 'English')
          recipes['en'][reel_link] = translated_text

        keyboard = [[InlineKeyboardButton(f"Translate to Russian {RUSSIAN_FLAG}", callback_data=TRANSLATE_TO_RUSSIAN)]]
        await query.edit_message_text(text=translated_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='MarkdownV2')


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), process_reel)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)

    translation_handler = CallbackQueryHandler(handle_translation_button)
    application.add_handler(translation_handler)
    
    application.run_polling()
