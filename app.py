import os
import json
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash

# Создаем экземпляр Flask
app = Flask(__name__, instance_relative_config=True)

# Убедимся, что папка instance существует
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Настройки приложения
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'  # Для продакшена используйте .env файл
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db = SQLAlchemy(app)

# Инициализация менеджера авторизации
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'

# Модели базы данных
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    level = db.Column(db.String(20), default='beginner')
    experience = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # beginner, intermediate, advanced
    category = db.Column(db.String(50), nullable=False)  # frontend, backend, database, etc.
    technology = db.Column(db.String(100))
    estimated_time = db.Column(db.String(50))
    salary_range = db.Column(db.String(100))
    company = db.Column(db.String(100))
    requirements = db.Column(db.Text)
    solution_template = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    progress = db.Column(db.Integer, default=0)  # 0-100%

class TaskSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    code = db.Column(db.Text)
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, accepted
    review_comments = db.Column(db.Text)

class Theory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    technology = db.Column(db.String(100))
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Roadmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    steps = db.Column(db.Text)  # JSON с шагами roadmap
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Формы
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', 
                                   validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Полное имя')
    submit = SubmitField('Зарегистрироваться')

class TaskSubmissionForm(FlaskForm):
    code = TextAreaField('Код решения', validators=[DataRequired()])
    comments = TextAreaField('Комментарии')
    submit = SubmitField('Отправить на проверку')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    """Инициализация базы данных"""
    print(f"Создание базы данных в: {app.instance_path}")
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        print("Таблицы созданы успешно")
        
        # Проверяем, есть ли данные
        if User.query.count() == 0:
            print("Создание тестовых данных...")
            create_sample_data()
            print("Тестовые данные созданы")
        else:
            print("База данных уже содержит данные")

