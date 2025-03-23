import json
import os
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox,
    QCheckBox, QStackedWidget, QListWidget, QAbstractItemView, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen
from googletrans import Translator
from huggingface_hub import InferenceClient
import mysql.connector


# Klasa do zarządzania połączeniem z bazą danych
class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Połączono z bazą danych!")
        except mysql.connector.Error as err:
            print(f"Błąd połączenia z bazą danych: {err}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Rozłączono z bazą danych.")

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor
        except mysql.connector.Error as err:
            print(f"Błąd wykonania zapytania: {err}")
            return None
        finally:
            cursor.close()

    def fetch_one(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchone()  # Odczytaj wynik
            return result
        except mysql.connector.Error as err:
            print(f"Błąd wykonania zapytania: {err}")
            return None
        finally:
            cursor.close()  # Zamknij kursor

    def fetch_all(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchall()  # Odczytaj wszystkie wyniki
            return result
        except mysql.connector.Error as err:
            print(f"Błąd wykonania zapytania: {err}")
            return []
        finally:
            cursor.close()  # Zamknij kursor


# Funkcja do generowania przykładowych zdań
def generate_example_sentence(word, language):
    try:
        client = InferenceClient(
            model="gpt2",
            token="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"
        )
        forbidden_words = ["słowo", "słowo", "słowo"]
        if any(forbidden_word in word.lower() for forbidden_word in forbidden_words):
            return "Przykładowe zdanie nie może być wygenerowane dla tego słowa."

        prompt = f"Create a short, example sentence with the word '{word}'"
        generated_text = client.text_generation(
            prompt,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True,
            top_k=50,
            top_p=0.95,
        )

        sentence = generated_text.strip()
        if not sentence.endswith("."):
            sentence += "."

        target_language = get_language_code(language)
        if target_language != "en":
            translator = Translator()
            sentence = translator.translate(sentence, dest=target_language).text

        return sentence

    except Exception as e:
        print(f"Błąd generowania: {str(e)}")
        return f"Błąd generowania: {str(e)}"


# Funkcja do pobierania kodu języka
def get_language_code(language_name):
    language_codes = {
        "Angielski": "en",
        "Hiszpański": "es",
        "Francuski": "fr",
        "Niemiecki": "de",
        "Włoski": "it",
        "Polski": "pl",
        "Portugalski": "pt",
        "Rosyjski": "ru",
        "Chiński": "zh-CN",
        "Japoński": "ja",
        "Koreański": "ko",
        "Arabski": "ar",
        "Turecki": "tr",
        "Holenderski": "nl",
        "Hindi": "hi",
        "Bengalski": "bn",
        "Portugalski (Brazylia)": "pt-BR",
        "Wietnamski": "vi",
        "Tajski": "th",
        "Grecki": "el",
        "Czeski": "cs",
        "Szwedzki": "sv",
        "Duński": "da",
        "Fiński": "fi",
        "Norweski": "no",
        "Węgierski": "hu",
        "Hebrajski": "he",
        "Perski": "fa",
        "Malajski": "ms",
        "Indonezyjski": "id",
        "Filipiński": "tl",
        "Ukraiński": "uk",
        "Rumuński": "ro",
        "Słowacki": "sk",
        "Kataloński": "ca",
        "Serbski": "sr",
        "Chorwacki": "hr",
        "Bułgarski": "bg",
        "Litewski": "lt",
        "Łotewski": "lv",
        "Estoński": "et",
        "Słoweński": "sl",
        "Albański": "sq",
        "Macedoński": "mk",
        "Afrikaans": "af",
        "Suahili": "sw",
        "Zulu": "zu",
        "Xhosa": "xh",
        "Irlandzki": "ga"
    }
    return language_codes.get(language_name, "en")


# Główna klasa aplikacji
class LanguageLearningApp(QWidget):
    def __init__(self):
        super().__init__()
        self.translator = Translator()
        self.correct_answers = 0
        self.wrong_answers = 0
        self.words_learned = set()
        self.dark_theme = True
        self.setWindowTitle("Talkie")
        self.setMinimumSize(300, 500)
        self.apply_theme()
        self.data_file = "flashcards.json"
        self.users_file = "users.json"
        self.load_data()
        self.current_user = None

        # Połączenie z bazą danych
        self.db_manager = DatabaseManager(
            host="localhost",
            user="root",  # Domyślny użytkownik XAMPP
            password="",  # Domyślne hasło XAMPP
            database="language_learning"  # Nazwa bazy danych
        )
        self.db_manager.connect()

        self.layout = QHBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def apply_theme(self):
        if self.dark_theme:
            self.setStyleSheet("""
                QWidget { 
                    background-color: #2E3440; 
                    color: #D8DEE9; 
                    font-family: 'Roboto', sans-serif; 
                    border-radius: 8px; 
                }
                QLabel { 
                    font-size: 20px; 
                    color: #ECEFF4; 
                }
                QPushButton { 
                    background-color: #4C566A; 
                    color: #ECEFF4; 
                    border-radius: 8px; 
                    padding: 10px; 
                    font-size: 16px; 
                    font-weight: bold; 
                    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); 
                }
                QPushButton:hover { 
                    background-color: #5E81AC; 
                }
                QLineEdit, QComboBox { 
                    border: 1px solid #4C566A; 
                    padding: 8px; 
                    border-radius: 5px; 
                    background-color: #3B4252; 
                    font-size: 16px; 
                    color: #ECEFF4; 
                }
                QTabWidget::pane { 
                    border: 1px solid #4C566A; 
                    border-radius: 8px; 
                    background-color: #3B4252; 
                }
                QTabBar::tab { 
                    background: #4C566A; 
                    border: 1px solid #4C566A; 
                    padding: 10px; 
                    border-top-left-radius: 8px; 
                    border-top-right-radius: 8px; 
                    font-size: 16px; 
                    color: #ECEFF4; 
                }
                QTabBar::tab:selected { 
                    background: #5E81AC; 
                    color: #ECEFF4; 
                }
                QTabBar::tab:hover { 
                    background: #81A1C1; 
                }
                QTableWidget { 
                    border: 1px solid #4C566A; 
                    background-color: #3B4252; 
                    font-size: 16px; 
                    border-radius: 8px; 
                    color: #ECEFF4; 
                }
                QTableWidget::item { 
                    padding: 10px; 
                }
                QTableWidget::item:selected { 
                    background-color: #5E81AC; 
                }
                QHeaderView::section {
                    background-color: #4C566A;
                    color: #ECEFF4;
                    padding: 5px;
                    border: none;
                }
                QSplitter::handle {
                    background-color: #4C566A;
                }
                QListWidget {
                    background-color: #3B4252;
                    border: 1px solid #4C566A;
                    border-radius: 8px;
                    color: #ECEFF4;
                }
                QListWidget::item {
                    padding: 10px;
                    border-radius: 8px;
                }
                QListWidget::item:selected {
                    background-color: #5E81AC;
                }
                QSlider::groove:horizontal {
                    background: #4C566A;
                    height: 10px;
                    border-radius: 5px;
                }
                QSlider::handle:horizontal {
                    background: #81A1C1;
                    width: 20px;
                    height: 20px;
                    margin: -5px 0;
                    border-radius: 10px;
                }
                QCheckBox {
                    font-size: 16px;
                    color: #ECEFF4;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    border: 2px solid #4C566A;
                }
                QCheckBox::indicator:checked {
                    background-color: #5E81AC;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget { 
                    background-color: #F5F5F5; 
                    color: #333; 
                    font-family: 'Roboto', sans-serif; 
                    border-radius: 8px; 
                }
                QLabel { 
                    font-size: 20px; 
                    color: #444; 
                }
                QPushButton { 
                    background-color: #1E88E5; 
                    color: white; 
                    border-radius: 8px; 
                    padding: 10px; 
                    font-size: 16px; 
                    font-weight: bold; 
                    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); 
                }
                QPushButton:hover { 
                    background-color: #1565C0; 
                }
                QLineEdit, QComboBox { 
                    border: 1px solid #CCC; 
                    padding: 8px; 
                    border-radius: 5px; 
                    background-color: #FFF; 
                    font-size: 16px; 
                }
                QTabWidget::pane { 
                    border: 1px solid #CCC; 
                    border-radius: 8px; 
                    background-color: #FFF; 
                }
                QTabBar::tab { 
                    background: #D1E3FF; 
                    border: 1px solid #CCC; 
                    padding: 10px; 
                    border-top-left-radius: 8px; 
                    border-top-right-radius: 8px; 
                    font-size: 16px; 
                }
                QTabBar::tab:selected { 
                    background: #1E88E5; 
                    color: white; 
                }
                QTabBar::tab:hover { 
                    background: #A0C4FF; 
                }
                QTableWidget { 
                    border: 1px solid #DDD; 
                    background-color: #FFF; 
                    font-size: 16px; 
                    border-radius: 8px; 
                }
                QTableWidget::item { 
                    padding: 10px; 
                }
                QTableWidget::item:selected { 
                    background-color: #B3E5FC; 
                }
                QHeaderView::section {
                    background-color: #D1E3FF;
                    color: #333;
                    padding: 5px;
                    border: none;
                }
                QSplitter::handle {
                    background-color: #CCC;
                }
                QListWidget {
                    background-color: #FFF;
                    border: 1px solid #CCC;
                    border-radius: 8px;
                    color: #333;
                }
                QListWidget::item {
                    padding: 10px;
                    border-radius: 8px;
                }
                QListWidget::item:selected {
                    background-color: #1E88E5;
                    color: white;
                }
                QSlider::groove:horizontal {
                    background: #D1E3FF;
                    height: 10px;
                    border-radius: 5px;
                }
                QSlider::handle:horizontal {
                    background: #1E88E5;
                    width: 20px;
                    height: 20px;
                    margin: -5px 0;
                    border-radius: 10px;
                }
                QCheckBox {
                    font-size: 16px;
                    color: #333;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    border: 2px solid #CCC;
                }
                QCheckBox::indicator:checked {
                    background-color: #1E88E5;
                }
            """)

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.apply_theme()
        self.update_account_section_theme()

    def update_account_section_theme(self):
        if self.dark_theme:
            self.account_section.setStyleSheet("background-color: #4C566A; border-radius: 8px; padding: 10px;")
        else:
            self.account_section.setStyleSheet("background-color: #D1E3FF; border-radius: 8px; padding: 10px;")

    def setup_ui(self):
        # Lewy panel nawigacyjny
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        left_panel.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Talkie", self)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        left_panel.addWidget(title)

        self.tab_list = QListWidget(self)
        self.tab_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tab_list.addItem("Fiszki")
        self.tab_list.addItem("Tworzenie")
        self.tab_list.addItem("Quiz")
        self.tab_list.addItem("Postęp")
        self.tab_list.addItem("Konto")
        self.tab_list.setCurrentRow(0)
        self.tab_list.currentRowChanged.connect(self.change_tab)
        left_panel.addWidget(self.tab_list)

        # Sekcja "Konto"
        self.account_section = QWidget()
        self.update_account_section_theme()
        account_layout = QVBoxLayout()
        self.account_label = QLabel("Konto 👤", self)
        account_layout.addWidget(self.account_label)
        self.account_button = QPushButton("Pokaż informacje", self)
        self.account_button.clicked.connect(self.show_account_info)
        account_layout.addWidget(self.account_button)
        self.account_section.setLayout(account_layout)
        left_panel.addWidget(self.account_section)

        self.toggle_theme_button = QPushButton("🌙", self)
        self.toggle_theme_button.clicked.connect(self.toggle_theme)
        left_panel.addWidget(self.toggle_theme_button)

        self.layout.addLayout(left_panel, 1)

        # Główny obszar zawartości
        self.stacked_widget = QStackedWidget(self)
        self.layout.addWidget(self.stacked_widget, 4)

        self.flashcard_tab = QWidget()
        self.setup_flashcard_tab()
        self.stacked_widget.addWidget(self.flashcard_tab)

        self.creation_tab = QWidget()
        self.setup_creation_tab()
        self.stacked_widget.addWidget(self.creation_tab)

        self.quiz_tab = QWidget()
        self.setup_quiz_tab()
        self.stacked_widget.addWidget(self.quiz_tab)

        self.progress_tab = QWidget()
        self.setup_progress_tab()
        self.stacked_widget.addWidget(self.progress_tab)

        self.account_tab = QWidget()
        self.setup_account_tab()
        self.stacked_widget.addWidget(self.account_tab)

        self.update_category_selector()

    def show_account_info(self):
        if self.current_user:
            QMessageBox.information(self, "Konto", f"Witaj {self.current_user['username']}!\nEmail: {self.current_user['email']}")
        else:
            QMessageBox.warning(self, "Błąd", "Nie jesteś zalogowany!")

    def change_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                self.categories = json.load(file)
        else:
            self.categories = {}

        if os.path.exists(self.users_file):
            with open(self.users_file, "r", encoding="utf-8") as file:
                self.users = json.load(file)
        else:
            self.users = []

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(self.categories, file, indent=4, ensure_ascii=False)
        with open(self.users_file, "w", encoding="utf-8") as file:
            json.dump(self.users, file, indent=4, ensure_ascii=False)

    def setup_flashcard_tab(self):
        layout = QVBoxLayout()
        category_layout = QHBoxLayout()
        self.category_selector = QComboBox(self)
        self.category_selector.currentTextChanged.connect(self.update_subcategory_selector)
        category_layout.addWidget(QLabel("Język:", self))
        category_layout.addWidget(self.category_selector)
        self.subcategory_selector = QComboBox(self)
        self.subcategory_selector.currentTextChanged.connect(self.update_flashcard_table)
        category_layout.addWidget(QLabel("Podkategoria:", self))
        category_layout.addWidget(self.subcategory_selector)
        layout.addLayout(category_layout)

        self.flashcard_table = QTableWidget(self)
        self.flashcard_table.setColumnCount(3)
        self.flashcard_table.setHorizontalHeaderLabels(["Słowo", "Tłumaczenie", "Przykładowe zdanie"])
        self.flashcard_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.flashcard_table)

        edit_delete_layout = QHBoxLayout()
        self.edit_button = QPushButton("✏️", self)
        self.edit_button.clicked.connect(self.show_edit_area)
        edit_delete_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("🗑️", self)
        self.delete_button.clicked.connect(self.delete_flashcard)
        edit_delete_layout.addWidget(self.delete_button)

        layout.addLayout(edit_delete_layout)

        # Pola do edycji fiszek (ukryte na początku)
        self.edit_area = QWidget()
        edit_area_layout = QVBoxLayout()
        self.edit_word_input = QLineEdit(self)
        self.edit_word_input.setPlaceholderText("Edytuj słowo")
        edit_area_layout.addWidget(self.edit_word_input)

        self.edit_translation_input = QLineEdit(self)
        self.edit_translation_input.setPlaceholderText("Edytuj tłumaczenie")
        edit_area_layout.addWidget(self.edit_translation_input)

        self.edit_example_sentence_input = QLineEdit(self)
        self.edit_example_sentence_input.setPlaceholderText("Edytuj przykładowe zdanie")
        edit_area_layout.addWidget(self.edit_example_sentence_input)

        self.save_edit_button = QPushButton("Zapisz zmiany", self)
        self.save_edit_button.clicked.connect(self.save_edited_flashcard)
        edit_area_layout.addWidget(self.save_edit_button)

        self.edit_area.setLayout(edit_area_layout)
        self.edit_area.hide()  # Ukryj interfejs edycji na początku
        layout.addWidget(self.edit_area)

        self.flashcard_tab.setLayout(layout)

    def show_edit_area(self):
        selected_row = self.flashcard_table.currentRow()
        if selected_row >= 0:
            category = self.category_selector.currentText()
            subcategory = self.subcategory_selector.currentText()
            flashcard = self.categories[category][subcategory][selected_row]
            self.edit_word_input.setText(flashcard["word"])
            self.edit_translation_input.setText(flashcard["translation"])
            self.edit_example_sentence_input.setText(flashcard["example_sentence"])
            self.edit_area.show()  # Pokaż interfejs edycji
        else:
            QMessageBox.warning(self, "Błąd", "Nie wybrano fiszki do edycji!")

    def save_edited_flashcard(self):
        selected_row = self.flashcard_table.currentRow()
        if selected_row >= 0:
            category = self.category_selector.currentText()
            subcategory = self.subcategory_selector.currentText()
            flashcard = self.categories[category][subcategory][selected_row]
            flashcard["word"] = self.edit_word_input.text().strip()
            flashcard["translation"] = self.edit_translation_input.text().strip()
            flashcard["example_sentence"] = self.edit_example_sentence_input.text().strip()
            self.save_data()
            self.update_flashcard_table()
            self.edit_area.hide()  # Ukryj interfejs edycji po zapisaniu
            QMessageBox.information(self, "Sukces", "Fiszka została zaktualizowana!")
        else:
            QMessageBox.warning(self, "Błąd", "Nie wybrano fiszki do edycji!")

    def setup_creation_tab(self):
        layout = QVBoxLayout()
        self.word_input = QLineEdit(self)
        self.word_input.setPlaceholderText("Słowo")
        self.translation_input = QLineEdit(self)
        self.translation_input.setPlaceholderText("Tłumaczenie")
        self.example_sentence_input = QLineEdit(self)
        self.example_sentence_input.setPlaceholderText("Przykładowe zdanie")
        self.category_selector_creation = QComboBox(self)
        self.category_selector_creation.addItems(self.categories.keys())
        self.category_selector_creation.currentTextChanged.connect(self.update_subcategory_selector_creation)
        self.subcategory_selector_creation = QComboBox(self)
        self.update_subcategory_selector_creation()

        # Przełącznik automatycznego tłumaczenia
        self.auto_translate_checkbox = QCheckBox("Automatyczne tłumaczenie", self)
        layout.addWidget(self.auto_translate_checkbox)

        layout.addWidget(QLabel("Dodaj fiszkę:"))
        layout.addWidget(QLabel("Kategoria:"))
        layout.addWidget(self.category_selector_creation)
        layout.addWidget(QLabel("Podkategoria:"))
        layout.addWidget(self.subcategory_selector_creation)
        layout.addWidget(self.word_input)
        layout.addWidget(self.translation_input)
        layout.addWidget(self.example_sentence_input)
        self.add_flashcard_button = QPushButton("Dodaj fiszkę", self)
        self.add_flashcard_button.clicked.connect(self.add_flashcard)
        layout.addWidget(self.add_flashcard_button)

        # Przyciski do zarządzania podkategoriami i językami
        buttons_layout = QHBoxLayout()
        self.delete_subcategory_button = QPushButton("Usuń podkategorię", self)
        self.delete_subcategory_button.clicked.connect(self.delete_subcategory)
        buttons_layout.addWidget(self.delete_subcategory_button)

        self.add_subcategory_button = QPushButton("Dodaj podkategorię", self)
        self.add_subcategory_button.clicked.connect(self.add_subcategory)
        buttons_layout.addWidget(self.add_subcategory_button)

        self.delete_category_button = QPushButton("Usuń język", self)
        self.delete_category_button.clicked.connect(self.delete_category)
        buttons_layout.addWidget(self.delete_category_button)

        self.add_category_button = QPushButton("Dodaj język", self)
        self.add_category_button.clicked.connect(self.add_category)
        buttons_layout.addWidget(self.add_category_button)

        layout.addLayout(buttons_layout)

        self.creation_feedback_label = QLabel("", self)
        layout.addWidget(self.creation_feedback_label)
        self.creation_tab.setLayout(layout)

    def setup_quiz_tab(self):
        layout = QVBoxLayout()
        self.language_selector = QComboBox(self)
        self.language_selector.addItems(self.categories.keys())
        self.language_selector.currentTextChanged.connect(self.update_quiz_subcategory_selector)
        layout.addWidget(QLabel("Wybierz język do quizu:"))
        layout.addWidget(self.language_selector)
        self.quiz_subcategory_selector = QComboBox(self)
        layout.addWidget(QLabel("Wybierz podkategorię do quizu:"))
        layout.addWidget(self.quiz_subcategory_selector)
        self.update_quiz_subcategory_selector()
        self.quiz_question_label = QLabel("Pytanie pojawi się tutaj", self)
        self.quiz_question_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.quiz_question_label)
        self.user_answer_input = QLineEdit(self)
        self.user_answer_input.setPlaceholderText("Wpisz swoją odpowiedź tutaj")
        layout.addWidget(self.user_answer_input)
        self.submit_answer_button = QPushButton("Zatwierdź odpowiedź", self)
        self.submit_answer_button.clicked.connect(self.check_quiz_answer)
        layout.addWidget(self.submit_answer_button)
        self.start_quiz_button = QPushButton("Rozpocznij quiz", self)
        self.start_quiz_button.clicked.connect(self.start_quiz)
        layout.addWidget(self.start_quiz_button)
        self.timer_label = QLabel("Pozostały czas: 30", self)
        layout.addWidget(self.timer_label)
        self.quiz_feedback_label = QLabel("", self)
        layout.addWidget(self.quiz_feedback_label)
        self.quiz_tab.setLayout(layout)

    def setup_progress_tab(self):
        layout = QVBoxLayout()
        self.progress_label = QLabel("Twój postęp", self)
        self.progress_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.progress_label)
        self.words_learned_label = QLabel("Słowa nauczone: 0", self)
        layout.addWidget(self.words_learned_label)
        self.quiz_performance_label = QLabel("Wyniki quizu: 0 poprawnych, 0 błędnych", self)
        layout.addWidget(self.quiz_performance_label)
        self.progress_tab.setLayout(layout)

    def setup_account_tab(self):
        layout = QVBoxLayout()
        self.login_label = QLabel("Logowanie", self)
        self.login_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.login_label)

        self.login_username_input = QLineEdit(self)
        self.login_username_input.setPlaceholderText("Nazwa użytkownika")
        layout.addWidget(self.login_username_input)

        self.login_password_input = QLineEdit(self)
        self.login_password_input.setPlaceholderText("Hasło")
        self.login_password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.login_password_input)

        self.login_button = QPushButton("Zaloguj się", self)
        self.login_button.clicked.connect(self.login_user)
        layout.addWidget(self.login_button)

        self.register_label = QLabel("Rejestracja", self)
        self.register_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.register_label)

        self.register_username_input = QLineEdit(self)
        self.register_username_input.setPlaceholderText("Nazwa użytkownika")
        layout.addWidget(self.register_username_input)

        self.register_email_input = QLineEdit(self)
        self.register_email_input.setPlaceholderText("Email")
        layout.addWidget(self.register_email_input)

        self.register_password_input = QLineEdit(self)
        self.register_password_input.setPlaceholderText("Hasło")
        self.register_password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.register_password_input)

        self.register_button = QPushButton("Zarejestruj się", self)
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)

        self.account_tab.setLayout(layout)

    def login_user(self):
        username = self.login_username_input.text().strip()
        password = self.login_password_input.text().strip()
        if username and password:
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            user = self.db_manager.fetch_one(query, (username, password))
            if user:
                self.current_user = {
                    "id": user[0],  # Pobierz identyfikator użytkownika
                    "username": user[1],
                    "email": user[2],
                    "password": user[3]
                }
                QMessageBox.information(self, "Sukces", "Zalogowano pomyślnie!")
            else:
                QMessageBox.warning(self, "Błąd", "Nieprawidłowa nazwa użytkownika lub hasło!")
        else:
            QMessageBox.warning(self, "Błąd", "Wprowadź nazwę użytkownika i hasło!")

    def register_user(self):
        username = self.register_username_input.text().strip()
        email = self.register_email_input.text().strip()
        password = self.register_password_input.text().strip()
        if username and email and password:
            query = "SELECT * FROM users WHERE username = %s"
            existing_user = self.db_manager.fetch_one(query, (username,))
            if existing_user:
                QMessageBox.warning(self, "Błąd", "Użytkownik o tej nazwie już istnieje!")
                return
            query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            self.db_manager.execute_query(query, (username, email, password))
            # Pobierz identyfikator nowo zarejestrowanego użytkownika
            query = "SELECT id FROM users WHERE username = %s"
            user_id = self.db_manager.fetch_one(query, (username,))[0]
            self.current_user = {
                "id": user_id,
                "username": username,
                "email": email,
                "password": password
            }
            QMessageBox.information(self, "Sukces", "Zarejestrowano pomyślnie!")
        else:
            QMessageBox.warning(self, "Błąd", "Wszystkie pola muszą być wypełnione!")

    def update_category_selector(self):
        self.category_selector.clear()
        self.category_selector.addItems(self.categories.keys())
        self.category_selector_creation.clear()
        self.category_selector_creation.addItems(self.categories.keys())
        self.update_subcategory_selector()

    def update_subcategory_selector(self):
        category = self.category_selector.currentText()
        self.subcategory_selector.clear()
        if category in self.categories:
            self.subcategory_selector.addItems(self.categories[category].keys())
        self.update_flashcard_table()

    def update_subcategory_selector_creation(self):
        category = self.category_selector_creation.currentText()
        self.subcategory_selector_creation.clear()
        if category in self.categories:
            self.subcategory_selector_creation.addItems(self.categories[category].keys())

    def update_quiz_subcategory_selector(self):
        category = self.language_selector.currentText()
        self.quiz_subcategory_selector.clear()
        if category in self.categories:
            self.quiz_subcategory_selector.addItems(self.categories[category].keys())

    def update_flashcard_table(self):
        if not self.current_user:
            return

        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        if category in self.categories and subcategory in self.categories[category]:
            flashcards = [fc for fc in self.categories[category][subcategory] if fc.get("user_id") == self.current_user['id']]
            self.flashcard_table.setRowCount(len(flashcards))
            for i, flashcard in enumerate(flashcards):
                self.flashcard_table.setItem(i, 0, QTableWidgetItem(flashcard["word"]))
                self.flashcard_table.setItem(i, 1, QTableWidgetItem(flashcard["translation"]))
                self.flashcard_table.setItem(i, 2, QTableWidgetItem(flashcard["example_sentence"]))

    def search_flashcards(self):
        search_text = self.search_input.text().lower()
        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        if category in self.categories and subcategory in self.categories[category]:
            flashcards = self.categories[category][subcategory]
            self.flashcard_table.setRowCount(0)
            for flashcard in flashcards:
                if search_text in flashcard["word"].lower() or search_text in flashcard["translation"].lower():
                    row_position = self.flashcard_table.rowCount()
                    self.flashcard_table.insertRow(row_position)
                    self.flashcard_table.setItem(row_position, 0, QTableWidgetItem(flashcard["word"]))
                    self.flashcard_table.setItem(row_position, 1, QTableWidgetItem(flashcard["translation"]))
                    self.flashcard_table.setItem(row_position, 2, QTableWidgetItem(flashcard["example_sentence"]))

    def update_progress_labels(self):
        self.words_learned_label.setText(f"Słowa nauczone: {len(self.words_learned)}")
        self.quiz_performance_label.setText(f"Wyniki quizu: {self.correct_answers} poprawnych, {self.wrong_answers} błędnych")

    def add_flashcard(self):
        if not self.current_user:
            QMessageBox.warning(self, "Błąd", "Musisz być zalogowany, aby dodać fiszkę!")
            return

        category = self.category_selector_creation.currentText()
        subcategory = self.subcategory_selector_creation.currentText()
        word = self.word_input.text().strip()
        translation = self.translation_input.text().strip()
        example_sentence = self.example_sentence_input.text().strip()

        if self.auto_translate_checkbox.isChecked() and not translation:
            target_language = get_language_code(category)
            try:
                translation = self.translator.translate(word, dest=target_language).text
            except Exception as e:
                self.creation_feedback_label.setText(f"Błąd tłumaczenia: {str(e)}")
                return

        if not example_sentence:
            try:
                example_sentence = generate_example_sentence(word, category)
            except Exception as e:
                self.creation_feedback_label.setText(f"Błąd generowania zdania: {str(e)}")
                return

        if word and translation and category and subcategory:
            # Zapisz fiszkę w bazie danych
            query = "INSERT INTO flashcards (category, subcategory, word, translation, example_sentence, user_id) VALUES (%s, %s, %s, %s, %s, %s)"
            self.db_manager.execute_query(query, (category, subcategory, word, translation, example_sentence, self.current_user['id']))

            # Zapisz fiszkę w pliku JSON
            if category not in self.categories:
                self.categories[category] = {}
            if subcategory not in self.categories[category]:
                self.categories[category][subcategory] = []
            self.categories[category][subcategory].append({
                "word": word,
                "translation": translation,
                "example_sentence": example_sentence,
                "user_id": self.current_user['id']
            })
            self.save_data()

            self.creation_feedback_label.setText(f"Fiszka '{word}' została dodana!")
            self.word_input.clear()
            self.translation_input.clear()
            self.example_sentence_input.clear()
        else:
            self.creation_feedback_label.setText("Wszystkie pola muszą być wypełnione!")

    def add_subcategory(self):
        category = self.category_selector_creation.currentText()
        if category:
            subcategory_name, ok = QInputDialog.getText(self, "Dodaj podkategorię", "Nowa podkategoria")
            if ok and subcategory_name:
                if subcategory_name not in self.categories[category]:
                    self.categories[category][subcategory_name] = []
                    self.save_data()
                    self.update_subcategory_selector_creation()
                    QMessageBox.information(self, "Sukces", f"Podkategoria '{subcategory_name}' została dodana!")
                else:
                    QMessageBox.warning(self, "Błąd", "Ta podkategoria już istnieje!")

    def add_category(self):
        category_name, ok = QInputDialog.getText(self, "Dodaj język", "Nowy język")
        if ok and category_name:
            if category_name not in self.categories:
                self.categories[category_name] = {}
                self.save_data()
                self.update_category_selector()
                QMessageBox.information(self, "Sukces", f"Język '{category_name}' został dodany!")
            else:
                QMessageBox.warning(self, "Błąd", "Ten język już istnieje!")

    def delete_flashcard(self):
        selected_row = self.flashcard_table.currentRow()
        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        if selected_row >= 0 and category in self.categories and subcategory in self.categories[category]:
            confirm = QMessageBox.question(self, "Potwierdzenie", "Czy na pewno chcesz usunąć tę fiszkę?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                del self.categories[category][subcategory][selected_row]
                self.save_data()
                self.update_flashcard_table()
                QMessageBox.information(self, "Sukces", "Fiszka została usunięta!")

    def delete_category(self):
        category = self.category_selector_creation.currentText()
        if category:
            confirm = QMessageBox.question(self, "Potwierdzenie", f"Czy na pewno chcesz usunąć język '{category}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                del self.categories[category]
                self.save_data()
                self.update_category_selector()
                QMessageBox.information(self, "Sukces", f"Język '{category}' został usunięty!")

    def delete_subcategory(self):
        category = self.category_selector_creation.currentText()
        subcategory = self.subcategory_selector_creation.currentText()
        if category and subcategory:
            confirm = QMessageBox.question(self, "Potwierdzenie", f"Czy na pewno chcesz usunąć podkategorię '{subcategory}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                del self.categories[category][subcategory]
                self.save_data()
                self.update_subcategory_selector_creation()
                QMessageBox.information(self, "Sukces", f"Podkategoria '{subcategory}' została usunięta!")

    def check_quiz_answer(self):
        user_answer = self.user_answer_input.text().strip()
        if hasattr(self, 'correct_answer'):
            if user_answer.lower() == self.correct_answer.lower():
                self.quiz_feedback_label.setText("Dobrze!")
                self.correct_answers += 1
                self.words_learned.add(self.correct_answer)
            else:
                self.quiz_feedback_label.setText(f"Źle! Poprawna odpowiedź to: {self.correct_answer}")
                self.wrong_answers += 1
            self.update_progress_labels()
        else:
            self.quiz_feedback_label.setText("Nie było jeszcze pytania.")
        self.user_answer_input.clear()

    def start_quiz(self):
        category = self.language_selector.currentText()
        subcategory = self.quiz_subcategory_selector.currentText()
        if category in self.categories and subcategory in self.categories[category]:
            flashcards = self.categories[category][subcategory]
            if flashcards:
                selected_flashcard = random.choice(flashcards)
                self.quiz_question_label.setText(f"Translate '{selected_flashcard['word']}'")
                self.correct_answer = selected_flashcard['translation']
            else:
                self.quiz_question_label.setText("No flashcards available in this subcategory.")
        else:
            self.quiz_question_label.setText("Invalid category or subcategory selected.")
        self.update_progress_labels()

    def get_language_code(self, language_name):
        language_codes = {
            "Angielski": "en",
            "Hiszpański": "es"
        }
        return language_codes.get(language_name, "en")

    def closeEvent(self, event):
        self.db_manager.disconnect()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    window = LanguageLearningApp()
    window.show()
    app.exec()
