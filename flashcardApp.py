
import json
import os
import random
import sys
from typing import Optional


try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox,
        QCheckBox, QStackedWidget, QListWidget, QAbstractItemView, QScrollArea
    )
    from PySide6.QtCore import Qt, QTimer
    from deep_translator import GoogleTranslator
    from mysql.connector import connect, Error
    import google.generativeai as genai
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please install required packages using:")
    print("pip install PySide6 deep-translator mysql-connector-python google-generativeai")
    sys.exit(1)

# Version requirements
REQUIRED_PACKAGES = {
    'PySide6': '>=6.0.0',
    'deep-translator': '>=1.11.0',
    'huggingface-hub': '>=0.19.0',
    'mysql-connector-python': '>=8.0.0'
}

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
            self.connection = connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Połączono z bazą danych!")
        except Error as err:
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
        except Error as err:
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
        except Error as err:
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
        except Error as err:
            print(f"Błąd wykonania zapytania: {err}")
            return []
        finally:
            cursor.close()  # Zamknij kursor


# Funkcja do generowania przykładowych zdań
def generate_example_sentence(word, language):
    try:
        word_clean = word.strip().lower()
        language_clean = language.strip().lower()

        # Zdefiniowane ręcznie przykładowe zdania
        predefined_sentences = {
            "spać": {
                "angielski": "I want to sleep.",
                "hiszpański": "Quiero dormir.",
                "niemiecki": "Ich möchte schlafen.",
                "francuski": "Je veux dormir.",
                "włoski": "Voglio dormire.",
                "polski": "Chcę spać."
            },
            # Możesz dodać więcej słów:
            "jeść": {
                "angielski": "I want to eat.",
                "hiszpański": "Quiero comer.",
                "niemiecki": "Ich möchte essen.",
                "francuski": "Je veux manger."
            }
        }

        # Jeśli mamy gotowe zdanie – zwróć je
        if word_clean in predefined_sentences and language_clean in predefined_sentences[word_clean]:
            return predefined_sentences[word_clean][language_clean]

        # W przeciwnym razie – użyj Gemini
        genai.configure(api_key="AIzaSyAaOpyMPAi_SDKrb3egTvt90OK0_ULQr30")
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            f"Create a short, natural sentence in {language} using the meaning of the word '{word}'. "
            f"The sentence should be easy to understand and suitable for language learners."
        )

        response = model.generate_content(prompt)
        sentence = response.text.strip()

        if not sentence.endswith((".", "!", "?")):
            sentence += "."

        return sentence

    except Exception as e:
        print(f"Error generating sentence with Gemini API: {str(e)}")
        return "Error generating sentence. Please try again or enter your own example."
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
        self.translator = GoogleTranslator()
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
        self.create_database_tables()
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
        self.tab_list.addItem("Konto") 
        self.tab_list.addItem("Postęp")
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
        self.account_tab = QWidget()
        self.setup_account_tab()
        self.stacked_widget.addWidget(self.account_tab)  # Usunięto zakładkę postęp
        self.update_category_selector()
        self.progress_tab = QWidget()  # Nowa zakładka "Postęp"
        self.setup_progress_tab()  # Metoda do konfiguracji zakładki "Postęp"
        self.stacked_widget.addWidget(self.progress_tab)  # Dodajemy zakładkę "Postęp"
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

        # Add search functionality
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Szukaj...")
        self.search_input.textChanged.connect(self.search_flashcards)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        self.flashcard_table = QTableWidget(self)
        self.flashcard_table.setColumnCount(3)
        self.flashcard_table.setHorizontalHeaderLabels(["Słowo", "Tłumaczenie", "Przykładowe zdanie"])
        self.flashcard_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.flashcard_table)

        edit_delete_layout = QHBoxLayout()
        # Po linii z edit_delete_layout
        refresh_button = QPushButton("Odśwież", self)
        refresh_button.clicked.connect(self.update_flashcard_table)
        edit_delete_layout.addWidget(refresh_button)
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

    def setup_progress_tab(self):
        layout = QVBoxLayout()

        # Nagłówek sekcji
        header_label = QLabel("Historia quizów", self)
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)

        # Tabela do wyświetlania wyników quizów
        self.progress_table = QTableWidget(self)
        self.progress_table.setColumnCount(4)
        self.progress_table.setHorizontalHeaderLabels(["Data", "Poprawne odpowiedzi", "Błędne odpowiedzi", "Całkowite punkty"])
        self.progress_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.progress_table)

        # Przyciski do filtrowania lub resetowania tabeli
        buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Odśwież", self)
        self.refresh_button.clicked.connect(self.update_progress_table)
        buttons_layout.addWidget(self.refresh_button)
        layout.addLayout(buttons_layout)

        # Ustawienie układu
        self.progress_tab.setLayout(layout)

        # Pobierz i wyświetl początkowe dane
        self.update_progress_table()
    
    def update_progress_table(self):
        if not self.current_user:
            return

        try:
            # Pobierz historię quizów z bazy danych
            query = """
            SELECT date, correct_answers, wrong_answers 
            FROM quiz_results 
            WHERE user_id = %s 
            ORDER BY date DESC
            """
            results = self.db_manager.fetch_all(query, (self.current_user['id'],))

            # Wypełnij tabelę
            self.progress_table.setRowCount(len(results))
            for i, result in enumerate(results):
                date = result[0].strftime("%Y-%m-%d %H:%M:%S")
                correct_answers = result[1]
                wrong_answers = result[2]
                total_points = correct_answers - wrong_answers  # Całkowite punkty

                self.progress_table.setItem(i, 0, QTableWidgetItem(date))
                self.progress_table.setItem(i, 1, QTableWidgetItem(str(correct_answers)))
                self.progress_table.setItem(i, 2, QTableWidgetItem(str(wrong_answers)))
                self.progress_table.setItem(i, 3, QTableWidgetItem(str(total_points)))

        except Exception as e:
            print(f"Błąd podczas pobierania historii quizów: {str(e)}")
            QMessageBox.warning(self, "Błąd", "Nie udało się pobrać historii quizów!")
    def change_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)
    
    def show_edit_area(self):
        selected_row = self.flashcard_table.currentRow()
        if selected_row >= 0:
            word = self.flashcard_table.item(selected_row, 0).text()
            translation = self.flashcard_table.item(selected_row, 1).text()
            example_sentence = self.flashcard_table.item(selected_row, 2).text()

            self.edit_word_input.setText(word)
            self.edit_translation_input.setText(translation)
            self.edit_example_sentence_input.setText(example_sentence)
            self.edit_area.show()
        else:
            QMessageBox.warning(self, "Błąd", "Nie wybrano fiszki do edycji!")

    def save_edited_flashcard(self):
        selected_row = self.flashcard_table.currentRow()
        if selected_row >= 0:
            category = self.category_selector.currentText()
            subcategory = self.subcategory_selector.currentText()

            # Aktualizacja w bazie danych
            try:
                word = self.edit_word_input.text().strip()
                translation = self.edit_translation_input.text().strip()
                example_sentence = self.edit_example_sentence_input.text().strip()

                query = """
                UPDATE flashcards 
                SET word = %s, translation = %s, example_sentence = %s
                WHERE category = %s AND subcategory = %s AND word = %s AND user_id = %s
                """
                original_word = self.flashcard_table.item(selected_row, 0).text()
                self.db_manager.execute_query(query, (word, translation, example_sentence,
                                                      category, subcategory, original_word,
                                                      self.current_user['id']))

                # Aktualizacja w pliku JSON
                for idx, flashcard in enumerate(self.categories[category][subcategory]):
                    if (flashcard["word"] == original_word and 
                        flashcard.get("user_id") == self.current_user['id']):

                        self.categories[category][subcategory][idx] = {
                            "word": word,
                            "translation": translation,
                            "example_sentence": example_sentence,
                            "user_id": self.current_user['id']
                        }
                        break
                    
                self.save_data()
                self.update_flashcard_table()
                self.edit_area.hide()
                QMessageBox.information(self, "Sukces", "Fiszka została zaktualizowana!")
            except Exception as e:
                print(f"Błąd podczas edycji fiszki: {str(e)}")
                QMessageBox.warning(self, "Błąd", "Nie udało się zapisać zmian!")
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

        # Wybór języka i podkategorii
        self.language_selector = QComboBox(self)
        self.language_selector.addItems(self.categories.keys())
        self.language_selector.currentTextChanged.connect(self.update_quiz_subcategory_selector)
        layout.addWidget(QLabel("Wybierz język do quizu:"))
        layout.addWidget(self.language_selector)

        self.quiz_subcategory_selector = QComboBox(self)
        layout.addWidget(QLabel("Wybierz podkategorię do quizu:"))
        layout.addWidget(self.quiz_subcategory_selector)
        self.update_quiz_subcategory_selector()

        # Wybór typu quizu
        self.quiz_type_selector = QComboBox(self)
        self.quiz_type_selector.addItems(["Pytania otwarte", "Testy ABCD"])
        layout.addWidget(QLabel("Typ quizu:"))
        layout.addWidget(self.quiz_type_selector)

        # Opcja losowości pytań
        self.random_questions_checkbox = QCheckBox("Losowe pytania", self)
        self.random_questions_checkbox.setChecked(True)
        layout.addWidget(self.random_questions_checkbox)

        # Etykieta pytania
        self.quiz_question_label = QLabel("Pytanie pojawi się tutaj", self)
        self.quiz_question_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.quiz_question_label)

        # Pole odpowiedzi użytkownika
        self.user_answer_input = QLineEdit(self)
        self.user_answer_input.setPlaceholderText("Wpisz swoją odpowiedź tutaj")
        layout.addWidget(self.user_answer_input)

        # Przyciski odpowiedzi (dla trybu ABCD)
        self.answer_buttons_layout = QHBoxLayout()
        self.answer_buttons = []
        for i in range(4):
            button = QPushButton(f"Odpowiedź {chr(65 + i)}", self)
            button.setVisible(False)
            button.clicked.connect(lambda _, idx=i: self.check_quiz_answer_abcd(idx))
            self.answer_buttons_layout.addWidget(button)
            self.answer_buttons.append(button)
        layout.addLayout(self.answer_buttons_layout)

        # Przycisk zatwierdzenia odpowiedzi
        self.submit_answer_button = QPushButton("Zatwierdź odpowiedź", self)
        self.submit_answer_button.clicked.connect(self.check_quiz_answer)
        layout.addWidget(self.submit_answer_button)

        # Przycisk rozpoczęcia quizu
        self.start_quiz_button = QPushButton("Rozpocznij quiz", self)
        self.start_quiz_button.clicked.connect(self.start_quiz)
        layout.addWidget(self.start_quiz_button)

        # Timer
        self.timer_label = QLabel("Pozostały czas: 30", self)
        layout.addWidget(self.timer_label)

        # Feedback
        self.quiz_feedback_label = QLabel("", self)
        layout.addWidget(self.quiz_feedback_label)

        # Ustawienie układu
        self.quiz_tab.setLayout(layout)
        self.quiz_timer = None
        self.quiz_time_left = 30

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
        try:
            # Get flashcards from database
            query = """
            SELECT word, translation, example_sentence 
            FROM flashcards 
            WHERE category = %s AND subcategory = %s AND user_id = %s
            """
            flashcards = self.db_manager.fetch_all(query, (category, subcategory, self.current_user['id']))
            self.flashcard_table.setRowCount(len(flashcards))
            for i, flashcard in enumerate(flashcards):
                self.flashcard_table.setItem(i, 0, QTableWidgetItem(flashcard[0]))
                self.flashcard_table.setItem(i, 1, QTableWidgetItem(flashcard[1]))
                self.flashcard_table.setItem(i, 2, QTableWidgetItem(flashcard[2]))
        except Exception as e:
            print(f"Error updating flashcard table: {str(e)}")
            QMessageBox.warning(self, "Błąd", "Nie udało się zaktualizować tabeli fiszek!")

    def search_flashcards(self):
        if not self.current_user:
            return
        search_text = self.search_input.text().lower()
        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        try:
            # Search in database
            query = """
            SELECT word, translation, example_sentence 
            FROM flashcards 
            WHERE category = %s AND subcategory = %s AND user_id = %s
            AND (LOWER(word) LIKE %s OR LOWER(translation) LIKE %s)
            """
            search_pattern = f"%{search_text}%"
            flashcards = self.db_manager.fetch_all(query, (category, subcategory, self.current_user['id'], search_pattern, search_pattern))
            self.flashcard_table.setRowCount(len(flashcards))
            for i, flashcard in enumerate(flashcards):
                self.flashcard_table.setItem(i, 0, QTableWidgetItem(flashcard[0]))
                self.flashcard_table.setItem(i, 1, QTableWidgetItem(flashcard[1]))
                self.flashcard_table.setItem(i, 2, QTableWidgetItem(flashcard[2]))
        except Exception as e:
            print(f"Error searching flashcards: {str(e)}")
            QMessageBox.warning(self, "Błąd", "Nie udało się wyszukać fiszek!")

    def translate_text(self, text, target_language):
        try:
            translator = GoogleTranslator(source='auto', target=target_language)
            # Wykonaj tłumaczenie
            translation = translator.translate(text)
            # Jeśli tłumaczenie się powiedzie, zwróć przetłumaczony tekst
            if translation:
                return translation
            else:
                raise Exception("Translation failed - no result received")
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Zwróć oryginalny tekst, jeśli tłumaczenie się nie powiedzie

    def create_database_tables(self):
        try:
            # Create users table
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.db_manager.execute_query(create_users_table)

            # Create flashcards table
            create_flashcards_table = """
            CREATE TABLE IF NOT EXISTS flashcards (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(255) NOT NULL,
                subcategory VARCHAR(255) NOT NULL,
                word VARCHAR(255) NOT NULL,
                translation VARCHAR(255) NOT NULL,
                example_sentence TEXT,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
            self.db_manager.execute_query(create_flashcards_table)

            # Create quiz results table
            create_quiz_results_table = """
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                correct_answers INT NOT NULL,
                wrong_answers INT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE            """
            self.db_manager.execute_query(create_quiz_results_table)
            print("Tabele bazy danych zostały utworzone pomyślnie!")
        except Exception as e:
            print(f"Błąd podczas tworzenia tabel: {str(e)}")
            QMessageBox.critical(self, "Błąd", "Nie udało się utworzyć tabel w bazie danych!")

    def add_flashcard(self):
        if not self.current_user:
            QMessageBox.warning(self, "Błąd", "Musisz być zalogowany, aby dodać fiszkę!")
            return
        category = self.category_selector_creation.currentText()
        subcategory = self.subcategory_selector_creation.currentText()
        word = self.word_input.text().strip()
        translation = self.translation_input.text().strip()
        example_sentence = self.example_sentence_input.text().strip()

        # Poprawione warunki dodawania fiszek
        if not word or not category or not subcategory:
            self.creation_feedback_label.setText("Słowo, kategoria i podkategoria są wymagane!")
            return

        try:
            # Automatyczne tłumaczenie jeśli zaznaczono odpowiednią opcję
            if self.auto_translate_checkbox.isChecked():
                target_language = get_language_code(category)
                if not translation:
                    translation = self.translate_text(word, target_language)
                    if translation == word:
                        self.creation_feedback_label.setText("Nie udało się automatycznie przetłumaczyć słowa. Wprowadź tłumaczenie ręcznie.")
                        return

            # Generowanie przykładu tylko jeśli pole jest puste
            if not example_sentence:
                example_sentence = generate_example_sentence(word, category)
                if example_sentence.startswith("Error"):
                    self.creation_feedback_label.setText("Nie udało się wygenerować przykładowego zdania. Wprowadź zdanie ręcznie.")
                    return

            # Save flashcard to database
            query = "INSERT INTO flashcards (category, subcategory, word, translation, example_sentence, user_id) VALUES (%s, %s, %s, %s, %s, %s)"
            self.db_manager.execute_query(query, (category, subcategory, word, translation, example_sentence, self.current_user['id']))

            # Save flashcard to JSON file
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
            self.update_flashcard_table()
        except Exception as e:
            self.creation_feedback_label.setText(f"Błąd podczas dodawania fiszki: {str(e)}")

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
        if selected_row < 0:
            QMessageBox.warning(self, "Błąd", "Nie wybrano fiszki do usunięcia!")
            return
        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        word = self.flashcard_table.item(selected_row, 0).text()
        confirm = QMessageBox.question(
            self, 
            "Potwierdzenie", 
            f"Czy na pewno chcesz usunąć fiszkę '{word}'?", 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                # Delete from database
                query = "DELETE FROM flashcards WHERE category = %s AND subcategory = %s AND word = %s AND user_id = %s"
                self.db_manager.execute_query(query, (category, subcategory, word, self.current_user['id']))
                
                # Update JSON file
                if category in self.categories and subcategory in self.categories[category]:
                    self.categories[category][subcategory] = [
                        fc for fc in self.categories[category][subcategory]
                        if fc["word"] != word or fc.get("user_id") != self.current_user['id']
                    ]
                    self.save_data()
                self.update_flashcard_table()
                QMessageBox.information(self, "Sukces", "Fiszka została usunięta!")
            except Exception as e:
                print(f"Error deleting flashcard: {str(e)}")
                QMessageBox.warning(self, "Błąd", "Nie udało się usunąć fiszki!")

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
        if not hasattr(self, 'correct_answer'):
            return
        user_answer = self.user_answer_input.text().strip()
        if user_answer.lower() == self.correct_answer.lower():
            self.quiz_feedback_label.setText("Dobrze! ✅")
            self.correct_answers += 1
            self.words_learned.add(self.correct_answer)
        else:
            self.quiz_feedback_label.setText(f"Źle! ❌ Poprawna odpowiedź to: {self.correct_answer}")
            self.wrong_answers += 1

        # Wyczyść pole odpowiedzi i przejdź do następnego pytania
        self.user_answer_input.clear()
        self.show_next_quiz_question(self.quiz_type_selector.currentText())

    def start_quiz(self):
        if not self.current_user:
            QMessageBox.warning(self, "Błąd", "Musisz być zalogowany, aby rozpocząć quiz!")
            return
        
        category = self.language_selector.currentText()
        subcategory = self.quiz_subcategory_selector.currentText()
        quiz_type = self.quiz_type_selector.currentText()
        random_questions = self.random_questions_checkbox.isChecked()
        
        try:
            # Pobierz fiszki z bazy danych
            query = """
            SELECT word, translation, example_sentence 
            FROM flashcards 
            WHERE category = %s AND subcategory = %s AND user_id = %s
            """
            flashcards = self.db_manager.fetch_all(query, (category, subcategory, self.current_user['id']))
            
            if not flashcards:
                QMessageBox.warning(self, "Błąd", "Nie masz żadnych fiszek w tej kategorii!")
                return
            
            # Sprawdź liczbę pytań dla trybu ABCD
            if quiz_type == "Testy ABCD" and len(flashcards) < 4:
                QMessageBox.warning(self, "Błąd", "Quiz ABCD wymaga co najmniej 4 fiszek w wybranej kategorii!")
                return
            
            # Losowe mieszanie pytań
            if random_questions:
                random.shuffle(flashcards)
            
            self.quiz_flashcards = flashcards
            self.current_quiz_index = 0
            self.correct_answers = 0
            self.wrong_answers = 0
            self.quiz_time_left = 30
            self.timer_label.setText(f"Pozostały czas: {self.quiz_time_left}")
            
            # Uruchom timer
            if self.quiz_timer is None:
                self.quiz_timer = QTimer()
                self.quiz_timer.timeout.connect(self.update_quiz_timer)
            self.quiz_timer.start(1000)  # Aktualizacja co sekundę
            
            # Wyświetl pierwsze pytanie
            self.show_next_quiz_question(quiz_type)
            
        except Exception as e:
            print(f"Error starting quiz: {str(e)}")
            QMessageBox.warning(self, "Błąd", "Nie udało się rozpocząć quizu!")

    def update_quiz_timer(self):
        self.quiz_time_left -= 1
        self.timer_label.setText(f"Pozostały czas: {self.quiz_time_left}")
        if self.quiz_time_left <= 0:
            self.quiz_timer.stop()
            self.quiz_feedback_label.setText("Czas się skończył! Przechodzimy do następnego pytania.")
            self.show_next_quiz_question()

    def show_next_quiz_question(self, quiz_type):
        if self.current_quiz_index < len(self.quiz_flashcards):
            selected_flashcard = self.quiz_flashcards[self.current_quiz_index]
            word, translation, example_sentence = selected_flashcard

            if quiz_type == "Pytania otwarte":
                self.quiz_question_label.setText(f"Przetłumacz: '{word}'")
                self.correct_answer = translation
                self.user_answer_input.setVisible(True)
                for button in self.answer_buttons:
                    button.setVisible(False)  # Ukryj przyciski odpowiedzi dla pytań otwartych

            elif quiz_type == "Testy ABCD":
                self.quiz_question_label.setText(f"Przetłumacz: '{word}'")
                self.correct_answer = translation
                self.user_answer_input.setVisible(False)

                # Generuj 4 odpowiedzi (1 poprawna + 3 losowe)
                answers = [translation]  # Dodaj poprawną odpowiedź
                while len(answers) < 4:
                    random_flashcard = random.choice(self.quiz_flashcards)
                    if random_flashcard[1] not in answers:  # Unikaj duplikatów
                        answers.append(random_flashcard[1])

                random.shuffle(answers)  # Losowo mieszaj odpowiedzi

                for i, answer in enumerate(answers):
                    self.answer_buttons[i].setText(answer)
                    self.answer_buttons[i].setVisible(True)  # Pokaż przyciski odpowiedzi dla pytań ABCD

            # Resetuj czasomierz
            self.quiz_time_left = 30
            self.timer_label.setText(f"Pozostały czas: {self.quiz_time_left}")
            self.quiz_feedback_label.setText("")
            self.current_quiz_index += 1
        else:
            # Zakończ quiz, jeśli wszystkie pytania zostały zadane
            self.quiz_timer.stop()
            self.quiz_question_label.setText("Quiz zakończony!")
            self.quiz_feedback_label.setText(f"Twój wynik: {self.correct_answers} poprawnych, {self.wrong_answers} błędnych")
            # Zapisz wyniki quizu do bazy danych
            try:
                query = """
                INSERT INTO quiz_results (user_id, correct_answers, wrong_answers, date)
                VALUES (%s, %s, %s, NOW())
                """
                self.db_manager.execute_query(query, (self.current_user['id'], self.correct_answers, self.wrong_answers))
            except Exception as e:
                print(f"Error saving quiz results: {str(e)}")
    

    def check_quiz_answer_abcd(self, selected_index):
        if not hasattr(self, 'correct_answer'):
            return

        selected_answer = self.answer_buttons[selected_index].text()
        if selected_answer.lower() == self.correct_answer.lower():
            self.quiz_feedback_label.setText("Dobrze! ✅")
            self.correct_answers += 1
            self.words_learned.add(self.correct_answer)
        else:
            self.quiz_feedback_label.setText(f"Źle! ❌ Poprawna odpowiedź to: {self.correct_answer}")
            self.wrong_answers += 1

        # Przejdź do następnego pytania, przekazując typ quizu
        self.show_next_quiz_question(self.quiz_type_selector.currentText())

    def closeEvent(self, event):
        self.db_manager.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LanguageLearningApp()
    window.show()
    sys.exit(app.exec())
