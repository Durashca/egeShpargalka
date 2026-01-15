import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import requests
import json
import os
import asyncio
import csv
import io

class EGEShpargalka(toga.App):
    def startup(self):
        # Настройки
        self.settings_file = "ege_settings.json"
        self.tasks_file = "tasks_cache.json"
        
        # Загрузка сохраненных данных
        self.settings = self.load_settings()
        self.stats = self.load_stats()
        
        # Основное окно
        self.main_window = toga.MainWindow(
            title=f"{self.formal_name} - Подготовка к ЕГЭ",
            size=(1000, 700)
        )
        
        # Создаем основные вкладки
        self.create_main_interface()
        
        # Асинхронная загрузка заданий
        asyncio.create_task(self.load_tasks_async())
        
    def create_main_interface(self):
        """Создает основной интерфейс с вкладками."""
        
        # Вкладка с предметами
        subjects_tab = self.create_subjects_tab()
        
        # Вкладка с вариантами
        variants_tab = self.create_variants_tab()
        
        # Вкладка со статистикой
        stats_tab = self.create_stats_tab()
        
        # Вкладка с настройками
        settings_tab = self.create_settings_tab()
        
        # Контейнер вкладок
        self.option_container = toga.OptionContainer(
            id="main_tabs",
            style=Pack(flex=1),
            content=[
                ("Предметы", subjects_tab),
                ("Варианты", variants_tab),
                ("Статистика", stats_tab),
                ("Настройки", settings_tab)
            ]
        )
        
        # Кнопка закрытия в нижней панели
        close_button = toga.Button(
            "Закрыть приложение",
            on_press=self.close_app,
            style=Pack(
                padding=10,
                background_color="#dc3545",
                color="white",
                font_weight="bold"
            )
        )
        
        # Основной контейнер
        main_box = toga.Box(
            children=[
                self.option_container,
                toga.Box(
                    children=[close_button],
                    style=Pack(padding=10, alignment=CENTER)
                )
            ],
            style=Pack(direction=COLUMN, flex=1)
        )
        
        self.main_window.content = main_box
        self.main_window.on_close = self.on_window_close
        self.main_window.show()
    
    def create_subjects_tab(self):
        """Создает вкладку с предметами."""
        subjects = [
            ("Математика", "math"),
            ("Физика", "physics"),
            ("Информатика", "informatics"),
            ("Русский язык", "russian")
        ]
        
        # Контейнер для кнопок выбора предмета
        subject_buttons_box = toga.Box(style=Pack(direction=ROW, padding=20, alignment=CENTER))
        
        for subject_name, subject_id in subjects:
            btn = toga.Button(
                subject_name,
                on_press=lambda widget, sid=subject_id: self.show_subject_tasks(sid),
                style=Pack(
                    padding=15,
                    margin=(0, 10),
                    background_color="#007bff",
                    color="white",
                    font_size=14,
                    flex=1
                )
            )
            subject_buttons_box.add(btn)
        
        # Область отображения заданий
        self.task_label = toga.Label(
            "Выберите предмет для начала подготовки",
            style=Pack(padding=20, font_size=16, text_align=CENTER)
        )
        
        # Поле для ответа
        self.answer_input = toga.TextInput(
            placeholder="Введите ваш ответ здесь...",
            style=Pack(padding=10, margin=(0, 20), flex=1)
        )
        
        # Кнопки действий
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=10, alignment=CENTER))
        
        check_button = toga.Button(
            "Проверить ответ",
            on_press=self.check_answer,
            style=Pack(padding=10, margin=(0, 5), background_color="#28a745", color="white")
        )
        
        next_button = toga.Button(
            "Следующий вопрос",
            on_press=self.next_question,
            style=Pack(padding=10, margin=(0, 5), background_color="#17a2b8", color="white")
        )
        
        show_answer_button = toga.Button(
            "Показать ответ",
            on_press=self.show_answer,
            style=Pack(padding=10, margin=(0, 5), background_color="#ffc107", color="black")
        )
        
        buttons_box.add(check_button)
        buttons_box.add(next_button)
        buttons_box.add(show_answer_button)
        
        # Результат проверки
        self.result_label = toga.Label(
            "",
            style=Pack(padding=10, font_size=14)
        )
        
        # Информация о текущем задании
        self.task_info_label = toga.Label(
            "",
            style=Pack(padding=10, font_size=12, color="#6c757d")
        )
        
        # Создаем вкладку
        tab_content = toga.Box(
            children=[
                toga.Label(
                    "Подготовка по предметам",
                    style=Pack(
                        padding=20,
                        font_size=20,
                        font_weight="bold",
                        text_align=CENTER
                    )
                ),
                subject_buttons_box,
                toga.Box(
                    children=[self.task_label],
                    style=Pack(padding=20, background_color="#f8f9fa")
                ),
                self.task_info_label,
                self.answer_input,
                buttons_box,
                self.result_label
            ],
            style=Pack(direction=COLUMN, padding=10)
        )
        
        # Инициализируем переменные для заданий
        self.current_subject = None
        self.current_task_index = 0
        self.tasks_data = {}
        self.current_task = None
        
        return tab_content
    
    def create_variants_tab(self):
        """Создает вкладку с вариантами ЕГЭ."""
        # Заголовок
        header = toga.Label(
            "Тренировочные варианты ЕГЭ",
            style=Pack(padding=20, font_size=20, font_weight="bold", text_align=CENTER)
        )
        
        # Информация
        info = toga.Label(
            "Выберите вариант для тренировки:\n\n"
            "• Вариант включает задания из всех предметов\n"
            "• На выполнение дается 3 часа 55 минут\n"
            "• Результаты сохраняются в статистике",
            style=Pack(padding=20, font_size=14, text_align=CENTER)
        )
        
        # Кнопки вариантов
        variants_box = toga.Box(style=Pack(direction=ROW, padding=20, alignment=CENTER))
        
        for i in range(1, 6):
            btn = toga.Button(
                f"Вариант #{i}",
                on_press=lambda widget, variant=i: self.start_variant(variant),
                style=Pack(
                    padding=15,
                    margin=(0, 10),
                    background_color="#6f42c1",
                    color="white",
                    font_size=14,
                    flex=1
                )
            )
            variants_box.add(btn)
        
        # Таймер и состояние
        self.timer_label = toga.Label(
            "Время: 03:55:00",
            style=Pack(padding=10, font_size=16, font_weight="bold", color="#dc3545")
        )
        
        self.variant_status_label = toga.Label(
            "Вариант не выбран",
            style=Pack(padding=10, font_size=14)
        )
        
        # Кнопки управления вариантом
        control_box = toga.Box(style=Pack(direction=ROW, padding=10, alignment=CENTER))
        
        start_button = toga.Button(
            "Начать вариант",
            on_press=self.start_variant_timer,
            style=Pack(padding=10, margin=(0, 5), background_color="#28a745", color="white")
        )
        
        pause_button = toga.Button(
            "Пауза",
            on_press=self.pause_variant,
            style=Pack(padding=10, margin=(0, 5), background_color="#ffc107", color="black")
        )
        
        finish_button = toga.Button(
            "Завершить досрочно",
            on_press=self.finish_variant,
            style=Pack(padding=10, margin=(0, 5), background_color="#dc3545", color="white")
        )
        
        control_box.add(start_button)
        control_box.add(pause_button)
        control_box.add(finish_button)
        
        return toga.Box(
            children=[
                header,
                info,
                variants_box,
                self.timer_label,
                self.variant_status_label,
                control_box
            ],
            style=Pack(direction=COLUMN, padding=10)
        )
    
    def create_stats_tab(self):
        """Создает вкладку со статистикой."""
        # Заголовок
        header = toga.Label(
            "Ваша статистика",
            style=Pack(padding=20, font_size=20, font_weight="bold", text_align=CENTER)
        )
        
        # Общая статистика
        self.total_stats_label = toga.Label(
            "Загрузка статистики...",
            style=Pack(padding=20, font_size=16, text_align=CENTER)
        )
        
        # Статистика по предметам
        self.subjects_stats_label = toga.Label(
            "",
            style=Pack(padding=20, font_size=14)
        )
        
        # Кнопки управления статистикой
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=10, alignment=CENTER))
        
        refresh_button = toga.Button(
            "Обновить статистику",
            on_press=self.refresh_stats,
            style=Pack(padding=10, margin=(0, 5), background_color="#17a2b8", color="white")
        )
        
        clear_button = toga.Button(
            "Сбросить статистику",
            on_press=self.clear_stats,
            style=Pack(padding=10, margin=(0, 5), background_color="#dc3545", color="white")
        )
        
        buttons_box.add(refresh_button)
        buttons_box.add(clear_button)
        
        return toga.Box(
            children=[
                header,
                self.total_stats_label,
                self.subjects_stats_label,
                buttons_box
            ],
            style=Pack(direction=COLUMN, padding=10)
        )
    
    def create_settings_tab(self):
        """Создает вкладку с настройками."""
        # Заголовок
        header = toga.Label(
            "Настройки приложения",
            style=Pack(padding=20, font_size=20, font_weight="bold", text_align=CENTER)
        )
        
        # URL вашего репозитория GitHub
        base_url = "https://raw.githubusercontent.com/Durashca/egeHelpDB/main/"
        
        # Создаем выбор файлов из репозитория
        file_label = toga.Label(
            "Выберите файл заданий из репозитория:",
            style=Pack(padding=(20, 20, 5, 20))
        )
        
        # Опции файлов
        self.file_selection = toga.Selection(
            items=[
                "mathematic.csv (Математика)",
                "physics.csv (Физика - в разработке)",
                "informatics.csv (Информатика - в разработке)",
                "russian.csv (Русский язык - в разработке)"
            ],
            value="mathematic.csv (Математика)",
            style=Pack(padding=10, margin=(0, 20))
        )
        
        # URL для загрузки
        self.csv_url_input = toga.TextInput(
            value=base_url + "mathematic.csv",
            placeholder="URL CSV файла",
            style=Pack(padding=10, margin=(0, 20))
        )
        
        # Выбор разделителя CSV
        delimiter_label = toga.Label(
            "Разделитель CSV файла:",
            style=Pack(padding=(20, 20, 5, 20))
        )
        
        self.delimiter_selection = toga.Selection(
            items=["Запятая (,)", "Точка с запятой (;)", "Табуляция (\\t)"],
            value="Запятая (,)",
            style=Pack(padding=10, margin=(0, 20))
        )
        
        # Обработчик изменения выбора файла
        self.file_selection.on_change = self.update_csv_url
        
        # Переключатель авто-проверки
        self.auto_check_switch = toga.Switch(
            "Автоматическая проверка ответов",
            value=self.settings.get("auto_check", True)
        )
        
        # Поле для времени варианта
        time_label = toga.Label(
            "Время на вариант (минуты):",
            style=Pack(padding=(20, 20, 5, 20))
        )
        
        self.variant_time_input = toga.TextInput(
            value=str(self.settings.get("variant_time", 235)),
            placeholder="235",
            style=Pack(padding=10, margin=(0, 20))
        )
        
        # Кнопки управления
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=20, alignment=CENTER))
        
        save_button = toga.Button(
            "Сохранить настройки",
            on_press=self.save_settings,
            style=Pack(padding=10, margin=(0, 5), background_color="#28a745", color="white")
        )
        
        load_button = toga.Button(
            "Загрузить задания",
            on_press=self.load_tasks_from_url,
            style=Pack(padding=10, margin=(0, 5), background_color="#17a2b8", color="white")
        )
        
        buttons_box.add(save_button)
        buttons_box.add(load_button)
        
        # Статус загрузки
        self.settings_status_label = toga.Label(
            "",
            style=Pack(padding=10, font_size=12)
        )
        
        return toga.Box(
            children=[
                header,
                file_label,
                self.file_selection,
                self.csv_url_input,
                delimiter_label,
                self.delimiter_selection,
                self.auto_check_switch,
                time_label,
                self.variant_time_input,
                buttons_box,
                self.settings_status_label
            ],
            style=Pack(direction=COLUMN)
        )
    
    def update_csv_url(self, widget):
        """Обновляет URL при выборе файла."""
        base_url = "https://raw.githubusercontent.com/Durashca/egeHelpDB/main/"
        
        selected = widget.value
        if selected:
            # Извлекаем имя файла из выбранной опции
            filename = selected.split(" (")[0]
            self.csv_url_input.value = base_url + filename
    
    async def load_tasks_async(self):
        """Асинхронная загрузка заданий."""
        try:
            # Пробуем загрузить из кэша
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks_data = json.load(f)
                print(f"Загружено {len(self.tasks_data)} предметов из кэша")
                return
            
            # Загружаем с GitHub если есть URL
            url = self.settings.get("csv_url", "")
            if url and url.startswith("http"):
                await self.load_tasks_from_url(None, show_message=False)
            
        except Exception as e:
            print(f"Ошибка при загрузке заданий: {e}")
            # Создаем тестовые данные
            self.tasks_data = self.create_sample_tasks()
    
    def create_sample_tasks(self):
        """Создает тестовые задания для всех предметов."""
        return {
            "math": [
                {
                    "question": "Найдите производную функции y = 3x²",
                    "answer": "6x",
                    "topic": "Производная",
                    "difficulty": "medium"
                },
                {
                    "question": "Решите уравнение: x² - 5x + 6 = 0",
                    "answer": "2, 3",
                    "topic": "Квадратные уравнения",
                    "difficulty": "easy"
                }
            ],
            "physics": [
                {
                    "question": "Чему равна скорость света в вакууме?",
                    "answer": "300000 км/с",
                    "topic": "Оптика",
                    "difficulty": "easy"
                }
            ],
            "informatics": [
                {
                    "question": "True AND False = ?",
                    "answer": "False",
                    "topic": "Логика",
                    "difficulty": "easy"
                }
            ],
            "russian": [
                {
                    "question": "В каком слове пишется буква Ё: ш...л?",
                    "answer": "шёл",
                    "topic": "Орфография",
                    "difficulty": "easy"
                }
            ]
        }
    
    def load_settings(self):
        """Загружает настройки из файла."""
        default_settings = {
            "csv_url": "https://raw.githubusercontent.com/Durashca/egeHelpDB/main/mathematic.csv",
            "delimiter": ",",
            "auto_check": True,
            "variant_time": 235
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Объединяем с дефолтными на случай отсутствия ключей
                    default_settings.update(loaded)
                    return default_settings
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
        
        return default_settings
    
    def load_stats(self):
        """Загружает статистику из файла."""
        default_stats = {
            "total_attempts": 0,
            "correct_answers": 0,
            "subjects": {
                "math": {"attempts": 0, "correct": 0},
                "physics": {"attempts": 0, "correct": 0},
                "informatics": {"attempts": 0, "correct": 0},
                "russian": {"attempts": 0, "correct": 0}
            },
            "variants_completed": 0,
            "best_score": 0
        }
        
        try:
            if os.path.exists("stats.json"):
                with open("stats.json", 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Объединяем с дефолтными на случай отсутствия ключей
                    for key in default_stats:
                        if key in loaded:
                            if isinstance(default_stats[key], dict) and isinstance(loaded[key], dict):
                                default_stats[key].update(loaded[key])
                            else:
                                default_stats[key] = loaded[key]
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")
        
        return default_stats
    
    def save_stats(self):
        """Сохраняет статистику в файл."""
        try:
            with open("stats.json", 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения статистики: {e}")
    
    async def load_tasks_from_url(self, widget, show_message=True):
        """Загружает задания с указанного URL."""
        if show_message:
            self.settings_status_label.text = "Загрузка заданий..."
            self.settings_status_label.style.color = "#17a2b8"
        
        try:
            url = self.csv_url_input.value.strip()
            if not url:
                if show_message:
                    self.settings_status_label.text = "Введите URL для загрузки"
                    self.settings_status_label.style.color = "#dc3545"
                return
            
            # Проверяем URL
            if not url.startswith("http"):
                if show_message:
                    self.settings_status_label.text = "Неверный URL. Должен начинаться с http:// или https://"
                    self.settings_status_label.style.color = "#dc3545"
                return
            
            # Получаем выбранный разделитель
            delimiter_text = self.delimiter_selection.value
            if delimiter_text == "Запятая (,)":
                delimiter = ","
            elif delimiter_text == "Точка с запятой (;)":
                delimiter = ";"
            elif delimiter_text == "Табуляция (\\t)":
                delimiter = "\t"
            else:
                delimiter = ","
            
            response = await asyncio.to_thread(requests.get, url, timeout=10)
            response.raise_for_status()
            
            # Пробуем разные кодировки
            content = None
            used_encoding = "utf-8"
            
            # Сначала пробуем utf-8
            try:
                content = response.content.decode('utf-8')
                used_encoding = "utf-8"
            except UnicodeDecodeError:
                # Пробуем windows-1251
                try:
                    content = response.content.decode('windows-1251')
                    used_encoding = "windows-1251"
                except UnicodeDecodeError:
                    # Пробуем cp1251
                    try:
                        content = response.content.decode('cp1251')
                        used_encoding = "cp1251"
                    except UnicodeDecodeError:
                        # Пробуем utf-8-sig
                        try:
                            content = response.content.decode('utf-8-sig')
                            used_encoding = "utf-8-sig"
                        except UnicodeDecodeError:
                            # Последняя попытка с игнорированием ошибок
                            content = response.content.decode('utf-8', errors='ignore')
                            used_encoding = "utf-8 (ignore errors)"
            
            # Парсим CSV
            csv_reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            
            # Группируем по предметам
            self.tasks_data = {}
            task_count = 0
            
            for row in csv_reader:
                # Определяем предмет
                subject = row.get('subject', '').lower().strip()
                if not subject:
                    # Если subject нет в данных, определяем по имени файла
                    filename = url.split("/")[-1].lower()
                    if "mathematic" in filename or "math" in filename:
                        subject = "math"
                    elif "physics" in filename:
                        subject = "physics"
                    elif "informatic" in filename:
                        subject = "informatics"
                    elif "russian" in filename:
                        subject = "russian"
                    else:
                        subject = "math"  # По умолчанию математика
                
                if subject not in self.tasks_data:
                    self.tasks_data[subject] = []
                
                # Извлекаем данные из строки
                question = row.get('question_text', row.get('Вопрос', ''))
                answer = row.get('correct_answer', row.get('Ответ', ''))
                topic = row.get('topic', row.get('Тема', 'Общая тема'))
                difficulty = row.get('difficulty', row.get('Сложность', 'medium'))
                explanation = row.get('explanation', row.get('Объяснение', ''))
                
                task = {
                    'question': question,
                    'answer': answer,
                    'topic': topic,
                    'difficulty': difficulty,
                    'explanation': explanation
                }
                
                # Проверяем, что есть хотя бы вопрос и ответ
                if task['question'] and task['answer']:
                    self.tasks_data[subject].append(task)
                    task_count += 1
                    print(f"Загружено задание по {subject}: {task['question'][:50]}...")
            
            # Сохраняем в кэш
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks_data, f, indent=2, ensure_ascii=False)
            
            if show_message:
                self.settings_status_label.text = f"Успешно загружено {task_count} заданий (кодировка: {used_encoding}, разделитель: {delimiter})"
                self.settings_status_label.style.color = "#28a745"
            
            print(f"Загружено {task_count} заданий по предметам: {list(self.tasks_data.keys())}")
            
            # Обновляем статистику
            self.refresh_stats_display()
            
        except requests.exceptions.Timeout:
            if show_message:
                self.settings_status_label.text = "Таймаут при загрузке заданий"
                self.settings_status_label.style.color = "#dc3545"
        except requests.exceptions.RequestException as e:
            if show_message:
                self.settings_status_label.text = f"Ошибка сети: {str(e)}"
                self.settings_status_label.style.color = "#dc3545"
        except Exception as e:
            if show_message:
                self.settings_status_label.text = f"Ошибка загрузки: {str(e)}"
                self.settings_status_label.style.color = "#dc3545"
            print(f"Ошибка загрузки CSV: {e}")
            import traceback
            traceback.print_exc()
    
    def show_subject_tasks(self, subject_id):
        """Показывает задания по выбранному предмету."""
        self.current_subject = subject_id
        self.current_task_index = 0
        
        # Обновляем статус
        subject_names = {
            "math": "Математика",
            "physics": "Физика", 
            "informatics": "Информатика",
            "russian": "Русский язык"
        }
        
        subject_name = subject_names.get(subject_id, subject_id)
        self.option_container.current_tab = "Предметы"
        
        if subject_id in self.tasks_data and self.tasks_data[subject_id]:
            self.show_next_task()
            self.task_info_label.text = f"Предмет: {subject_name} | Заданий: {len(self.tasks_data[subject_id])}"
        else:
            self.task_label.text = f"Задания по {subject_name} пока не загружены.\nИспользуйте вкладку 'Настройки' для загрузки."
            self.task_info_label.text = ""
            self.answer_input.value = ""
            self.result_label.text = ""
    
    def show_next_task(self):
        """Показывает следующее задание."""
        if not self.current_subject or self.current_subject not in self.tasks_data:
            return
        
        tasks = self.tasks_data[self.current_subject]
        if not tasks:
            return
        
        if self.current_task_index >= len(tasks):
            self.current_task_index = 0
        
        self.current_task = tasks[self.current_task_index]
        
        # Обновляем интерфейс
        difficulty_symbols = {
            "easy": "🟢 Легко",
            "medium": "🟡 Средне", 
            "hard": "🔴 Сложно"
        }
        
        difficulty = self.current_task.get('difficulty', 'medium')
        symbol = difficulty_symbols.get(difficulty, '🟡 Средне')
        
        self.task_label.text = f"{symbol}\n\n{self.current_task['question']}"
        self.answer_input.value = ""
        self.result_label.text = ""
        
        # Обновляем информацию о задании
        topic = self.current_task.get('topic', 'Общая тема')
        self.task_info_label.text = (
            f"Тема: {topic} | Сложность: {difficulty} | "
            f"Задание {self.current_task_index + 1} из {len(tasks)}"
        )
    
    def check_answer(self, widget):
        """Проверяет ответ пользователя."""
        if not self.current_task:
            self.result_label.text = "Сначала выберите задание!"
            self.result_label.style.color = "#dc3545"
            return
        
        user_answer = self.answer_input.value.strip()
        correct_answer = str(self.current_task['answer']).strip()
        
        if not user_answer:
            self.result_label.text = "Введите ответ для проверки!"
            self.result_label.style.color = "#ffc107"
            return
        
        # Обновляем статистику
        if self.current_subject:
            self.stats['total_attempts'] += 1
            if self.current_subject in self.stats['subjects']:
                self.stats['subjects'][self.current_subject]['attempts'] += 1
        
        # Сравниваем ответы (нестрого)
        user_normalized = user_answer.lower().replace(',', '.').replace(' ', '').replace(';', ',')
        correct_normalized = correct_answer.lower().replace(',', '.').replace(' ', '').replace(';', ',')
        
        if user_normalized == correct_normalized:
            self.result_label.text = "✅ Правильно! Отличная работа!"
            self.result_label.style.color = "#28a745"
            
            # Обновляем статистику
            self.stats['correct_answers'] += 1
            if self.current_subject in self.stats['subjects']:
                self.stats['subjects'][self.current_subject]['correct'] += 1
        else:
            self.result_label.text = f"❌ Неверно. Ваш ответ: '{user_answer}'\nПравильный ответ: '{correct_answer}'"
            
            # Добавляем объяснение если есть
            explanation = self.current_task.get('explanation', '')
            if explanation:
                self.result_label.text += f"\n\nОбъяснение: {explanation}"
            
            self.result_label.style.color = "#dc3545"
        
        self.save_stats()
        self.refresh_stats_display()
    
    def show_answer(self, widget):
        """Показывает правильный ответ."""
        if self.current_task:
            explanation = self.current_task.get('explanation', '')
            if explanation:
                self.result_label.text = f"Правильный ответ: {self.current_task['answer']}\n\nОбъяснение: {explanation}"
            else:
                self.result_label.text = f"Правильный ответ: {self.current_task['answer']}"
            self.result_label.style.color = "#17a2b8"
    
    def next_question(self, widget):
        """Показывает следующее задание."""
        if self.current_subject and self.current_subject in self.tasks_data:
            tasks_count = len(self.tasks_data[self.current_subject])
            if tasks_count > 0:
                self.current_task_index = (self.current_task_index + 1) % tasks_count
                self.show_next_task()
    
    def start_variant(self, variant_number):
        """Начинает выполнение варианта."""
        self.variant_status_label.text = f"Выполняется вариант #{variant_number}"
        self.option_container.current_tab = "Варианты"
    
    def start_variant_timer(self, widget):
        """Запускает таймер для варианта."""
        self.variant_status_label.text = "Вариант начат! Таймер запущен."
        # Здесь можно реализовать реальный таймер
    
    def pause_variant(self, widget):
        """Ставит вариант на паузу."""
        self.variant_status_label.text = "Вариант на паузе"
    
    def finish_variant(self, widget):
        """Завершает вариант досрочно."""
        self.variant_status_label.text = "Вариант завершен досрочно"
        self.timer_label.text = "Время: 00:00:00"
        
        # Обновляем статистику
        self.stats['variants_completed'] += 1
        self.save_stats()
        self.refresh_stats_display()
    
    def refresh_stats(self, widget=None):
        """Обновляет отображение статистики."""
        self.refresh_stats_display()
    
    def refresh_stats_display(self):
        """Обновляет данные статистики на экране."""
        total = self.stats['total_attempts']
        correct = self.stats['correct_answers']
        
        if total > 0:
            percentage = (correct / total) * 100
            stats_text = (
                f"Всего решено: {total} заданий\n"
                f"Правильных ответов: {correct}\n"
                f"Точность: {percentage:.1f}%\n"
                f"Завершено вариантов: {self.stats['variants_completed']}"
            )
        else:
            stats_text = "Вы еще не решили ни одного задания"
        
        self.total_stats_label.text = stats_text
        
        # Статистика по предметам
        subjects_text = "Статистика по предметам:\n"
        for subject, data in self.stats['subjects'].items():
            subject_name = {
                "math": "Математика",
                "physics": "Физика",
                "informatics": "Информатика",
                "russian": "Русский язык"
            }.get(subject, subject)
            
            if data['attempts'] > 0:
                perc = (data['correct'] / data['attempts'] * 100)
                subjects_text += f"\n{subject_name}: {data['correct']}/{data['attempts']} ({perc:.1f}%)"
            else:
                subjects_text += f"\n{subject_name}: 0/0 (0%)"
        
        self.subjects_stats_label.text = subjects_text
    
    def clear_stats(self, widget):
        """Сбрасывает статистику."""
        # Подтверждение
        if hasattr(self.main_window, 'confirm_dialog'):
            if self.main_window.confirm_dialog("Сброс статистики", "Вы уверены, что хотите сбросить всю статистику?"):
                self.stats = self.load_stats()  # Загружаем дефолтные
                self.save_stats()
                self.refresh_stats_display()
        else:
            # Простая реализация если confirm_dialog недоступен
            self.stats = self.load_stats()
            self.save_stats()
            self.refresh_stats_display()
            self.settings_status_label.text = "Статистика сброшена"
    
    def save_settings(self, widget):
        """Сохраняет настройки."""
        try:
            # Валидация времени варианта
            try:
                variant_time = int(self.variant_time_input.value)
                if variant_time < 10 or variant_time > 240:
                    self.settings_status_label.text = "Время варианта должно быть от 10 до 240 минут"
                    self.settings_status_label.style.color = "#dc3545"
                    return
            except ValueError:
                self.settings_status_label.text = "Время варианта должно быть числом"
                self.settings_status_label.style.color = "#dc3545"
                return
            
            # Получаем разделитель
            delimiter_text = self.delimiter_selection.value
            if delimiter_text == "Запятая (,)":
                delimiter = ","
            elif delimiter_text == "Точка с запятой (;)":
                delimiter = ";"
            elif delimiter_text == "Табуляция (\\t)":
                delimiter = "\t"
            else:
                delimiter = ","
            
            self.settings = {
                "csv_url": self.csv_url_input.value,
                "delimiter": delimiter,
                "auto_check": self.auto_check_switch.value,
                "variant_time": variant_time
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.settings_status_label.text = "Настройки сохранены!"
            self.settings_status_label.style.color = "#28a745"
            
        except Exception as e:
            self.settings_status_label.text = f"Ошибка сохранения: {e}"
            self.settings_status_label.style.color = "#dc3545"
    
    def close_app(self, widget):
        """Закрывает приложение."""
        self.main_window.close()
    
    def on_window_close(self, window):
        """Обработчик закрытия окна."""
        # Сохраняем настройки при закрытии
        try:
            self.save_settings(None)
            self.save_stats()
        except:
            pass
        return True

def main():
    return EGEShpargalka('EGE Шпаргалка', 'org.ege.shpargalka')

if __name__ == '__main__':
    app = main()
    app.main_loop()