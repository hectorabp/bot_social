from flask import Flask
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from routes.user_routes import Userbp
from routes.profile_routes import Profilebp
from routes.task_routes import Taskbp
from routes.web_routes import web_bp


app = Flask(__name__)
app.secret_key = 'super_secret_key_cambiar_en_produccion' # Necesario para sesiones y flash messages

app.register_blueprint(Userbp)
app.register_blueprint(Profilebp)
app.register_blueprint(Taskbp)
app.register_blueprint(web_bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
