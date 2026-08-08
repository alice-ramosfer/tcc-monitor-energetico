# ================================================================
#  TCC — MONITOR ENERGÉTICO ESCOLAR
#  app.py — Ponto de entrada principal
#
#  COMO RODAR:
#    1. Ative o venv:  venv\Scripts\activate
#    2. Execute:       python app.py
#    3. Acesse:        http://localhost:5000
#    Login padrão:     admin@escola.com / admin123
# ================================================================

from flask import Flask
from extensions import db, login_manager
from routes.auth      import auth_bp
from routes.dashboard import dash_bp
from routes.api       import api_bp
from routes.ml_routes import ml_bp
import os

def create_app():
    app = Flask(__name__)

    # ── Configurações ─────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tcc-energia-2026-dev')

    # Para usar MySQL:
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:senha@localhost/tcc_energia'
    # Para usar SQLite (mais fácil para desenvolvimento local):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///tcc_energia.db'   # Arquivo gerado automaticamente na pasta
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Extensões ─────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para continuar.'
    login_manager.login_message_category = 'warning'

    # ── Blueprints (rotas) ────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp,  url_prefix='/api')
    app.register_blueprint(ml_bp,   url_prefix='/ml')

    # ── Cria tabelas e admin padrão ───────────────────────────
    with app.app_context():
        db.create_all()
        _criar_admin_padrao()

    return app


def _criar_admin_padrao():
    from models import Usuario
    import bcrypt
    if not Usuario.query.first():
        h = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
        admin = Usuario(nome='Administrador',
                        email='admin@escola.com',
                        senha_hash=h,
                        perfil='admin')
        db.session.add(admin)
        db.session.commit()
        print("✓ Banco criado!")
        print("✓ Admin: admin@escola.com / admin123")


if __name__ == '__main__':
    app = create_app()

    # Inicia scheduler de ML automático (roda a cada 1 hora)
    from routes.ml_routes import iniciar_scheduler
    iniciar_scheduler(app)

    print("\n" + "="*50)
    print("  Monitor Energético — TCC 2026")
    print("  Acesse: http://localhost:5000")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
