import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования для Termux
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_arina.log')
    ]
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.environ.get('TOKEN') or "8277567431:AAFXaAZ-t0WygzAsOSIajCfYlDTFm92fJdQ"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Хранение данных в файле для Termux
DATA_FILE = "bot_data.json"

def load_user_data() -> Dict[str, Any]:
    """Загружает данные пользователей из файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_data(data: Dict[str, Any]):
    """Сохраняет данные пользователей в файл"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

# Загружаем данные при старте
users_data = load_user_data()

# Состояния
class Form(StatesGroup):
    name = State()
    age = State()
    main_menu = State()
    psychology_test = State()
    diary = State()
    diary_q1 = State()
    diary_q2 = State()
    diary_q3 = State()

# Цитаты
quotes = [
    "Жизнь — это то, что с тобой происходит, пока ты строишь планы. — Джон Леннон",
    "Единственный способ сделать великую работу — любить то, что делаешь. — Стив Джобс",
    "Будь тем изменением, которое ты хочешь видеть в мире. — Махатма Ганди",
    "Не так важно, как медленно ты идешь, если ты не останавливаешься. — Конфуций",
    "Счастье — это не что-то готовое. Оно приходит от ваших собственных действий. — Далай-лама",
    "Лучший способ предсказать будущее — создать его. — Абрахам Линкольн",
    "Успех — это способность переходить от одной неудачи к другой без потери энтузиазма. — Уинстон Черчилль",
    "Мы — то, что мы делаем постоянно. Совершенство, значит, не действие, а привычка. — Аристотель",
    "Ваше время ограничено, не тратьте его, живя чужой жизнью. — Стив Джобс",
    "Сложнее всего начать действовать, все остальное зависит только от упорства. — Амелия Эрхарт"
]

# Вопросы психологического теста
psychology_questions = [
    "Как вы обычно реагируете на стрессовые ситуации?",
    "Насколько легко вы заводите новые знакомства?",
    "Как часто вы чувствуете беспокойство без видимой причины?",
    "Насколько вы довольны своей жизнью?",
    "Как вы относитесь к изменениям в жизни?",
    "Насколько вы уверены в себе?",
    "Как вы справляетесь с неудачами?",
    "Насколько важно для вас мнение окружающих?",
    "Как часто вы занимаетесь самоанализом?",
    "Насколько вы оптимистично смотрите в будущее?"
]

# Вопросы для дневника самоконтроля
diary_questions = [
    {
        "id": "mood",
        "question": "Как вы оцениваете свое настроение сегодня?",
        "options": ["Отлично 😊", "Хорошо 🙂", "Нормально 😐", "Плохо 😔", "Ужасно 😞"]
    },
    {
        "id": "productivity", 
        "question": "Насколько продуктивным был ваш день?",
        "options": ["Очень продуктивный", "Довольно продуктивный", "Средне", "Мало продуктивный", "Непродуктивный"]
    },
    {
        "id": "sleep",
        "question": "Как вы оцениваете качество вашего сна сегодня?",
        "options": ["Отличный сон 😴", "Хороший сон 💤", "Средний сон 🛌", "Плохой сон 😫", "Бессонница 🥱"]
    }
]

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    if user_id not in users_data:
        users_data[user_id] = {
            "name": "",
            "age": 0,
            "test_results": [],
            "diary_entries": []
        }
        save_user_data(users_data)
    
    await message.answer("Привет! Добро пожаловать в бота для самопознания и развития! 😊")
    
    await asyncio.sleep(2)
    await message.answer("Как тебя зовут?")
    await state.set_state(Form.name)

# Получение имени
@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    name = message.text
    users_data[user_id]["name"] = name
    save_user_data(users_data)
    
    await state.update_data(name=name)
    await message.answer(f"Приятно познакомиться, {name}! Сколько тебе лет?")
    await state.set_state(Form.age)

