import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import io
from collections import Counter

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "8277567431:AAFXaAZ-t0WygzAsOSIajCfYlDTFm92fJdQ"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Хранение данных пользователей
users_data = {}

# Состояния для FSM
class Form(StatesGroup):
    name = State()
    age = State()
    main_menu = State()
    psychology_test = State()
    diary = State()
    diary_q1 = State()
    diary_q2 = State()
    diary_q3 = State()
    statistics = State()

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
current_quote_index = {}

# Вопросы психологического теста
psychology_questions = [
    {
        "question": "Как вы обычно реагируете на стрессовые ситуации?",
        "options": ["Паникую", "Сохраняю спокойствие", "Ищу решение проблемы", "Избегаю ситуации"],
        "weights": [1, 4, 5, 2]  # Веса ответов для подсчета баллов
    },
    {
        "question": "Насколько легко вы заводите новые знакомства?",
        "options": ["Очень легко", "Довольно легко", "С трудом", "Стараюсь избегать"],
        "weights": [5, 4, 2, 1]
    },
    {
        "question": "Как часто вы чувствуете беспокойство без видимой причины?",
        "options": ["Часто", "Иногда", "Редко", "Практически никогда"],
        "weights": [1, 2, 4, 5]
    },
    {
        "question": "Насколько вы довольны своей жизнью?",
        "options": ["Полностью доволен", "В основном доволен", "Нейтрально", "Не доволен"],
        "weights": [5, 4, 3, 1]
    },
    {
        "question": "Как вы относитесь к изменениям в жизни?",
        "options": ["Приветствую", "Принимаю с осторожностью", "Сопротивляюсь", "Боюсь"],
        "weights": [5, 4, 2, 1]
    },
    {
        "question": "Насколько вы уверены в себе?",
        "options": ["Очень уверен", "Довольно уверен", "Не очень уверен", "Не уверен совсем"],
        "weights": [5, 4, 2, 1]
    },
    {
        "question": "Как вы справляетесь с неудачами?",
        "options": ["Анализирую и делаю выводы", "Расстраиваюсь, но продолжаю", "Долго переживаю", "Сдаюсь"],
        "weights": [5, 4, 2, 1]
    },
    {
        "question": "Насколько важно для вас мнение окружающих?",
        "options": ["Очень важно", "Довольно важно", "Не очень важно", "Совсем не важно"],
        "weights": [2, 3, 4, 5]
    },
    {
        "question": "Как часто вы занимаетесь самоанализом?",
        "options": ["Регулярно", "Иногда", "Редко", "Никогда"],
        "weights": [5, 4, 2, 1]
    },
    {
        "question": "Насколько вы оптимистично смотрите в будущее?",
        "options": ["Очень оптимистично", "Скорее оптимистично", "Скорее пессимистично", "Пессимистично"],
        "weights": [5, 4, 2, 1]
    }
]

# Вопросы для дневника самоконтроля
diary_questions = [
    {
        "question": "Как вы оцениваете свое настроение сегодня?",
        "options": ["Отлично 😊", "Хорошо 🙂", "Нормально 😐", "Плохо 😔", "Ужасно 😞"],
        "values": [5, 4, 3, 2, 1]
    },
    {
        "question": "Насколько продуктивным был ваш день?",
        "options": ["Очень продуктивный", "Довольно продуктивный", "Средне", "Мало продуктивный", "Непродуктивный"],
        "values": [5, 4, 3, 2, 1]
    },
    {
        "question": "Как вы справлялись со стрессом сегодня?",
        "options": ["Отлично", "Хорошо", "Нормально", "Плохо", "Не справлялся"],
        "values": [5, 4, 3, 2, 1]
    }
]

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {
            "test_results": [],
            "diary_entries": [],
            "name": "",
            "age": 0
        }
    
    await message.answer("Привет! Добро пожаловать в бота для самопознания и развития! 😊")
    
    await asyncio.sleep(3)
    await message.answer("Как тебя зовут?")
    await state.set_state(Form.name)

