from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from pathlib import Path
import sys
import math
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.user import UserModule
from modules.countries import CountriesModule
from modules.cities import CitiesModule
from modules.neighborhoods import NeighborhoodsModule
from modules.genders import GendersModule
from modules.political_parties import PoliticalPartiesModule
from modules.football_clubs import FootballClubsModule
from modules.ideologies import IdeologiesModule
from modules.music_styles import MusicStylesModule
from controller.profile_controller import ProfileController

web_bp = Blueprint('web', __name__)

# Initialize modules
user_module = UserModule()
countries_module = CountriesModule()
cities_module = CitiesModule()
neighborhoods_module = NeighborhoodsModule()
genders_module = GendersModule()
political_parties_module = PoliticalPartiesModule()
football_clubs_module = FootballClubsModule()
ideologies_module = IdeologiesModule()
music_styles_module = MusicStylesModule()
profile_controller = ProfileController()

@web_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))
    return redirect(url_for('web.login'))

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email and password:
            user = user_module.get_user_by_email(email)
            if user and user_module.verify_password(password, user['password']):
                session['user_id'] = user['id']
                session['user_email'] = user['correo']
                session['user_role'] = user['id_rol']
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('web.dashboard'))
            else:
                flash('Credenciales inválidas', 'danger')
        else:
            flash('Por favor complete todos los campos', 'warning')
            
    return render_template('auth/login.html')

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Lógica de registro
        flash('Registro exitoso. Por favor inicia sesión.', 'success')
        return redirect(url_for('web.login'))
    return render_template('auth/register.html')

@web_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver esta página', 'warning')
        return redirect(url_for('web.login'))
    return render_template('dashboard/index.html')

@web_bp.route('/profiles/create', methods=['GET', 'POST'])
def create_profile():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
        
    if request.method == 'POST':
        payload = request.form.to_dict()
        # Convert empty strings to None for optional fields if needed, 
        # but controller validation might handle it or we might need to clean it up.
        # ProfileController.create expects a dict.
        
        result = profile_controller.create(payload)
        
        if result.get('success'):
            flash('Perfil creado exitosamente', 'success')
            return redirect(url_for('web.dashboard'))
        else:
            flash(f"Error al crear perfil: {result.get('error')}", 'danger')
            # In a real app, we would pass 'payload' back to context to repopulate form
        
    # Fetch real data from DB
    try:
        context = {
            'paises': countries_module.list_all(),
            'ciudades': cities_module.list_all(),
            'barrios': neighborhoods_module.list_all(),
            'generos': genders_module.list_all(),
            'partidos': political_parties_module.list_all(),
            'clubes': football_clubs_module.list_all(),
            'ideologias': ideologies_module.list_all(),
            'musicas': music_styles_module.list_all()
        }
    except AttributeError:
        # Fallback if list_all is not implemented yet in modules
        flash('Error: Módulos de base de datos incompletos (falta list_all)', 'warning')
        context = {
            'paises': [], 'ciudades': [], 'barrios': [], 'generos': [],
            'partidos': [], 'clubes': [], 'ideologias': [], 'musicas': []
        }

    return render_template('dashboard/create_profile.html', **context)