# Получение возраста
@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    age = message.text
    
    try:
        age_int = int(age)
        users_data[user_id]["age"] = age_int
        save_user_data(users_data)
        await state.update_data(age=age_int)
        
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🧠 Психотест")],
                [types.KeyboardButton(text="📓 Заполнить дневник самоконтроля")],
                [types.KeyboardButton(text="💭 Цитата дня")],
                [types.KeyboardButton(text="📊 Моя статистика")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(f"Отлично, {users_data[user_id]['name']}! Выбери, что тебя интересует:", reply_markup=keyboard)
        await state.set_state(Form.main_menu)
        
    except ValueError:
        await message.answer("Пожалуйста, введите возраст числом:")

# Обработка выбора в главном меню
@dp.message(Form.main_menu)
async def main_menu(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    if message.text == "🧠 Психотест":
        await message.answer("Начинаем психологический тест! Ответьте на 10 вопросов.")
        await ask_psychology_question(message, state, 0)
        
    elif message.text == "📓 Заполнить дневник самоконтроля":
        if "current_diary" not in users_data[user_id]:
            users_data[user_id]["current_diary"] = []
        await message.answer("Начнем заполнение дневника самоконтроля!")
        await ask_diary_question(message, state, 0)
        
    elif message.text == "💭 Цитата дня":
        await show_quote(message, user_id)
        
    elif message.text == "📊 Моя статистика":
        await show_statistics(message, user_id)

# Функция показа статистики
async def show_statistics(message: Message, user_id: str):
    user_data = users_data.get(user_id, {})
    
    if not user_data.get("test_results") and not user_data.get("diary_entries"):
        await message.answer("У вас пока нет данных для статистики. Пройдите тест или заполните дневник!")
        return
    
    stats_text = f"📊 Статистика пользователя {user_data.get('name', '')}\n\n"
    
    # Статистика психотестов
    if user_data.get("test_results"):
        total_tests = len(user_data["test_results"])
        last_test = user_data["test_results"][-1]["date"] if user_data["test_results"] else "Нет данных"
        
        stats_text += "🧠 **Статистика психотестов:**\n"
        stats_text += f"• Всего пройдено тестов: {total_tests}\n"
        stats_text += f"• Последний тест: {last_test}\n\n"
    else:
        stats_text += "🧠 **Психотесты:** Нет данных\n\n"
    
    # Статистика дневника
    if user_data.get("diary_entries"):
        total_entries = len(user_data["diary_entries"])
        last_entry = user_data["diary_entries"][-1]["date"] if user_data["diary_entries"] else "Нет данных"
        
        # Анализ настроения
        moods = []
        sleep_quality = []
        for entry in user_data["diary_entries"]:
            for answer in entry.get("answers", []):
                if "настроение" in answer.get("question", "").lower():
                    moods.append(answer.get("answer", ""))
                elif "сон" in answer.get("question", "").lower():
                    sleep_quality.append(answer.get("answer", ""))
        
        # Самые частые ответы
        def most_common(lst):
            return max(set(lst), key=lst.count) if lst else "Нет данных"
        
        stats_text += "📓 **Статистика дневника:**\n"
        stats_text += f"• Всего записей: {total_entries}\n"
        stats_text += f"• Самое частое настроение: {most_common(moods)}\n"
        stats_text += f"• Частое качество сна: {most_common(sleep_quality)}\n"
        stats_text += f"• Последняя запись: {last_entry}\n"
        
        # Советы по сну
        if sleep_quality:
            bad_sleep_count = sleep_quality.count("Плохой сон 😫") + sleep_quality.count("Бессонница 🥱")
            if bad_sleep_count > len(sleep_quality) * 0.5:  # Если больше 50% плохого сна
                stats_text += "\n💡 **Совет:** Попробуйте улучшить качество сна:\n"
                stats_text += "• Соблюдайте режим сна\n"
                stats_text += "• Избегайте экранов перед сном\n"
                stats_text += "• Создайте комфортную атмосферу\n"
    else:
        stats_text += "📓 **Дневник:** Нет данных\n"
    
    await message.answer(stats_text)

# Функция показа цитаты
async def show_quote(message: Message, user_id: str):
    quote = random.choice(quotes)
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Следующая цитата →", callback_data="next_quote")]
        ]
    )
    
    await message.answer(f"💭 {quote}", reply_markup=keyboard)

# Обработка следующей цитаты
@dp.callback_query(lambda c: c.data == "next_quote")
async def next_quote(callback_query: CallbackQuery):
    quote = random.choice(quotes)
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Следующая цитата →", callback_data="next_quote")]
        ]
    )
    
    await callback_query.message.edit_text(f"💭 {quote}", reply_markup=keyboard)
    await callback_query.answer()

