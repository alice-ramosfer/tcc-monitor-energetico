from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import Usuario
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '').encode()
        user  = Usuario.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(senha, user.senha_hash.encode()):
            login_user(user, remember=True)
            flash(f'Bem-vinda, {user.nome}!', 'success')
            return redirect(url_for('dashboard.index'))
        flash('E-mail ou senha incorretos.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if current_user.perfil != 'admin':
        flash('Apenas administradores podem criar usuários.', 'danger')
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        nome   = request.form.get('nome', '').strip()
        email  = request.form.get('email', '').strip().lower()
        senha  = request.form.get('senha', '').encode()
        perfil = request.form.get('perfil', 'viewer')
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'warning')
        else:
            h = bcrypt.hashpw(senha, bcrypt.gensalt()).decode()
            db.session.add(Usuario(nome=nome, email=email, senha_hash=h, perfil=perfil))
            db.session.commit()
            flash(f'Usuário {nome} criado!', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('novo_usuario.html')


@app.route('/reset-admin-temp')
def reset_admin_temp():
    from models import Usuario
    u = Usuario.query.filter_by(email='admin@escola.com').first()
    if u:
        u.set_senha('admin123')
        db.session.commit()
        return 'Senha resetada! Apague esta rota depois.'
    return 'Usuário não encontrado'