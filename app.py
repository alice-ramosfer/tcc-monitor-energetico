# ================================================================
#  TCC — MONITOR ENERGÉTICO ESCOLAR
#  app.py — Ponto de entrada principal
#
#  LOCAL:    python app.py  →  http://localhost:5000
#  RAILWAY:  gunicorn "app:create_app()" (Procfile já configurado)
# ================================================================

from flask import Flask
from extensions import db, login_manager
from routes.auth      import auth_bp
from routes.dashboard import dash_bp
from routes.api       import api_bp
from routes.ml_routes import ml_bp
from models import Usuario
from extensions import db
import bcrypt
import os


def create_app():
    app = Flask(__name__)

    # ── SECRET_KEY ────────────────────────────────────────────
    # Local: usa valor padrão
    # Railway: define a variável SECRET_KEY no painel Variables
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY', 'tcc-energia-2026-dev-local'
    )

    # ── BANCO DE DADOS ─────────────────────────────────────────
    # Local:   usa SQLite automaticamente (sem configuração)
    # Railway: define DATABASE_URL no painel Variables com o MySQL
    #          Formato: mysql+pymysql://root:SENHA@host:PORT/railway
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///tcc_energia.db')

    # Railway às vezes entrega "mysql://" — corrige para "mysql+pymysql://"
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://')

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,      # Reconecta se a conexão cair
        'pool_recycle':  300,       # Recicla conexões a cada 5 min
    }

    # ── EXTENSÕES ─────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view         = 'auth.login'
    login_manager.login_message      = 'Faça login para continuar.'
    login_manager.login_message_category = 'warning'

    # ── BLUEPRINTS ────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp,  url_prefix='/api')
    app.register_blueprint(ml_bp,   url_prefix='/ml')

    # ── BANCO + ADMIN PADRÃO ──────────────────────────────────
    with app.app_context():
        db.create_all()
        _criar_admin_padrao()

    return app


def _criar_admin_padrao():
    try:
        if not Usuario.query.filter_by(email='admin@escola.com').first():
            senha_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            admin = Usuario(
                nome='Administrador',
                email='admin@escola.com',
                senha_hash=senha_hash,
                perfil='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('✓ Admin criado')
        else:
            print('✓ Admin já existe — nada a fazer')
    except Exception as e:
        db.session.rollback()
        print(f'⚠ Erro: {e}')


# ── EXECUÇÃO LOCAL ────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()

    # Scheduler de ML (roda a cada 1 hora)
    from routes.ml_routes import iniciar_scheduler
    iniciar_scheduler(app)

    print("\n" + "="*50)
    print("  Monitor Energético — TCC 2026")
    print("  Local:  http://localhost:5000")
    print("  Login:  admin@escola.com / admin123")
    print("="*50 + "\n")

    # debug=False em produção, True só local
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=5000)
