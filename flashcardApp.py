import json
import os
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox,
    QSplitter, QCheckBox
)
from PySide6.QtCore import Qt
from googletrans import Translator

class LanguageLearningApp(QWidget):
    def __init__(self):
        super().__init__()
        self.translator = Translator()
        self.setWindowTitle("Aplikacja do Nauki Języków")
        self.setMinimumSize(1500, 700)
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
""")

        self.data_file = "flashcards.json"
        self.load_data()
        self.layout = QVBoxLayout()
        header = QLabel("Aplikacja do Nauki Języków", self)
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E88E5; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(header)
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs)
        self.flashcard_tab = QWidget()
        self.tabs.addTab(self.flashcard_tab, "Fiszki")
        self.setup_flashcard_tab()
        self.creation_tab = QWidget()
        self.tabs.addTab(self.creation_tab, "Tworzenie Fiszek")
        self.setup_creation_tab()
        self.quiz_tab = QWidget()
        self.tabs.addTab(self.quiz_tab, "Quiz")
        self.setup_quiz_tab()
        self.progress_tab = QWidget()
        self.tabs.addTab(self.progress_tab, "Postęp")
        self.setup_progress_tab()
        self.setLayout(self.layout)
        self.update_category_selector()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                self.categories = json.load(file)
        else:
            self.categories = {
                "Angielski": {
                    "czasowniki": [
                        {"word": "run", "translation": "biegać", "example_sentence": "I run every day."},
                        {"word": "eat", "translation": "jeść", "example_sentence": "I eat lunch at noon."}
                    ],
                    "rzeczowniki": [
                        {"word": "book", "translation": "książka", "example_sentence": "This is my favorite book."},
                        {"word": "dog", "translation": "pies", "example_sentence": "The dog is barking."}
                    ]
                },
                "Hiszpański": {
                    "czasowniki": [
                        {"word": "correr", "translation": "biegać", "example_sentence": "Corro todos los días."},
                        {"word": "comer", "translation": "jeść", "example_sentence": "Como a las doce."}
                    ],
                    "rzeczowniki": [
                        {"word": "libro", "translation": "książka", "example_sentence": "Este es mi libro favorito."},
                        {"word": "perro", "translation": "pies", "example_sentence": "El perro está ladrando."}
                    ]
                }
            }

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(self.categories, file, indent=4, ensure_ascii=False)

    def setup_flashcard_tab(self):
        layout = QVBoxLayout()
        category_layout = QHBoxLayout()
        self.category_selector = QComboBox(self)
        self.category_selector.currentTextChanged.connect(self.update_subcategory_selector)
        category_layout.addWidget(QLabel("Wybierz język:", self))
        category_layout.addWidget(self.category_selector)
        self.subcategory_selector = QComboBox(self)
        self.subcategory_selector.currentTextChanged.connect(self.update_flashcard_table)
        category_layout.addWidget(QLabel("Wybierz podkategorię:", self))
        category_layout.addWidget(self.subcategory_selector)
        self.add_category_button = QPushButton("Dodaj język", self)
        self.add_category_button.clicked.connect(self.add_category)
        category_layout.addWidget(self.add_category_button)
        self.delete_category_button = QPushButton("Usuń język", self)
        self.delete_category_button.clicked.connect(self.delete_category)
        category_layout.addWidget(self.delete_category_button)
        self.delete_subcategory_button = QPushButton("Usuń podkategorię", self)
        self.delete_subcategory_button.clicked.connect(self.delete_subcategory)
        category_layout.addWidget(self.delete_subcategory_button)
        layout.addLayout(category_layout)
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Szukaj fiszki...")
        self.search_input.textChanged.connect(self.search_flashcards)
        layout.addWidget(self.search_input)
        self.splitter = QSplitter(self)
        self.flashcard_table = QTableWidget(self)
        self.flashcard_table.setColumnCount(3)
        self.flashcard_table.setHorizontalHeaderLabels(["Słowo", "Tłumaczenie", "Przykładowe zdanie"])
        self.flashcard_table.horizontalHeader().setStretchLastSection(True)
        self.splitter.addWidget(self.flashcard_table)
        self.edit_widget = QWidget()
        edit_layout = QVBoxLayout()
        self.edit_word_input = QLineEdit(self)
        self.edit_translation_input = QLineEdit(self)
        self.edit_example_sentence_input = QLineEdit(self)
        edit_layout.addWidget(QLabel("Edytuj słowo:"))
        edit_layout.addWidget(self.edit_word_input)
        edit_layout.addWidget(QLabel("Edytuj tłumaczenie:"))
        edit_layout.addWidget(self.edit_translation_input)
        edit_layout.addWidget(QLabel("Edytuj zdanie:"))
        edit_layout.addWidget(self.edit_example_sentence_input)
        self.save_button = QPushButton("Zapisz zmiany", self)
        self.save_button.clicked.connect(self.save_flashcard_edits)
        edit_layout.addWidget(self.save_button)
        self.edit_widget.setLayout(edit_layout)
        self.splitter.addWidget(self.edit_widget)
        self.edit_widget.hide()
        layout.addWidget(self.splitter)
        self.edit_button = QPushButton("Edytuj wybraną fiszkę", self)
        self.edit_button.clicked.connect(self.show_edit_area)
        layout.addWidget(self.edit_button)
        self.delete_button = QPushButton("Usuń wybraną fiszkę", self)
        self.delete_button.clicked.connect(self.delete_flashcard)
        layout.addWidget(self.delete_button)
        self.flashcard_feedback_label = QLabel("", self)
        layout.addWidget(self.flashcard_feedback_label)
        self.flashcard_tab.setLayout(layout)

    def add_category(self):
        category_name, ok = QInputDialog.getText(self, "Dodaj język", "Nowy język")
        if ok and category_name:
            if category_name not in self.categories:
                self.categories[category_name] = {}
                self.save_data()
                self.update_category_selector()
                QMessageBox.information(self, "Sukces", f"język '{category_name}' została dodana!")
            else:
                QMessageBox.warning(self, "Błąd", "ten język już istnieje!")

    def delete_category(self):
        category = self.category_selector.currentText()
        if category:
            confirm = QMessageBox.question(self, "Potwierdzenie", f"Czy na pewno chcesz usunąć kategorię '{category}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                del self.categories[category]
                self.save_data()
                self.update_category_selector()
                QMessageBox.information(self, "Sukces", f"Kategoria '{category}' została usunięta!")

    def delete_subcategory(self):
        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        if category and subcategory:
            confirm = QMessageBox.question(self, "Potwierdzenie", f"Czy na pewno chcesz usunąć podkategorię '{subcategory}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                del self.categories[category][subcategory]
                self.save_data()
                self.update_subcategory_selector()
                QMessageBox.information(self, "Sukces", f"Podkategoria '{subcategory}' została usunięta!")

    def show_edit_area(self):
        selected_row = self.flashcard_table.currentRow()
        if selected_row >= 0:
            self.edit_widget.show()
            category = self.category_selector.currentText()
            subcategory = self.subcategory_selector.currentText()
            flashcard = self.categories[category][subcategory][selected_row]
            self.edit_word_input.setText(flashcard["word"])
            self.edit_translation_input.setText(flashcard["translation"])
            self.edit_example_sentence_input.setText(flashcard["example_sentence"])
        else:
            self.flashcard_feedback_label.setText("Nie wybrano fiszki do edycji!")

    def save_flashcard_edits(self):
        selected_row = self.flashcard_table.currentRow()
        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        if selected_row >= 0 and category in self.categories and subcategory in self.categories[category]:
            flashcard = self.categories[category][subcategory][selected_row]
            flashcard["word"] = self.edit_word_input.text().strip()
            flashcard["translation"] = self.edit_translation_input.text().strip()
            flashcard["example_sentence"] = self.edit_example_sentence_input.text().strip()
            self.save_data()
            self.update_flashcard_table()
            self.flashcard_feedback_label.setText("Fiszka została zaktualizowana!")
            self.edit_widget.hide()
        else:
            self.flashcard_feedback_label.setText("Nie wybrano fiszki do edycji!")

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
        self.auto_translate_checkbox = QCheckBox("Automatyczne tłumaczenie", self)
        layout.addWidget(self.auto_translate_checkbox)
        self.add_flashcard_button = QPushButton("Dodaj fiszkę", self)
        self.add_flashcard_button.clicked.connect(self.add_flashcard)
        self.add_subcategory_button = QPushButton("Dodaj podkategorię", self)
        self.add_subcategory_button.clicked.connect(self.add_subcategory)
        layout.addWidget(QLabel("Dodaj fiszkę:"))
        layout.addWidget(QLabel("Kategoria:"))
        layout.addWidget(self.category_selector_creation)
        layout.addWidget(QLabel("Podkategoria:"))
        layout.addWidget(self.subcategory_selector_creation)
        layout.addWidget(self.word_input)
        layout.addWidget(self.translation_input)
        layout.addWidget(self.example_sentence_input)
        layout.addWidget(self.add_flashcard_button)
        layout.addWidget(self.add_subcategory_button)
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
        category = self.category_selector.currentText()
        subcategory = self.subcategory_selector.currentText()
        if category in self.categories and subcategory in self.categories[category]:
            flashcards = self.categories[category][subcategory]
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

    def add_flashcard(self):
        category = self.category_selector_creation.currentText()
        subcategory = self.subcategory_selector_creation.currentText()
        word = self.word_input.text().strip()
        translation = self.translation_input.text().strip()
        example_sentence = self.example_sentence_input.text().strip()
        if self.auto_translate_checkbox.isChecked() and not translation:
            target_language = self.get_language_code(category)
            try:
                translation = self.translator.translate(word, dest=target_language).text
            except Exception as e:
                self.creation_feedback_label.setText(f"Błąd tłumaczenia: {str(e)}")
                return
        if word and translation and category and subcategory:
            if subcategory not in self.categories[category]:
                self.categories[category][subcategory] = []
            self.categories[category][subcategory].append({
                "word": word,
                "translation": translation,
                "example_sentence": example_sentence
            })
            self.save_data()
            self.update_flashcard_table()
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

    def check_quiz_answer(self):
        user_answer = self.user_answer_input.text().strip()
        if hasattr(self, 'correct_answer'):
            if user_answer.lower() == self.correct_answer.lower():
                self.quiz_feedback_label.setText("Dobrze!")
            else:
                self.quiz_feedback_label.setText(f"Źle! Poprawna odpowiedź to:{self.correct_answer}")
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

    def get_language_code(self, language_name):
        language_codes = {
            "Angielski": "en",
            "Hiszpański": "es"
        }
        return language_codes.get(language_name, "en")

if __name__ == "__main__":
    app = QApplication([])
    window = LanguageLearningApp()
    window.show()
    app.exec()
