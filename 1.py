import os
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes

# Состояния для диалога
SELECT_FILTER, SEND_IMAGE = range(2)

# Замените на токен вашего бота
token = 'ваш токен'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Отправить изображение", callback_data='send_image')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)
    return SEND_IMAGE

async def send_filter_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Бинаризация", callback_data='binarize')],
        [InlineKeyboardButton("Размытие", callback_data='blur')],
        [InlineKeyboardButton("Собственное размытие", callback_data='gaussian_blur')],
        [InlineKeyboardButton("Усиление краев", callback_data='edge_enhance')],
        [InlineKeyboardButton("Усиление цвета", callback_data='color_enhance')],
        [InlineKeyboardButton("Серый", callback_data='grayscale')],
        [InlineKeyboardButton("Контраст", callback_data='contrast')],
        [InlineKeyboardButton("Яркость", callback_data='brightness')],
        [InlineKeyboardButton("Фильтр 'Восторг'", callback_data='sharpen')],
        [InlineKeyboardButton("Размер 4:3", callback_data='resize_4_3')],
        [InlineKeyboardButton("Размер 16:9", callback_data='resize_16_9')],
        [InlineKeyboardButton("Инверсия цветов", callback_data='invert')],
        [InlineKeyboardButton("Добавить рамку", callback_data='add_border')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите фильтр:', reply_markup=reply_markup)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['photo'] = update.message.photo[-1].file_id
    await send_filter_options(update, context)
    return SELECT_FILTER

async def filter_image(file_id, context):
    # Получаем изображение из Telegram
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive('temp_image.jpg')

    img = Image.open('temp_image.jpg')
    img_processed = img

    # Применяем фильтры
    filter_type = context.user_data.get('filter_type', 'binarize')  # Пример, установить значение фильтра
    if filter_type == 'binarize':
        img_processed = img.convert("L").point(lambda x: 0 if x < 128 else 255, '1')
    elif filter_type == 'blur':
        img_processed = img.filter(ImageFilter.BLUR)
    elif filter_type == 'gaussian_blur':
        img_processed = img.filter(ImageFilter.GaussianBlur(radius=5))
    elif filter_type == 'edge_enhance':
        img_processed = img.filter(ImageFilter.EDGE_ENHANCE)
    elif filter_type == 'color_enhance':
        enhancer = ImageEnhance.Color(img)
        img_processed = enhancer.enhance(1.5)
    elif filter_type == 'grayscale':
        img_processed = img.convert("L")
    elif filter_type == 'contrast':
        enhancer = ImageEnhance.Contrast(img)
        img_processed = enhancer.enhance(1.5)
    elif filter_type == 'brightness':
        enhancer = ImageEnhance.Brightness(img)
        img_processed = enhancer.enhance(1.5)
    elif filter_type == 'sharpen':
        img_processed = img.filter(ImageFilter.SHARPEN)
    elif filter_type == 'resize_4_3':
        img_processed = img.resize((800, 600))  # 4:3 aspect ratio
    elif filter_type == 'resize_16_9':
        img_processed = img.resize((1280, 720))  # 16:9 aspect ratio
    elif filter_type == 'invert':
        img_processed = ImageOps.invert(img)
    elif filter_type == 'add_border':
        img_processed = ImageOps.expand(img, border=50, fill='black')

    # Сохраняем обработанное изображение
    img_processed.save('processed_image.png')
    return 'processed_image.png'

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'send_image':
        await query.message.reply_text("Отправьте изображение для обработки.")
        return SEND_IMAGE
    elif query.data == 'cancel':
        await query.message.reply_text('Обработка отменена.')
        return ConversationHandler.END

    file_id = context.user_data['photo']
    filter_type = query.data
    context.user_data['filter_type'] = filter_type  # Сохраняем тип фильтра

    # Обработка изображения с выбранным фильтром
    img_path = await filter_image(file_id, context)

    # Отправка обработанного изображения обратно пользователю
    await context.bot.send_photo(chat_id=query.message.chat_id, photo=open(img_path, 'rb'))
    os.remove('temp_image.jpg')
    os.remove(img_path)

    await query.message.reply_text('Обработка завершена! Отправьте новое изображение для обработки.')

    return SEND_IMAGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Обработка отменена.')
    return ConversationHandler.END

def main() -> None:
    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SEND_IMAGE: [MessageHandler(filters.PHOTO, handle_image), CallbackQueryHandler(button)],
            SELECT_FILTER: [CallbackQueryHandler(button)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
