from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Leitura, AnomaliaML
from datetime import datetime, timedelta

dash_bp = Blueprint('dashboard', __name__)
CIRCUITOS = ('sala_aula', 'robotica', 'recepcao')
NOMES = {'sala_aula': 'Sala de Aula', 'robotica': 'Sala de Robótica', 'recepcao': 'Recepção'}

@dash_bp.route('/')
@login_required
def index():
    cards = []
    for c in CIRCUITOS:
        ultima = Leitura.query.filter_by(circuito=c).order_by(Leitura.timestamp.desc()).first()
        desde  = datetime.utcnow() - timedelta(hours=24)
        n_anom = AnomaliaML.query.filter_by(circuito=c, eh_anomalia=True)\
                                 .filter(AnomaliaML.timestamp >= desde).count()
        cards.append({'circuito': c, 'nome': NOMES[c], 'ultima': ultima, 'anomalias24': n_anom})

    anomalias = AnomaliaML.query.filter_by(eh_anomalia=True)\
                                .order_by(AnomaliaML.timestamp.desc()).limit(8).all()
    return render_template('dashboard.html', cards=cards, anomalias=anomalias, usuario=current_user)

@dash_bp.route('/circuito/<nome>')
@login_required
def circuito(nome):
    if nome not in CIRCUITOS:
        return 'Circuito não encontrado', 404
    desde   = datetime.utcnow() - timedelta(hours=24)
    leituras = Leitura.query.filter(Leitura.circuito==nome, Leitura.timestamp>=desde)\
                            .order_by(Leitura.timestamp.asc()).all()
    anomalias = AnomaliaML.query.filter_by(circuito=nome, eh_anomalia=True)\
                                .order_by(AnomaliaML.timestamp.desc()).limit(10).all()
    return render_template('circuito.html', circuito=nome, nome=NOMES[nome],
                           leituras=leituras, anomalias=anomalias, hoje=datetime.now().strftime('%Y-%m-%d'))

@dash_bp.route('/ml-dashboard')
@login_required
def pagina_ml():
    anomalias = AnomaliaML.query.filter_by(eh_anomalia=True)\
                                .order_by(AnomaliaML.timestamp.desc()).limit(50).all()
    return render_template('ml.html', anomalias=anomalias, usuario=current_user)