# Функция для задавания вопросов психологического теста
async def ask_psychology_question(message: Message, state: FSMContext, question_index: int):
    if question_index < len(psychology_questions):
        question_text = psychology_questions[question_index]
        
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Отлично/Всегда")],
                [types.KeyboardButton(text="Хорошо/Часто")],
                [types.KeyboardButton(text="Нормально/Иногда")],
                [types.KeyboardButton(text="Плохо/Редко")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(f"Вопрос {question_index + 1}/{len(psychology_questions)}:\n\n{question_text}", reply_markup=keyboard)
        await state.update_data(current_question=question_index)
        await state.set_state(Form.psychology_test)
    else:
        await finish_psychology_test(message, state)

# Обработка ответов психологического теста
@dp.message(Form.psychology_test)
async def process_psychology_answer(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = await state.get_data()
    question_index = data.get("current_question", 0)
    
    if "current_test" not in users_data[user_id]:
        users_data[user_id]["current_test"] = []
    
    users_data[user_id]["current_test"].append({
        "question": psychology_questions[question_index],
        "answer": message.text
    })
    
    await ask_psychology_question(message, state, question_index + 1)

# Завершение психологического теста
async def finish_psychology_test(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    current_test = users_data[user_id].get("current_test", [])
    
    # Сохраняем результат теста
    test_result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answers": current_test,
        "total_questions": len(current_test)
    }
    
    if "test_results" not in users_data[user_id]:
        users_data[user_id]["test_results"] = []
    
    users_data[user_id]["test_results"].append(test_result)
    save_user_data(users_data)
    
    # Формируем отчет
    report = f"🎉 Тест завершен!\n\n"
    report += f"📊 Вы ответили на {len(current_test)} вопросов.\n\n"
    report += "💭 Основные выводы:\n"
    
    positive_count = sum(1 for answer in current_test if "Отлично" in answer["answer"] or "Хорошо" in answer["answer"])
    percentage = (positive_count / len(current_test)) * 100 if current_test else 0
    
    if percentage >= 70:
        report += "У вас отличные психологические показатели! 🎯\n"
        report += "Продолжайте заниматься саморазвитием."
    elif percentage >= 40:
        report += "Ваши показатели в норме. 📈\n"
        report += "Есть куда расти, но вы на правильном пути."
    else:
        report += "Есть над чем поработать. 🔧\n"
        report += "Рекомендуется уделять больше внимания психологическому здоровью."
    
    # Возвращаем основную клавиатуру
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🧠 Психотест")],
            [types.KeyboardButton(text="📓 Заполнить дневник самоконтроля")],
            [types.KeyboardButton(text="💭 Цитата дня")],
            [types.KeyboardButton(text="📊 Моя статистика")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(report, reply_markup=keyboard)
    await state.set_state(Form.main_menu)

# Функция для задавания вопросов дневника
async def ask_diary_question(message: Message, state: FSMContext, question_index: int):
    if question_index < len(diary_questions):
        question_data = diary_questions[question_index]
        question_text = question_data["question"]
        options = question_data["options"]
        
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=option)] for option in options],
            resize_keyboard=True
        )
        
        await message.answer(f"Вопрос {question_index + 1}/{len(diary_questions)}:\n\n{question_text}", reply_markup=keyboard)
        
        if question_index == 0:
            await state.set_state(Form.diary_q1)
        elif question_index == 1:
            await state.set_state(Form.diary_q2)
        elif question_index == 2:
            await state.set_state(Form.diary_q3)
            
        await state.update_data(current_diary_question=question_index)
    else:
        await finish_diary(message, state)

# Обработка ответов дневника
@dp.message(Form.diary_q1)
async def process_diary_q1(message: Message, state: FSMContext):
    await process_diary_answer(message, state, 0)

@dp.message(Form.diary_q2)
async def process_diary_q2(message: Message, state: FSMContext):
    await process_diary_answer(message, state, 1)

@dp.message(Form.diary_q3)
async def process_diary_q3(message: Message, state: FSMContext):
    await process_diary_answer(message, state, 2)