# Получение имени
@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text
    users_data[user_id]["name"] = name
    
    await state.update_data(name=name)
    await message.answer(f"Приятно познакомиться, {name}! Сколько тебе лет?")
    await state.set_state(Form.age)

# Получение возраста
@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    user_id = message.from_user.id
    age = message.text
    
    try:
        age_int = int(age)
        users_data[user_id]["age"] = age_int
        await state.update_data(age=age_int)
        
        # Создаем клавиатуру с основным меню
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
    user_id = message.from_user.id
    
    if message.text == "🧠 Психотест":
        users_data[user_id]["current_test"] = []
        await message.answer("Начинаем психологический тест! Ответьте на 10 вопросов.")
        await ask_psychology_question(message, state, 0)
        
    elif message.text == "📓 Заполнить дневник самоконтроля":
        users_data[user_id]["current_diary"] = []
        await message.answer("Начнем заполнение дневника самоконтроля!")
        await ask_diary_question(message, state, 0)
        
    elif message.text == "💭 Цитата дня":
        await show_quote(message, user_id)
        
    elif message.text == "📊 Моя статистика":
        await show_statistics(message, user_id)

# Функция показа статистики
async def show_statistics(message: Message, user_id: int):
    user_data = users_data.get(user_id, {})
    
    if not user_data.get("test_results") and not user_data.get("diary_entries"):
        await message.answer("У вас пока нет данных для статистики. Пройдите тест или заполните дневник!")
        return
    
    stats_text = f"📊 Статистика пользователя {user_data.get('name', '')}\n\n"
    
    # Статистика психотестов
    if user_data.get("test_results"):
        test_stats = await calculate_test_statistics(user_data["test_results"])
        stats_text += "🧠 **Статистика психотестов:**\n"
        stats_text += f"• Всего пройдено тестов: {test_stats['total_tests']}\n"
        stats_text += f"• Средний балл: {test_stats['average_score']:.1f}/50\n"
        stats_text += f"• Лучший результат: {test_stats['best_score']}/50\n"
        stats_text += f"• Последний тест: {test_stats['last_test_date']}\n"
        
        # Создаем график прогресса тестов
        if len(test_stats['scores_history']) > 1:
            chart = await create_test_progress_chart(test_stats['scores_history'])
            await message.answer_photo(
                BufferedInputFile(chart.getvalue(), filename="test_progress.png"),
                caption=stats_text
            )
        else:
            await message.answer(stats_text)
    else:
        stats_text += "🧠 **Психотесты:** Нет данных\n\n"
    
    # Статистика дневника
    if user_data.get("diary_entries"):
        diary_stats = await calculate_diary_statistics(user_data["diary_entries"])
        diary_text = "\n📓 **Статистика дневника:**\n"
        diary_text += f"• Всего записей: {diary_stats['total_entries']}\n"
        diary_text += f"• Среднее настроение: {diary_stats['avg_mood']:.1f}/5\n"
        diary_text += f"• Средняя продуктивность: {diary_stats['avg_productivity']:.1f}/5\n"
        diary_text += f"• Средний уровень стресса: {diary_stats['avg_stress']:.1f}/5\n"
        diary_text += f"• Самое частое настроение: {diary_stats['most_common_mood']}\n"
        diary_text += f"• Последняя запись: {diary_stats['last_entry_date']}\n"
        
        # Создаем график настроения
        if len(diary_stats['mood_history']) > 1:
            chart = await create_mood_chart(diary_stats['mood_history'], diary_stats['productivity_history'])
            await message.answer_photo(
                BufferedInputFile(chart.getvalue(), filename="mood_chart.png"),
                caption=diary_text
            )
        else:
            await message.answer(diary_text)
    else:
        await message.answer(stats_text + "\n📓 **Дневник:** Нет данных")

