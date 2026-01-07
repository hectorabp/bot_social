FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirement y instalar dependencias
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar el código del backend
COPY controller ./controller
COPY modules ./modules
COPY scheduled_service ./scheduled_service
COPY service ./service
COPY routes ./routes
COPY templates ./templates
COPY static ./static
COPY app.py ./app.py

# Variables de entorno por defecto
ENV FLASK_RUN_PORT=5000
ENV PYTHONUNBUFFERED=1

# Exponer puerto del servicio (app.py usa por defecto 5000 o env PORT)
EXPOSE 5000

# Comando por defecto: arrancar con gunicorn
CMD ["python", "app.py"]
