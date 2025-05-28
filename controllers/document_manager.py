##document_manager.py


import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QFileDialog, QMessageBox, QGroupBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
import uuid

class DocumentManagerDialog(QDialog):
    def __init__(self, parent=None, plot_id=None, plot_manager=None):
        super().__init__(parent)
        self.plot_id = plot_id
        self.plot_manager = plot_manager
        self.setWindowTitle("Управление документами участка")
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_documents()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        rental_group = QGroupBox("Договоры аренды")
        rental_layout = QVBoxLayout()
        
        self.rental_list = QListWidget()
        self.add_rental_btn = QPushButton("Добавить договор аренды")
        self.add_rental_btn.clicked.connect(lambda: self.add_document('rental'))
        self.remove_rental_btn = QPushButton("Удалить выбранное")
        self.remove_rental_btn.clicked.connect(lambda: self.remove_document('rental'))
        
        rental_btn_layout = QHBoxLayout()
        rental_btn_layout.addWidget(self.add_rental_btn)
        rental_btn_layout.addWidget(self.remove_rental_btn)
        
        rental_layout.addWidget(self.rental_list)
        rental_layout.addLayout(rental_btn_layout)
        rental_group.setLayout(rental_layout)
        
        cadastral_group = QGroupBox("Кадастровые выписки")
        cadastral_layout = QVBoxLayout()
        
        self.cadastral_list = QListWidget()
        self.add_cadastral_btn = QPushButton("Добавить кадастровую выписку")
        self.add_cadastral_btn.clicked.connect(lambda: self.add_document('cadastral'))
        self.remove_cadastral_btn = QPushButton("Удалить выбранное")
        self.remove_cadastral_btn.clicked.connect(lambda: self.remove_document('cadastral'))
        
        cadastral_btn_layout = QHBoxLayout()
        cadastral_btn_layout.addWidget(self.add_cadastral_btn)
        cadastral_btn_layout.addWidget(self.remove_cadastral_btn)
        
        cadastral_layout.addWidget(self.cadastral_list)
        cadastral_layout.addLayout(cadastral_btn_layout)
        cadastral_group.setLayout(cadastral_layout)
        
        layout.addWidget(rental_group)
        layout.addWidget(cadastral_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def load_documents(self):
        self.rental_list.clear()
        self.cadastral_list.clear()
        
        documents = self.plot_manager.get_documents(self.plot_id)
        for doc in documents:
            item_text = f"{doc['file_name']} ({doc['file_type']})"
            if doc['document_type'] == 'rental':
                self.rental_list.addItem(item_text)
            elif doc['document_type'] == 'cadastral':
                self.cadastral_list.addItem(item_text)
    
    def add_document(self, doc_type):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Выберите {'договор аренды' if doc_type == 'rental' else 'кадастровую выписку'}",
            "",
            "Документы (*.pdf *.docx)"
        )
        
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in ['.pdf', '.docx']:
                QMessageBox.warning(self, "Ошибка", "Поддерживаются только PDF и Word документы")
                return
                
            file_type = 'pdf' if file_ext == '.pdf' else 'docx'
            
            docs_dir = os.path.join(os.path.dirname(__file__), "documents")
            os.makedirs(docs_dir, exist_ok=True)
            
            unique_name = f"{uuid.uuid4()}{file_ext}"
            new_path = os.path.join(docs_dir, unique_name)
            
            try:
                with open(file_path, 'rb') as src, open(new_path, 'wb') as dst:
                    dst.write(src.read())
                
                self.plot_manager.add_document(
                    self.plot_id,
                    doc_type,
                    new_path,
                    file_type
                )
                self.load_documents()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить документ: {str(e)}")
    
    def get_documents(self):
        """Возвращает список прикрепленных документов"""
        documents = []
        for doc in self.plot_manager.get_documents(self.plot_id):
            documents.append({
                'type': doc['document_type'],
                'path': doc['file_path'],
                'name': doc['file_name']
            })
        return documents

    def remove_document(self, doc_type):
        list_widget = self.rental_list if doc_type == 'rental' else self.cadastral_list
        selected_row = list_widget.currentRow()
        
        if selected_row >= 0:
            documents = self.plot_manager.get_documents(self.plot_id, doc_type)
            if 0 <= selected_row < len(documents):
                doc_id = documents[selected_row]['id']
                file_path = documents[selected_row]['file_path']
                
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    self.plot_manager.delete_document(doc_id)
                    self.load_documents()
                    
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось удалить документ: {str(e)}")