# Расчет статистики тестов
async def calculate_test_statistics(test_results):
    stats = {
        "total_tests": len(test_results),
        "scores": [],
        "scores_history": [],
        "dates": []
    }
    
    for test in test_results:
        stats["scores"].append(test["total_score"])
        stats["scores_history"].append(test["total_score"])
        stats["dates"].append(test["date"])
    
    if stats["scores"]:
        stats["average_score"] = sum(stats["scores"]) / len(stats["scores"])
        stats["best_score"] = max(stats["scores"])
        stats["last_test_date"] = stats["dates"][-1] if stats["dates"] else "Нет данных"
    else:
        stats["average_score"] = 0
        stats["best_score"] = 0
        stats["last_test_date"] = "Нет данных"
    
    return stats

# Расчет статистики дневника
async def calculate_diary_statistics(diary_entries):
    stats = {
        "total_entries": len(diary_entries),
        "moods": [],
        "productivity": [],
        "stress": [],
        "mood_history": [],
        "productivity_history": [],
        "dates": []
    }
    
    for entry in diary_entries:
        for answer in entry["answers"]:
            if "настроение" in answer["question"].lower():
                stats["moods"].append(answer["numeric_value"])
                stats["mood_history"].append(answer["numeric_value"])
            elif "продуктив" in answer["question"].lower():
                stats["productivity"].append(answer["numeric_value"])
                stats["productivity_history"].append(answer["numeric_value"])
            elif "стресс" in answer["question"].lower():
                stats["stress"].append(answer["numeric_value"])
        
        stats["dates"].append(entry["date"])
    
    if stats["moods"]:
        stats["avg_mood"] = sum(stats["moods"]) / len(stats["moods"])
        stats["avg_productivity"] = sum(stats["productivity"]) / len(stats["productivity"]) if stats["productivity"] else 0
        stats["avg_stress"] = sum(stats["stress"]) / len(stats["stress"]) if stats["stress"] else 0
        
        # Определяем самое частое настроение
        mood_counter = Counter(stats["moods"])
        most_common_value = mood_counter.most_common(1)[0][0]
        
        # Преобразуем числовое значение в текстовое
        mood_map = {
            5: "Отлично 😊",
            4: "Хорошо 🙂",
            3: "Нормально 😐",
            2: "Плохо 😔",
            1: "Ужасно 😞"
        }
        stats["most_common_mood"] = mood_map.get(most_common_value, "Нет данных")
        stats["last_entry_date"] = stats["dates"][-1] if stats["dates"] else "Нет данных"
    else:
        stats["avg_mood"] = 0
        stats["avg_productivity"] = 0
        stats["avg_stress"] = 0
        stats["most_common_mood"] = "Нет данных"
        stats["last_entry_date"] = "Нет данных"
    
    return stats

# Создание графика прогресса тестов
async def create_test_progress_chart(scores):
    plt.figure(figsize=(10, 6))
    
    # Создаем данные для графика
    x = list(range(1, len(scores) + 1))
    y = scores
    
    plt.plot(x, y, marker='o', linewidth=2, markersize=8)
    plt.fill_between(x, y, alpha=0.3)
    
    plt.title('Прогресс в психотестах', fontsize=16, fontweight='bold')
    plt.xlabel('Номер теста', fontsize=12)
    plt.ylabel('Баллы', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(x)
    
    # Добавляем максимально возможный балл
    plt.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Максимум (50)')
    
    plt.legend()
    plt.tight_layout()
    
    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    
    return buf

# Создание графика настроения и продуктивности
async def create_mood_chart(mood_history, productivity_history):
    plt.figure(figsize=(12, 6))
    
    # Создаем данные для графиков
    x = list(range(1, len(mood_history) + 1))
    
    # График настроения
    plt.subplot(2, 1, 1)
    plt.plot(x, mood_history, marker='o', color='green', linewidth=2, markersize=6, label='Настроение')
    plt.fill_between(x, mood_history, alpha=0.3, color='green')
    plt.title('Динамика настроения', fontsize=14, fontweight='bold')
    plt.xlabel('Запись в дневнике')
    plt.ylabel('Оценка (1-5)')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 6)
    plt.legend()
    
    # График продуктивности
    plt.subplot(2, 1, 2)
    plt.plot(x, productivity_history, marker='s', color='blue', linewidth=2, markersize=6, label='Продуктивность')
    plt.fill_between(x, productivity_history, alpha=0.3, color='blue')
    plt.title('Динамика продуктивности', fontsize=14, fontweight='bold')
    plt.xlabel('Запись в дневнике')
    plt.ylabel('Оценка (1-5)')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 6)
    plt.legend()
    
    plt.tight_layout()
    
    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    
    return buf