@web_bp.route('/profiles/upload', methods=['GET', 'POST'])
def upload_profiles():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
        
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
            
        if file:
            try:
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Replace NaN with None
                df = df.where(pd.notnull(df), None)
                
                # Normalize headers to lowercase and strip spaces
                df.columns = df.columns.str.strip().str.lower()
                
                # Load catalogs for name resolution
                try:
                    catalogs = {
                        'pais': {str(x['pais']).lower(): x['id'] for x in countries_module.list_all()},
                        'ciudad': {str(x['ciudad']).lower(): x['id'] for x in cities_module.list_all()},
                        'barrio': {str(x['barrio']).lower(): x['id'] for x in neighborhoods_module.list_all()},
                        'genero': {str(x['genero']).lower(): x['id'] for x in genders_module.list_all()},
                        'partido_politico': {str(x['partido_politico']).lower(): x['id'] for x in political_parties_module.list_all()},
                        'club_futbol': {str(x['club_futbol']).lower(): x['id'] for x in football_clubs_module.list_all()},
                        'ideologia': {str(x['ideologia']).lower(): x['id'] for x in ideologies_module.list_all()},
                        'estilo_musica': {str(x['estilo_musica']).lower(): x['id'] for x in music_styles_module.list_all()}
                    }
                except Exception as e:
                    # If a module fails, we just continue with empty catalog for that one
                    print(f"Error loading catalogs: {e}")
                    catalogs = {}

                # Map of excel column name -> (db_key, catalog_key)
                column_mapping = {
                    'pais': ('id_pais', 'pais'),
                    'ciudad': ('id_ciudad', 'ciudad'),
                    'barrio': ('id_barrio', 'barrio'),
                    'genero': ('id_genero', 'genero'),
                    'partido': ('id_partido_politico', 'partido_politico'),
                    'partido_politico': ('id_partido_politico', 'partido_politico'),
                    'club': ('id_club_futbol', 'club_futbol'),
                    'club_futbol': ('id_club_futbol', 'club_futbol'),
                    'ideologia': ('id_ideologia', 'ideologia'),
                    'musica': ('id_estilo_musica', 'estilo_musica'),
                    'estilo_musica': ('id_estilo_musica', 'estilo_musica')
                }

                success_count = 0
                error_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    payload = row.to_dict()
                    
                    # Resolve names to IDs
                    for col_name, (db_key, catalog_key) in column_mapping.items():
                        if col_name in payload and payload[col_name] and db_key not in payload:
                            val = str(payload[col_name]).strip().lower()
                            if catalog_key in catalogs and val in catalogs[catalog_key]:
                                payload[db_key] = catalogs[catalog_key][val]

                    # Convert float IDs to int if they are numbers
                    for key in ['id_pais', 'id_ciudad', 'id_barrio', 'id_genero', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_plantilla']:
                        if key in payload and payload[key] is not None:
                            try:
                                payload[key] = int(float(payload[key]))
                            except (ValueError, TypeError):
                                pass 
                                
                    result = profile_controller.create(payload)
                    if result.get('success'):
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Fila {index+2}: {result.get('error')}")
                
                if success_count > 0:
                    flash(f'{success_count} perfiles creados exitosamente.', 'success')
                if error_count > 0:
                    flash(f'{error_count} errores. Primeros errores: {"; ".join(errors[:3])}', 'warning')
                    
            except Exception as e:
                flash(f'Error al procesar el archivo: {str(e)}', 'danger')
                
            return redirect(url_for('web.dashboard'))

    return render_template('dashboard/upload_profiles.html')

@web_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('web.login'))

@web_bp.route('/emails')
def email_list():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))

    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    filters = {}
    # Location
    if request.args.get('id_pais'): filters['id_pais'] = request.args.get('id_pais')
    if request.args.get('id_ciudad'): filters['id_ciudad'] = request.args.get('id_ciudad')
    if request.args.get('id_barrio'): filters['id_barrio'] = request.args.get('id_barrio')
    
    # Preferences
    if request.args.get('id_genero'): filters['id_genero'] = request.args.get('id_genero')
    if request.args.get('id_partido_politico'): filters['id_partido_politico'] = request.args.get('id_partido_politico')
    if request.args.get('id_club_futbol'): filters['id_club_futbol'] = request.args.get('id_club_futbol')
    if request.args.get('id_ideologia'): filters['id_ideologia'] = request.args.get('id_ideologia')
    if request.args.get('id_estilo_musica'): filters['id_estilo_musica'] = request.args.get('id_estilo_musica')

    # Social Networks
    if request.args.get('has_FB'): filters['has_FB'] = True
    if request.args.get('has_IG'): filters['has_IG'] = True
    if request.args.get('has_TW'): filters['has_TW'] = True
    if request.args.get('has_TK'): filters['has_TK'] = True

    # Note: order_by='p.id' assumes the controller/module supports 'p.id' which it does in list_with_relations
    result = profile_controller.get_profiles(filters=filters, page=page, per_page=per_page, order_by='p.id')
    
    profiles = []
    pagination = None
    
    if result.get('success'):
        profiles = result.get('profiles', [])
        total = result.get('total', 0)
        total_pages = math.ceil(total / per_page) if per_page else 0
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    else:
        flash(f"Error al cargar perfiles: {result.get('error')}", 'danger')

    try:
        paises = countries_module.list_all()
        ciudades = cities_module.list_all()
        barrios = neighborhoods_module.list_all()
        generos = genders_module.list_all()
        partidos = political_parties_module.list_all()
        clubes = football_clubs_module.list_all()
        ideologias = ideologies_module.list_all()
        musicas = music_styles_module.list_all()
    except Exception as e:
        flash(f"Error al cargar filtros: {str(e)}", 'warning')
        paises = ciudades = barrios = generos = partidos = clubes = ideologias = musicas = []

    context = {
        'profiles': profiles,
        'pagination': pagination,
        'paises': paises,
        'ciudades': ciudades,
        'barrios': barrios,
        'generos': generos,
        'partidos': partidos,
        'clubes': clubes,
        'ideologias': ideologias,
        'musicas': musicas,
        'filters': request.args
    }
    return render_template('dashboard/email_list.html', **context)