async def process_diary_answer(message: Message, state: FSMContext, question_index: int):
    user_id = str(message.from_user.id)
    answer_text = message.text
    question_data = diary_questions[question_index]
    
    # Проверяем, что ответ соответствует одному из вариантов
    valid_answers = question_data["options"]
    if answer_text not in valid_answers:
        await message.answer(f"Пожалуйста, выберите один из предложенных вариантов:")
        return
    
    # Сохраняем ответ
    if "current_diary" not in users_data[user_id]:
        users_data[user_id]["current_diary"] = []
    
    users_data[user_id]["current_diary"].append({
        "id": question_data["id"],
        "question": question_data["question"],
        "answer": answer_text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Задаем следующий вопрос или завершаем
    await ask_diary_question(message, state, question_index + 1)

# Завершение заполнения дневника
async def finish_diary(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    diary_entry = users_data[user_id].get("current_diary", [])
    
    # Сохраняем запись дневника
    diary_record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answers": diary_entry
    }
    
    if "diary_entries" not in users_data[user_id]:
        users_data[user_id]["diary_entries"] = []
    
    users_data[user_id]["diary_entries"].append(diary_record)
    save_user_data(users_data)
    
    # Очищаем текущий дневник
    users_data[user_id]["current_diary"] = []
    
    # Формируем сводку
    summary = "📓 Дневник заполнен!\n\n"
    summary += "Ваши ответы:\n\n"
    
    for entry in diary_entry:
        summary += f"• {entry['question']}\n"
        summary += f"  → {entry['answer']}\n\n"
    
    # Анализ сна (новый третий вопрос)
    sleep_answer = next((item for item in diary_entry if item["id"] == "sleep"), None)
    if sleep_answer:
        sleep_text = sleep_answer["answer"]
        if "Отличный" in sleep_text or "Хороший" in sleep_text:
            summary += "💤 **Качество сна:** Отличное! Вы хорошо отдохнули.\n"
        elif "Средний" in sleep_text:
            summary += "💤 **Качество сна:** Среднее. Попробуйте улучшить режим.\n"
        else:
            summary += "💤 **Качество сна:** Требует улучшения. Рекомендации:\n"
            summary += "   - Ложитесь спать в одно время\n"
            summary += "   - Проветривайте комнату перед сном\n"
            summary += "   - Избегайте кофеина вечером\n"
    
    summary += "\n✅ Данные сохранены. Вы можете просмотреть статистику в меню."
    
    # Возвращаем основную клавиатуру
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🧠 Психотест")],
            [types.KeyboardButton(text="📓 Заполнить дневник самоконтроля")],
            [types.KeyboardButton(text="💭 Цитата дня")],
            [types.KeyboardButton(text="📊 Моя статистика")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(summary, reply_markup=keyboard)
    await state.set_state(Form.main_menu)

# Команда для просмотра данных
@dp.message(Command("data"))
async def cmd_data(message: Message):
    user_id = str(message.from_user.id)
    
    if user_id in users_data:
        test_count = len(users_data[user_id].get("test_results", []))
        diary_count = len(users_data[user_id].get("diary_entries", []))
        
        response = f"📁 Ваши данные:\n"
        response += f"• Психотестов пройдено: {test_count}\n"
        response += f"• Записей в дневнике: {diary_count}\n"
        response += f"• Имя: {users_data[user_id].get('name', 'Не указано')}\n"
        response += f"• Возраст: {users_data[user_id].get('age', 'Не указан')}\n\n"
        response += "Файл данных: bot_data.json"
    else:
        response = "У вас еще нет сохраненных данных."
    
    await message.answer(response)

# Команда для сброса данных (осторожно!)
@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Да, сбросить", callback_data="reset_confirm"),
                types.InlineKeyboardButton(text="Отмена", callback_data="reset_cancel")
            ]
        ]
    )
    
    await message.answer("⚠️ Вы уверены, что хотите сбросить все данные? Это действие нельзя отменить!", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data in ["reset_confirm", "reset_cancel"])
async def handle_reset(callback_query: CallbackQuery):
    user_id = str(callback_query.from_user.id)
    
    if callback_query.data == "reset_confirm":
        if user_id in users_data:
            # Сохраняем только имя и возраст
            name = users_data[user_id].get("name", "")
            age = users_data[user_id].get("age", 0)
            users_data[user_id] = {
                "name": name,
                "age": age,
                "test_results": [],
                "diary_entries": []
            }
            save_user_data(users_data)
            await callback_query.message.answer("✅ Все данные сброшены, кроме имени и возраста.")
        else:
            await callback_query.message.answer("У вас нет сохраненных данных для сброса.")
    else:
        await callback_query.message.answer("❌ Сброс данных отменен.")
    
    await callback_query.answer()

# Главная функция с обработкой ошибок
async def main():
    logger.info("=" * 50)
    logger.info("Запуск бота Арины для Termux...")
    logger.info(f"ID файла данных: {DATA_FILE}")
    logger.info("=" * 50)
    
    try:
        # Удаляем вебхук на всякий случай
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.info("Попробуйте перезапустить через 10 секунд...")
        await asyncio.sleep(10)
        # Попробуем перезапуститься
        await main()

if __name__ == "__main__":
    # Информация о системе
    logger.info(f"Python версия: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Файл данных существует: {os.path.exists(DATA_FILE)}")
    
    # Автоматическое сохранение данных при выходе
    import atexit
    atexit.register(lambda: save_user_data(users_data))
    
    # Бесконечный перезапуск при ошибках
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем (Ctrl+C)")
            # Сохраняем данные перед выходом
            save_user_data(users_data)
            break
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            # Сохраняем данные перед перезапуском
            save_user_data(users_data)
            import time
            time.sleep(30)  # Ждем 30 секунд перед перезапуском
