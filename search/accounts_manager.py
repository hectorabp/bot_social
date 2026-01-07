import csv
import os
from datetime import datetime

class AccountsManager:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        # Crear el archivo si no existe con encabezados
        if not os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Fecha y Hora', 'Nombre', 'Correo', 'Estado'])

    def create(self, nombre, correo, estado='Incompleto'):
        """Crear un nuevo registro en el CSV."""
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.csv_file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([fecha_hora, nombre, correo, estado])
        print(f"Registro creado: {nombre}, {correo}, {estado}")

    def read(self, filtro=None):
        """Leer todos los registros o filtrar por un criterio (dict con claves como 'Nombre', 'Correo', etc.)."""
        registros = []
        with open(self.csv_file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if filtro:
                    if all(row.get(key) == value for key, value in filtro.items()):
                        registros.append(row)
                else:
                    registros.append(row)
        return registros

    def update(self, index, **kwargs):
        """Actualizar un registro por índice de fila (0-based). kwargs: campos a actualizar."""
        registros = self.read()
        if 0 <= index < len(registros):
            for key, value in kwargs.items():
                if key in registros[index]:
                    registros[index][key] = value
            self._escribir_todos(registros)
            print(f"Registro en índice {index} actualizado.")
        else:
            print("Índice fuera de rango.")

    def delete(self, index):
        """Eliminar un registro por índice de fila (0-based)."""
        registros = self.read()
        if 0 <= index < len(registros):
            eliminado = registros.pop(index)
            self._escribir_todos(registros)
            print(f"Registro eliminado: {eliminado}")
        else:
            print("Índice fuera de rango.")

    def _escribir_todos(self, registros):
        """Método auxiliar para escribir todos los registros de vuelta al CSV."""
        with open(self.csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            if registros:
                writer = csv.DictWriter(file, fieldnames=registros[0].keys())
                writer.writeheader()
                writer.writerows(registros)