## harvest_manager.py


from PyQt5.QtWidgets import (
    QTableWidgetItem, QPushButton, QComboBox, QDateEdit, 
    QDialog, QMessageBox
)
from PyQt5.QtCore import QDate
from ui.harvest_dialog import HarvestDialog

class HarvestManager:
    def __init__(self, plot_manager):
        self.plot_manager = plot_manager

    def update_harvest_history(self, table, plot_id, date_from, date_to, culture_filter=None):
        try:
            table.setRowCount(0)
            if not plot_id:
                return

            all_harvests = self.plot_manager.get_harvests_for_plot(plot_id)
            if not all_harvests:
                return

            filtered = [h for h in all_harvests if date_from <= h['date'] <= date_to]

            if culture_filter and culture_filter != "Все культуры":
                filtered = [h for h in filtered if h['culture'] == culture_filter]

            filtered.sort(key=lambda x: x['date'], reverse=True)

            table.setRowCount(len(filtered))
            for row_idx, harvest_record in enumerate(filtered):
                workers = self.plot_manager.db.fetch_all("""
                    SELECT w.name FROM workers w
                    JOIN harvest_workers hw ON w.id = hw.worker_id
                    WHERE hw.harvest_id = ?
                """, (harvest_record['id'],))
                
                workers_str = ", ".join([w['name'] for w in workers])

                table.setItem(row_idx, 0, QTableWidgetItem(harvest_record['date']))
                table.setItem(row_idx, 1, QTableWidgetItem(harvest_record['culture']))
                table.setItem(row_idx, 2, QTableWidgetItem(f"{harvest_record['amount']:.2f}"))
                table.setItem(row_idx, 3, QTableWidgetItem(workers_str))

                edit_btn = QPushButton("✏️")
                edit_btn.clicked.connect(
                    self.create_edit_handler(table, plot_id, harvest_record)
                )
                table.setCellWidget(row_idx, 4, edit_btn)

        except Exception as e:
            print(f"Ошибка при обновлении истории сборов: {str(e)}")

    def create_edit_handler(self, table, plot_id, record):
        def handler():
            self.edit_harvest_record(table, plot_id, record)
        return handler

    def update_culture_filter(self, combo: QComboBox, plot_id: int):
        combo.clear()
        combo.addItem("Все культуры")

        if not plot_id:
            return

        harvests = self.plot_manager.get_harvests_for_plot(plot_id)
        cultures = sorted(set(
            h['culture'] for h in harvests if h['culture']
        ))

        for culture in cultures:
            combo.addItem(culture)

    def edit_harvest_record(self, table, plot_id, record):
        try:
            dialog = HarvestDialog(
                table.parent(),
                self.plot_manager.db,
                plot_id,
                record
            )
        
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                
                # Обновляем запись о сборе урожая
                self.plot_manager.db.execute("""
                    UPDATE harvests 
                    SET date=?, culture=?, amount=?
                    WHERE id=?
                """, (new_data['date'], new_data['culture'], new_data['amount'], record['id']))
                
                # Обновляем рабочих
                self.plot_manager.db.execute(
                    "DELETE FROM harvest_workers WHERE harvest_id=?",
                    (record['id'],)
                )
                
                for worker_id in new_data['worker_ids']:
                    self.plot_manager.db.execute(
                        "INSERT INTO harvest_workers (harvest_id, worker_id) VALUES (?, ?)",
                        (record['id'], worker_id)
                    )
                
                date_from = table.property('date_from')
                date_to = table.property('date_to')
                culture_filter = table.property('culture_filter')
                
                self.update_harvest_history(
                    table,
                    plot_id,
                    date_from,
                    date_to,
                    culture_filter
                )

        except Exception as e:
            print(f"Ошибка при редактировании записи: {str(e)}")