import subprocess
import sys
import os

def install_requirements():
    """Установка зависимостей"""
    print("Установка зависимостей...")
    requirements = [
        "Flask==2.2.5",
        "Flask-SQLAlchemy==3.0.5", 
        "Flask-Login==0.6.2",
        "Flask-WTF==1.1.1",
        "WTForms==3.0.1",
        "python-dotenv==1.0.0",
        "Werkzeug==2.2.2"
    ]
    
    for package in requirements:
        print(f"Установка {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("Все зависимости установлены!")

def create_folder_structure():
    """Создание структуры папок"""
    folders = ['templates', 'static', 'static/css', 'static/js', 'static/images', 'instance']
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Создана папка: {folder}")
    
    print("Структура папок создана!")

if __name__ == "__main__":
    print("Настройка проекта IT Career Catalyst")
    print("=" * 50)
    
    try:
        create_folder_structure()
        install_requirements()
        
        print("\nЗапуск приложения...")
        print("Откройте в браузере: http://127.0.0.1:5000")
        print("=" * 50)
        
        # Запуск основного приложения
        import app
        app.init_db()
        app.app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Попробуйте запустить вручную:")
        print("1. pip install -r requirements.txt")
        print("2. python app.py")
        input("Нажмите Enter для выхода...")