# Функция показа цитаты
async def show_quote(message: Message, user_id: int):
    global current_quote_index
    
    if user_id not in current_quote_index:
        current_quote_index[user_id] = 0
    
    quote = quotes[current_quote_index[user_id]]
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Следующая цитата →", callback_data="next_quote")]
        ]
    )
    
    await message.answer(f"💭 {quote}", reply_markup=keyboard)

# Обработка следующей цитаты
@dp.callback_query(lambda c: c.data == "next_quote")
async def next_quote(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if user_id not in current_quote_index:
        current_quote_index[user_id] = 0
    
    current_quote_index[user_id] = (current_quote_index[user_id] + 1) % len(quotes)
    quote = quotes[current_quote_index[user_id]]
    
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
        question_data = psychology_questions[question_index]
        question_text = question_data["question"]
        options = question_data["options"]
        
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=option)] for option in options],
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
    user_id = message.from_user.id
    data = await state.get_data()
    question_index = data.get("current_question", 0)
    
    # Получаем вес ответа
    answer_text = message.text
    question_data = psychology_questions[question_index]
    
    if answer_text in question_data["options"]:
        answer_index = question_data["options"].index(answer_text)
        score = question_data["weights"][answer_index]
    else:
        score = 2  # Средний балл при некорректном ответе
    
    # Сохраняем ответ
    if "current_test" not in users_data[user_id]:
        users_data[user_id]["current_test"] = []
    
    users_data[user_id]["current_test"].append({
        "question": question_data["question"],
        "answer": answer_text,
        "score": score
    })
    
    await ask_psychology_question(message, state, question_index + 1)

# Завершение психологического теста
async def finish_psychology_test(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_test = users_data[user_id].get("current_test", [])
    
    # Рассчитываем общий балл
    total_score = sum(answer["score"] for answer in current_test)
    max_score = 50  # Максимально возможный балл (5*10 вопросов)
    
    # Определяем результат
    percentage = (total_score / max_score) * 100
    
    if percentage >= 80:
        result = "Отличный результат! Вы обладаете прекрасной психологической устойчивостью."
        recommendation = "Продолжайте в том же духе!"
    elif percentage >= 60:
        result = "Хороший результат! У вас хорошие психологические показатели."
        recommendation = "Есть небольшой потенциал для роста."
    elif percentage >= 40:
        result = "Средний результат. Есть над чем поработать."
        recommendation = "Рекомендуется уделять больше внимания саморазвитию."
    else:
        result = "Результат ниже среднего. Рекомендуется обратить внимание на свое психологическое состояние."
        recommendation = "Попробуйте практиковать медитацию или обратитесь к психологу."
    
    # Сохраняем результат теста
    test_result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answers": current_test,
        "total_score": total_score,
        "max_score": max_score,
        "percentage": percentage
    }
    
    if "test_results" not in users_data[user_id]:
        users_data[user_id]["test_results"] = []
    
    users_data[user_id]["test_results"].append(test_result)
    
    # Формируем детальный отчет
    report = f"🎉 Тест завершен!\n\n"
    report += f"📊 Ваши результаты:\n"
    report += f"• Набрано баллов: {total_score}/{max_score}\n"
    report += f"• Процент выполнения: {percentage:.1f}%\n\n"
    report += f"📈 Оценка: {result}\n"
    report += f"💡 Рекомендация: {recommendation}\n\n"
    
    # Показываем слабые места (вопросы с наименьшими баллами)
    weak_answers = sorted(current_test, key=lambda x: x["score"])[:3]
    if weak_answers:
        report += "📝 Вопросы для улучшения:\n"
        for i, answer in enumerate(weak_answers, 1):
            report += f"{i}. {answer['question']}\n"
            report += f"   Ваш ответ: {answer['answer']} ({answer['score']}/5 баллов)\n\n"
    
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
    user_id = message.from_user.id
    answer_text = message.text
    question_data = diary_questions[question_index]
    
    # Получаем числовое значение ответа
    if answer_text in question_data["options"]:
        answer_index = question_data["options"].index(answer_text)
        numeric_value = question_data["values"][answer_index]
    else:
        numeric_value = 3  # Среднее значение при некорректном ответе
    
    # Сохраняем ответ
    if "current_diary" not in users_data[user_id]:
        users_data[user_id]["current_diary"] = []
    
    users_data[user_id]["current_diary"].append({
        "question": question_data["question"],
        "answer": answer_text,
        "numeric_value": numeric_value
    })
    
    # Задаем следующий вопрос или завершаем
    await ask_diary_question(message, state, question_index + 1)

