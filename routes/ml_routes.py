from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from ml.engine import run_all_ml

ml_bp = Blueprint('ml', __name__)

@ml_bp.route('/rodar', methods=['POST'])
@login_required
def rodar_ml():
    try:
        run_all_ml(current_app._get_current_object())
        return jsonify({'status': 'ok', 'mensagem': 'ML executado com sucesso!'})
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@ml_bp.route('/resumo/<circuito>')
@login_required
def resumo_ml(circuito):
    import json
    from models import AnomaliaML
    resultado = {}
    for algo in ('isolation_forest', 'kmeans', 'regressao'):
        ul = AnomaliaML.query.filter_by(circuito=circuito, algoritmo=algo)\
                             .order_by(AnomaliaML.timestamp.desc()).first()
        if ul and ul.descricao:
            try:
                resultado[algo] = json.loads(ul.descricao)
            except Exception:
                resultado[algo] = {'descricao': ul.descricao}
        else:
            resultado[algo] = None
    return jsonify(resultado)

def iniciar_scheduler(app):
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        s = BackgroundScheduler()
        s.add_job(lambda: run_all_ml(app), 'interval', hours=1,
                  id='ml_job', replace_existing=True)
        s.start()
        print("✓ Scheduler ML: roda automaticamente a cada 1 hora")
        return s
    except ImportError:
        print("⚠ apscheduler não instalado — ML só roda manualmente")
        print("  pip install apscheduler")
        return None