def create_sample_data():
    """Создание тестовых данных"""
    # Создаем тестового пользователя
    admin = User(
        username='admin',
        email='admin@example.com',
        full_name='Администратор',
        level='advanced',
        experience=1000
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Создаем обычного пользователя
    user = User(
        username='student',
        email='student@example.com',
        full_name='Студент Тестовый',
        level='beginner',
        experience=100
    )
    user.set_password('student123')
    db.session.add(user)
    
    # Создаем задачи
    tasks_data = [
        {
            'title': 'Виджет погоды для CRM',
            'description': 'Разработать React-компонент для отображения погоды в карточке клиента. Компонент должен отображать текущую погоду, прогноз на 5 дней и иметь возможность выбора города.',
            'difficulty': 'intermediate',
            'category': 'frontend',
            'technology': 'React, API, CSS',
            'estimated_time': '8-12 часов',
            'salary_range': '~80 000 ₽',
            'company': 'TechCorp Inc.',
            'requirements': '1. Использовать React 18+\n2. Интеграция с OpenWeather API\n3. Адаптивный дизайн для мобильных устройств\n4. Кэширование запросов\n5. Обработка ошибок API\n6. Анимации загрузки',
            'solution_template': 'import React, { useState, useEffect } from "react";\n\nfunction WeatherWidget() {\n  const [weather, setWeather] = useState(null);\n  const [loading, setLoading] = useState(true);\n  \n  useEffect(() => {\n    // Получение данных о погоде\n    fetchWeatherData();\n  }, []);\n  \n  const fetchWeatherData = async () => {\n    try {\n      // Ваш код здесь\n    } catch (error) {\n      console.error("Ошибка при получении данных:", error);\n    }\n  };\n  \n  return (\n    <div className="weather-widget">\n      {/* Ваш JSX код здесь */}\n    </div>\n  );\n}\n\nexport default WeatherWidget;'
        },
        {
            'title': 'REST API для блога',
            'description': 'Создать RESTful API на Node.js с полной CRUD функциональностью для статей блога. API должно поддерживать аутентификацию пользователей, загрузку изображений и пагинацию.',
            'difficulty': 'beginner',
            'category': 'backend',
            'technology': 'Node.js, Express, MongoDB, JWT',
            'estimated_time': '10-15 часов',
            'salary_range': '~65 000 ₽',
            'company': 'DevSolutions',
            'requirements': '1. Express.js фреймворк\n2. MongoDB с Mongoose ODM\n3. JWT аутентификация\n4. Валидация входных данных\n5. Загрузка файлов (изображений)\n6. Пагинация результатов\n7. Поиск по статьям',
            'solution_template': 'const express = require("express");\nconst mongoose = require("mongoose");\nconst jwt = require("jsonwebtoken");\n\nconst app = express();\napp.use(express.json());\n\n// Подключение к MongoDB\nmongoose.connect("mongodb://localhost/blog", {\n  useNewUrlParser: true,\n  useUnifiedTopology: true\n});\n\n// Схема статьи\nconst articleSchema = new mongoose.Schema({\n  title: String,\n  content: String,\n  author: String,\n  createdAt: { type: Date, default: Date.now }\n});\n\nconst Article = mongoose.model("Article", articleSchema);\n\n// Ваш код маршрутов здесь\n\napp.listen(3000, () => {\n  console.log("Сервер запущен на порту 3000");\n});'
        },
        {
            'title': 'Оптимизация запросов для интернет-магазина',
            'description': 'Проанализировать и оптимизировать медленные SQL-запросы в базе данных PostgreSQL для интернет-магазина с 100,000+ товаров. Улучшить производительность на 50%.',
            'difficulty': 'advanced',
            'category': 'database',
            'technology': 'PostgreSQL, SQL, EXPLAIN',
            'estimated_time': '12-18 часов',
            'salary_range': '~95 000 ₽',
            'company': 'E-Commerce Pro',
            'requirements': '1. Анализ EXPLAIN планов запросов\n2. Создание оптимальных индексов\n3. Оптимизация JOIN запросов\n4. Настройка конфигурации PostgreSQL\n5. Рефакторинг сложных запросов\n6. Кэширование часто используемых данных',
            'solution_template': '-- 1. Анализ текущих медленных запросов\nEXPLAIN ANALYZE \nSELECT p.*, c.name as category_name \nFROM products p \nJOIN categories c ON p.category_id = c.id \nWHERE p.price BETWEEN 100 AND 1000 \nORDER BY p.created_at DESC \nLIMIT 50;\n\n-- 2. Создание индексов\nCREATE INDEX idx_products_price_category ON products(price, category_id);\nCREATE INDEX idx_products_created_at ON products(created_at DESC);\n\n-- 3. Оптимизированный запрос\n-- Ваш оптимизированный SQL код здесь'
        },
        {
            'title': 'Адаптивная верстка лендинга',
            'description': 'Сверстать адаптивный landing page по макету в Figma для IT-курсов. Страница должна корректно отображаться на всех устройствах от мобильных до десктопов.',
            'difficulty': 'beginner',
            'category': 'frontend',
            'technology': 'HTML5, CSS3, JavaScript',
            'estimated_time': '4-6 часов',
            'salary_range': '~45 000 ₽',
            'company': 'WebDesign Studio',
            'requirements': '1. Pixel-perfect верстка\n2. Mobile-first подход\n3. Кроссбраузерная совместимость\n4. Анимации на CSS/JS\n5. Оптимизация производительности\n6. Семантическая разметка',
            'solution_template': '<!DOCTYPE html>\n<html lang="ru">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>IT Курсы</title>\n  <style>\n    /* Ваш CSS код здесь */\n    * {\n      margin: 0;\n      padding: 0;\n      box-sizing: border-box;\n    }\n    \n    .container {\n      max-width: 1200px;\n      margin: 0 auto;\n      padding: 0 20px;\n    }\n    \n    /* Медиа-запросы для адаптивности */\n    @media (max-width: 768px) {\n      /* Стили для мобильных устройств */\n    }\n  </style>\n</head>\n<body>\n  <!-- Ваша HTML разметка здесь -->\n  \n  <script>\n    // Ваш JavaScript код здесь\n  </script>\n</body>\n</html>'
        },
        {
            'title': 'Telegram-бот для уведомлений',
            'description': 'Разработать Telegram-бота на Python для отправки уведомлений о статусе заказов в интернет-магазине. Бот должен интегрироваться с существующим API магазина.',
            'difficulty': 'intermediate',
            'category': 'backend',
            'technology': 'Python, Telegram API, PostgreSQL',
            'estimated_time': '8-12 часов',
            'salary_range': '~75 000 ₽',
            'company': 'ShopTech',
            'requirements': '1. Python 3.8+\n2. Библиотека python-telegram-bot\n3. Интеграция с REST API магазина\n4. Асинхронная обработка запросов\n5. Логирование ошибок\n6. Конфигурация через environment variables',
            'solution_template': 'import os\nimport logging\nfrom telegram import Update\nfrom telegram.ext import Application, CommandHandler, ContextTypes\nimport requests\n\n# Настройка логирования\nlogging.basicConfig(\n    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",\n    level=logging.INFO\n)\n\nlogger = logging.getLogger(__name__)\n\n# Токен бота из переменных окружения\nBOT_TOKEN = os.getenv("BOT_TOKEN")\nSHOP_API_URL = os.getenv("SHOP_API_URL")\n\nasync def start(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    """Обработчик команды /start"""\n    user = update.effective_user\n    await update.message.reply_text(\n        f"Привет, {user.first_name}! Я бот для отслеживания заказов.\\n"\n        "Используйте /help для списка команд."\n    )\n\nasync def check_order(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    """Проверка статуса заказа"""\n    # Ваш код здесь\n    pass\n\n# Основная функция\nasync def main():\n    """Запуск бота"""\n    application = Application.builder().token(BOT_TOKEN).build()\n    \n    # Регистрация обработчиков команд\n    application.add_handler(CommandHandler("start", start))\n    application.add_handler(CommandHandler("order", check_order))\n    \n    # Запуск бота\n    await application.run_polling()\n\nif __name__ == "__main__":\n    import asyncio\n    asyncio.run(main())'
        }
    ]
    
    for task_data in tasks_data:
        task = Task(**task_data)
        db.session.add(task)
    
    # Создаем теоретические материалы
    theory_data = [
        {
            'title': 'Основы баз данных: SQL и нормализация',
            'content': 'В этом руководстве вы изучите фундаментальные концепции проектирования баз данных. Мы рассмотрим: 1) Основы реляционных баз данных, 2) SQL запросы (SELECT, INSERT, UPDATE, DELETE), 3) Нормализацию до 3NF, 4) Создание индексов, 5) Транзакции и ACID свойства.',
            'category': 'database',
            'technology': 'SQL, PostgreSQL, MySQL',
            'difficulty': 'beginner'
        },
        {
            'title': 'React: Современные подходы к разработке',
            'content': 'Полное руководство по современной разработке на React. Рассматриваем: хуки (useState, useEffect, useContext), управление состоянием (Redux, Context API), оптимизацию производительности (React.memo, useMemo, useCallback), Server-Side Rendering и лучшие практики.',
            'category': 'frontend',
            'technology': 'React, JavaScript, TypeScript',
            'difficulty': 'intermediate'
        },
        {
            'title': 'REST API: проектирование и реализация',
            'content': 'Пошаговое руководство по созданию эффективных RESTful API. Темы: архитектура REST, версионирование API, аутентификация (JWT, OAuth2), документация (Swagger/OpenAPI), тестирование (Postman, unit tests), деплой и мониторинг.',
            'category': 'backend',
            'technology': 'Node.js, Python, REST, FastAPI/Express',
            'difficulty': 'intermediate'
        },
        {
            'title': 'Docker для разработчиков',
            'content': 'Практическое руководство по использованию Docker в разработке. Контейнеризация приложений, Docker Compose для многоконтейнерных приложений, создание Dockerfile, управление образами и контейнерами, интеграция с CI/CD.',
            'category': 'devops',
            'technology': 'Docker, Docker Compose, CI/CD',
            'difficulty': 'intermediate'
        }
    ]
    
    for theory_item in theory_data:
        theory = Theory(**theory_item)
        db.session.add(theory)
    
    # Создаем roadmap'ы
    roadmaps_data = [
        {
            'title': 'Junior Backend-разработчик',
            'description': 'Полный путь от основ программирования до полноценного backend-разработчика. Идеально для начинающих, которые хотят освоить серверную разработку.',
            'category': 'backend',
            'steps': json.dumps([
                {'title': 'Основы программирования на Python/JavaScript', 'description': 'Изучение синтаксиса, структур данных, ООП', 'completed': False},
                {'title': 'Работа с Git и GitHub', 'description': 'Версионный контроль, ветвление, пулл-реквесты', 'completed': False},
                {'title': 'Базы данных и SQL', 'description': 'PostgreSQL/MySQL, проектирование схем, запросы', 'completed': False},
                {'title': 'Основы HTTP и REST API', 'description': 'Протокол HTTP, методы, статус-коды, REST архитектура', 'completed': False},
                {'title': 'Фреймворк (Django/Express/Flask)', 'description': 'Создание веб-приложений, роутинг, middleware', 'completed': False},
                {'title': 'Аутентификация и авторизация', 'description': 'JWT, сессии, OAuth2, ролевая модель', 'completed': False},
                {'title': 'Тестирование и отладка', 'description': 'Unit тесты, интеграционные тесты, дебаггинг', 'completed': False},
                {'title': 'Деплой и основы DevOps', 'description': 'Docker, облачные платформы, CI/CD', 'completed': False}
            ])
        },
        {
            'title': 'Frontend-разработчик',
            'description': 'Комплексный план становления профессиональным фронтенд-разработчиком. От верстки до современных фреймворков.',
            'category': 'frontend',
            'steps': json.dumps([
                {'title': 'HTML5 и семантическая верстка', 'description': 'Семантические теги, доступность, валидация', 'completed': False},
                {'title': 'CSS3 и препроцессоры', 'description': 'Flexbox, Grid, анимации, SASS/SCSS', 'completed': False},
                {'title': 'JavaScript и ES6+', 'description': 'Современный JS, асинхронное программирование', 'completed': False},
                {'title': 'React/Vue/Angular основы', 'description': 'Выбор фреймворка, компоненты, состояние', 'completed': False},
                {'title': 'State management', 'description': 'Redux/Vuex, Context API, управление состоянием', 'completed': False},
                {'title': 'Инструменты сборки', 'description': 'Webpack, Vite, настройка проекта', 'completed': False},
                {'title': 'Тестирование фронтенда', 'description': 'Jest, React Testing Library, Cypress', 'completed': False},
                {'title': 'Оптимизация производительности', 'description': 'Lazy loading, code splitting, caching', 'completed': False}
            ])
        },
        {
            'title': 'Специалист по базам данных',
            'description': 'Путь от основ SQL до администрирования сложных баз данных и оптимизации производительности.',
            'category': 'database',
            'steps': json.dumps([
                {'title': 'Основы SQL', 'description': 'SELECT, JOIN, агрегатные функции, подзапросы', 'completed': False},
                {'title': 'Проектирование и нормализация БД', 'description': 'ER-диаграммы, нормальные формы', 'completed': False},
                {'title': 'Администрирование PostgreSQL/MySQL', 'description': 'Установка, настройка, бэкапы, мониторинг', 'completed': False},
                {'title': 'Оптимизация запросов', 'description': 'EXPLAIN, индексы, оптимизация JOIN', 'completed': False},
                {'title': 'Репликация и шардинг', 'description': 'Мастер-слейв репликация, горизонтальное шардинг', 'completed': False},
                {'title': 'NoSQL базы данных', 'description': 'MongoDB, Redis, их применение', 'completed': False},
                {'title': 'Миграции и версионирование схем', 'description': 'Инструменты миграции, управление изменениями', 'completed': False},
                {'title': 'Безопасность баз данных', 'description': 'Роли, привилегии, инъекции SQL', 'completed': False}
            ])
        }
    ]
    
    for roadmap_data in roadmaps_data:
        roadmap = Roadmap(**roadmap_data)
        db.session.add(roadmap)
    
    # Сохраняем все изменения
    db.session.commit()
    print(f"Создано: {User.query.count()} пользователей, {Task.query.count()} заданий, {Theory.query.count()} материалов")

# Маршруты
@app.route('/')
def index():
    """Главная страница"""
    tasks = Task.query.order_by(db.func.random()).limit(3).all()
    theory_count = Theory.query.count()
    task_count = Task.query.count()
    roadmap_count = Roadmap.query.count()
    
    user_progress = None
    if current_user.is_authenticated:
        user_tasks = UserTask.query.filter_by(user_id=current_user.id).all()
        completed = len([ut for ut in user_tasks if ut.status == 'completed'])
        in_progress = len([ut for ut in user_tasks if ut.status == 'in_progress'])
        user_progress = {
            'completed': completed,
            'in_progress': in_progress,
            'total_tasks': task_count
        }
    
    return render_template('index.html', 
                         tasks=tasks, 
                         theory_count=theory_count,
                         task_count=task_count,
                         roadmap_count=roadmap_count,
                         user_progress=user_progress)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный email или пароль', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Пользователь с таким именем уже существует', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация прошла успешно! Теперь вы можете войти в систему.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """Профиль пользователя"""
    user_tasks = UserTask.query.filter_by(user_id=current_user.id).all()
    
    # Получаем информацию о задачах
    completed_tasks = []
    in_progress_tasks = []
    
    for ut in user_tasks:
        task = Task.query.get(ut.task_id)
        if task:
            task_info = {
                'task': task,
                'user_task': ut,
                'progress': ut.progress,
                'completed_at': ut.completed_at
            }
            if ut.status == 'completed':
                completed_tasks.append(task_info)
            elif ut.status == 'in_progress':
                in_progress_tasks.append(task_info)
    
    total_tasks = Task.query.count()
    completed_count = len(completed_tasks)
    progress_percentage = int((completed_count / total_tasks * 100)) if total_tasks > 0 else 0
    
    return render_template('profile.html', 
                         completed_tasks=completed_tasks,
                         in_progress_tasks=in_progress_tasks,
                         progress_percentage=progress_percentage,
                         completed_count=completed_count,
                         total_tasks=total_tasks)

@app.route('/tasks')
def tasks():
    """Страница с заданиями"""
    category = request.args.get('category', 'all')
    difficulty = request.args.get('difficulty', 'all')
    
    query = Task.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if difficulty != 'all':
        query = query.filter_by(difficulty=difficulty)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Получаем статусы задач для текущего пользователя
    user_task_statuses = {}
    if current_user.is_authenticated:
        user_tasks = UserTask.query.filter_by(user_id=current_user.id).all()
        for ut in user_tasks:
            user_task_statuses[ut.task_id] = {
                'status': ut.status,
                'progress': ut.progress
            }
    
    return render_template('tasks.html', 
                         tasks=tasks, 
                         user_task_statuses=user_task_statuses,
                         current_category=category,
                         current_difficulty=difficulty)

@app.route('/task/<int:task_id>')
def task_detail(task_id):
    """Детальная страница задания"""
    task = Task.query.get_or_404(task_id)
    form = TaskSubmissionForm()
    
    user_task = None
    if current_user.is_authenticated:
        user_task = UserTask.query.filter_by(
            user_id=current_user.id, 
            task_id=task_id
        ).first()
    
    submissions = []
    if current_user.is_authenticated:
        submissions = TaskSubmission.query.filter_by(
            user_id=current_user.id, 
            task_id=task_id
        ).order_by(TaskSubmission.submitted_at.desc()).all()
    
    return render_template('task_detail.html', 
                         task=task, 
                         form=form,
                         user_task=user_task,
                         submissions=submissions)

@app.route('/task/<int:task_id>/start', methods=['POST'])
@login_required
def start_task(task_id):
    """Начать выполнение задачи"""
    task = Task.query.get_or_404(task_id)
    
    user_task = UserTask.query.filter_by(
        user_id=current_user.id, 
        task_id=task_id
    ).first()
    
    if not user_task:
        user_task = UserTask(
            user_id=current_user.id,
            task_id=task_id,
            status='in_progress',
            started_at=datetime.utcnow(),
            progress=0
        )
        db.session.add(user_task)
        db.session.commit()
        flash(f'Вы начали выполнение задачи "{task.title}"', 'success')
    elif user_task.status != 'in_progress':
        user_task.status = 'in_progress'
        user_task.started_at = datetime.utcnow()
        db.session.commit()
        flash(f'Вы продолжили выполнение задачи "{task.title}"', 'success')
    else:
        flash(f'Вы уже выполняете задачу "{task.title}"', 'info')
    
    return redirect(url_for('task_detail', task_id=task_id))

@app.route('/task/<int:task_id>/submit', methods=['POST'])
@login_required
def submit_task(task_id):
    """Отправить решение задачи"""
    task = Task.query.get_or_404(task_id)
    form = TaskSubmissionForm()
    
    if form.validate_on_submit():
        # Проверяем, есть ли активная задача
        user_task = UserTask.query.filter_by(
            user_id=current_user.id, 
            task_id=task_id
        ).first()
        
        if not user_task or user_task.status != 'in_progress':
            flash('Сначала начните выполнение задачи', 'warning')
            return redirect(url_for('task_detail', task_id=task_id))
        
        # Создаем запись о решении
        submission = TaskSubmission(
            user_id=current_user.id,
            task_id=task_id,
            code=form.code.data,
            comments=form.comments.data,
            status='pending'
        )
        
        # Обновляем статус задачи
        user_task.status = 'completed'
        user_task.progress = 100
        user_task.completed_at = datetime.utcnow()
        
        db.session.add(submission)
        db.session.commit()
        
        flash('Ваше решение отправлено на проверку!', 'success')
        return redirect(url_for('task_detail', task_id=task_id))
    
    # Если форма не валидна
    return render_template('task_detail.html', task=task, form=form)

@app.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Отметить задачу как выполненную"""
    task = Task.query.get_or_404(task_id)
    
    user_task = UserTask.query.filter_by(
        user_id=current_user.id, 
        task_id=task_id
    ).first()
    
    if user_task:
        user_task.status = 'completed'
        user_task.progress = 100
        user_task.completed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Задача "{task.title}" отмечена как выполненная!', 'success')
    else:
        flash('Сначала начните выполнение задачи', 'warning')
    
    return redirect(url_for('task_detail', task_id=task_id))

@app.route('/roadmaps')
def roadmaps():
    """Страница с карьерными путями"""
    roadmaps_list = Roadmap.query.all()
    
    # Парсим JSON шаги для каждого roadmap
    roadmap_data = []
    for roadmap in roadmaps_list:
        if roadmap.steps:
            try:
                steps = json.loads(roadmap.steps)
            except:
                steps = []
        else:
            steps = []
        
        roadmap_data.append({
            'id': roadmap.id,
            'title': roadmap.title,
            'description': roadmap.description,
            'category': roadmap.category,
            'steps': steps,
            'created_at': roadmap.created_at
        })
    
    return render_template('roadmaps.html', roadmaps=roadmap_data)

@app.route('/theory')
def theory():
    """Теоретические материалы"""
    category = request.args.get('category', 'all')
    
    query = Theory.query
    if category != 'all':
        query = query.filter_by(category=category)
    
    theory_items = query.order_by(Theory.created_at.desc()).all()
    return render_template('theory.html', theory_items=theory_items, current_category=category)

@app.route('/blog')
def blog():
    """Блог"""
    return render_template('blog.html')

# API эндпоинты
@app.route('/api/tasks/count')
def get_tasks_count():
    count = Task.query.count()
    return jsonify({'count': count})

@app.route('/api/user/progress')
@login_required
def get_user_progress():
    user_tasks = UserTask.query.filter_by(user_id=current_user.id).all()
    completed = len([ut for ut in user_tasks if ut.status == 'completed'])
    in_progress = len([ut for ut in user_tasks if ut.status == 'in_progress'])
    total_tasks = Task.query.count()
    
    return jsonify({
        'completed': completed,
        'in_progress': in_progress,
        'total_tasks': total_tasks,
        'progress_percentage': int((completed / total_tasks * 100)) if total_tasks > 0 else 0
    })

@app.route('/api/stats')
def get_stats():
    users_count = User.query.count()
    tasks_count = Task.query.count()
    theory_count = Theory.query.count()
    submissions_count = TaskSubmission.query.count()
    roadmaps_count = Roadmap.query.count()
    
    return jsonify({
        'users': users_count,
        'tasks': tasks_count,
        'theory': theory_count,
        'submissions': submissions_count,
        'roadmaps': roadmaps_count
    })

# Обработка ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Глобальный контекстный процессор
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

if __name__ == '__main__':
    print("=" * 50)
    print("Запуск IT Career Catalyst")
    print("=" * 50)
    
    # Инициализация базы данных
    init_db()
    
    print("\nСтатистика базы данных:")
    print(f"Пользователи: {User.query.count()}")
    print(f"Задания: {Task.query.count()}")
    print(f"Теория: {Theory.query.count()}")
    print(f"Roadmaps: {Roadmap.query.count()}")
    
    print("\nДоступные учетные записи для тестирования:")
    print("1. admin / admin123 (администратор)")
    print("2. student / student123 (студент)")
    
    print("\nСервер запускается...")
    print("Откройте в браузере: http://127.0.0.1:5000")
    print("=" * 50)
    
    # Запуск приложения
    app.run(debug=True, host='0.0.0.0', port=5000)