# Завершение заполнения дневника
async def finish_diary(message: Message, state: FSMContext):
    user_id = message.from_user.id
    diary_entry = users_data[user_id].get("current_diary", [])
    
    # Рассчитываем средние значения
    mood_value = next((item["numeric_value"] for item in diary_entry if "настроение" in item["question"].lower()), 3)
    productivity_value = next((item["numeric_value"] for item in diary_entry if "продуктив" in item["question"].lower()), 3)
    stress_value = next((item["numeric_value"] for item in diary_entry if "стресс" in item["question"].lower()), 3)
    
    summary = "📓 Дневник заполнен!\n\n"
    summary += "Ваши ответы:\n\n"
    
    for i, entry in enumerate(diary_entry, 1):
        summary += f"{i}. {entry['question']}\n"
        summary += f"   Ответ: {entry['answer']}\n\n"
    
    summary += f"📈 Итоговые показатели:\n"
    summary += f"• Настроение: {mood_value}/5 "
    if mood_value >= 4:
        summary += "😊\n"
    elif mood_value >= 3:
        summary += "🙂\n"
    else:
        summary += "😔\n"
    
    summary += f"• Продуктивность: {productivity_value}/5 "
    if productivity_value >= 4:
        summary += "🔥\n"
    elif productivity_value >= 3:
        summary += "👍\n"
    else:
        summary += "👎\n"
    
    summary += f"• Управление стрессом: {stress_value}/5 "
    if stress_value >= 4:
        summary += "💪\n\n"
    elif stress_value >= 3:
        summary += "👌\n\n"
    else:
        summary += "😓\n\n"
    
    # Рекомендация
    if mood_value < 3 or stress_value < 3:
        summary += "💡 Рекомендация: Сегодня был сложный день. Попробуйте сделать что-то приятное для себя вечером."
    elif productivity_value < 3:
        summary += "💡 Рекомендация: Запланируйте важные задачи на завтра с утра."
    else:
        summary += "💡 Рекомендация: Отличный день! Продолжайте в том же духе!"
    
    # Сохраняем запись дневника
    diary_record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answers": diary_entry,
        "mood": mood_value,
        "productivity": productivity_value,
        "stress": stress_value
    }
    
    if "diary_entries" not in users_data[user_id]:
        users_data[user_id]["diary_entries"] = []
    
    users_data[user_id]["diary_entries"].append(diary_record)
    
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

# Главная функция
async def main():
    logger.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())