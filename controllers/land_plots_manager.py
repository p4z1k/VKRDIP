##controllers/land_plots_manager.py
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from db.database_manager import DatabaseManager
from ui.field_work_tab import FieldWorkTab
class LandPlotManager:
    def __init__(self, db_path="full_data.db"):
        self.db = DatabaseManager(db_path)

    def add_plot(self, name, coordinates, area, plot_type, additional_data=None):
        print("[DEBUG] add_plot called", name, coordinates, area, plot_type, additional_data)
        now = datetime.now().isoformat()
        rental_expiry = additional_data.get("rental_expiry_date") if additional_data else None
        assignment_date = additional_data.get("assignment_date", now[:10]) if additional_data else now[:10]
        status = additional_data.get("status", "Новый") if additional_data else "Новый"
        crop = additional_data.get("crop", "") if additional_data else ""
    
        self.db.execute("""
            INSERT INTO plots (
                name, coordinates, area, type,
                cadastral_number, property_type, assignment_date, address,
                area_sqm, land_category, land_use, cadastral_value,
                owner_name, owner_contacts, created_at, updated_at,
                rental_expiry_date, status, crop
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            json.dumps(coordinates),
            area,
            plot_type,
            additional_data.get("cadastral_number", "") if additional_data else "",
            additional_data.get("property_type", "") if additional_data else "",
            assignment_date,
            additional_data.get("address", "") if additional_data else "",
            additional_data.get("area_sqm", area * 10000) if additional_data else area * 10000,
            additional_data.get("land_category", "") if additional_data else "",
            additional_data.get("land_use", "") if additional_data else "",
            additional_data.get("cadastral_value", 0) if additional_data else 0,
            additional_data.get("owner_name", "") if additional_data else "",
            additional_data.get("owner_contacts", "") if additional_data else "",
            now,
            now,
            rental_expiry,
            status,
            crop
        ))

    def add_document(self, plot_id, document_type, file_path, file_type):
        file_name = os.path.basename(file_path)
        upload_date = datetime.now().isoformat()
        self.db.execute("""
            INSERT INTO plot_documents 
            (plot_id, document_type, file_name, file_path, file_type, upload_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (plot_id, document_type, file_name, file_path, file_type, upload_date))
        return True
    
    def get_documents(self, plot_id, document_type=None):
        query = "SELECT * FROM plot_documents WHERE plot_id = ?"
        params = [plot_id]
        if document_type:
            query += " AND document_type = ?"
            params.append(document_type)
            
        return self.db.fetch_all(query, tuple(params))

    def delete_document(self, document_id):
        self.db.execute("DELETE FROM plot_documents WHERE id = ?", (document_id,))
        return True

    def get_all_plots(self, sort_key: str = 'name', 
                      filter_type: str = None, 
                      search_query: str = None) -> List[Dict]:
        query = "SELECT * FROM plots WHERE 1=1"
        params = []
        if filter_type:
            query += " AND type = ?"
            params.append(filter_type)
        if search_query:
            query += " AND (LOWER(name) LIKE ? OR LOWER(address) LIKE ?)"
            params.append(f"%{search_query.lower()}%")
            params.append(f"%{search_query.lower()}%")
        query += f" ORDER BY {sort_key}"
        plots = self.db.fetch_all(query, tuple(params))
        for plot in plots:
            if plot.get('coordinates'):
                try:
                    plot["coordinates"] = json.loads(plot["coordinates"])
                except:
                    plot["coordinates"] = []
            if 'area_ha' not in plot:
                plot['area_ha'] = plot.get('area', 0)
        return plots

    def get_plot_by_id(self, plot_id: int) -> Optional[Dict]:
        plot = self.db.fetch_one("SELECT * FROM plots WHERE id = ?", (plot_id,))
        if plot:
            if plot.get('coordinates'):
                try:
                    plot["coordinates"] = json.loads(plot["coordinates"])
                except:
                    plot["coordinates"] = []
            plot["area_sqm"] = plot.get("area_sqm", 0) or 0
            plot["area_ha"] = plot.get("area_ha", plot.get("area", 0)) or 0
            plot["cadastral_value"] = plot.get("cadastral_value", 0) or 0
            if not plot.get('assignment_date'):
                plot['assignment_date'] = datetime.now().isoformat()[:10]
            if plot.get('type') == 'Арендованный' and not plot.get('rental_expiry_date'):
                plot['rental_expiry_date'] = (datetime.now() + timedelta(days=365)).isoformat()[:10]
        return plot

    def update_plot(self, plot_id: int, **kwargs):
        try:
            keys = []
            values = []
            additional_data = kwargs.pop('additional_data', {})
            for key, value in kwargs.items():
                if value is None:
                    continue
                if key == "coordinates":
                    value = json.dumps(value) if value else None
                keys.append(f"{key} = ?")
                values.append(value)
            for key, value in additional_data.items():
                if value is not None:
                    keys.append(f"{key} = ?")
                    values.append(value)
            keys.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(plot_id)
            if not keys:
                return False
            self.db.execute(f"""
                UPDATE plots SET {', '.join(keys)} WHERE id = ?
            """, tuple(values))
            return True
        except Exception as e:
            print(f"Ошибка при обновлении участка: {str(e)}")
            return False

    def delete_plot(self, plot_id: int) -> bool:
        self.db.execute("DELETE FROM plots WHERE id = ?", (plot_id,))
        return True

    def add_harvest_record(self, plot_id: int, date: str, culture: str, amount: float) -> int:
        cursor = self.db.execute("""
            INSERT INTO harvests (plot_id, date, culture, amount)
            VALUES (?, ?, ?, ?)
        """, (plot_id, date, culture, amount))
        return cursor.lastrowid

    def get_harvests_for_plot(self, plot_id: int) -> List[Dict]:
        return self.db.fetch_all("SELECT * FROM harvests WHERE plot_id = ?", (plot_id,))