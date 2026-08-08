from flask import Blueprint, request, jsonify
from extensions import db
from models import Leitura, AnomaliaML
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)
CIRCUITOS = ('sala_aula', 'robotica', 'recepcao')
API_KEY   = 'tcc-esp32-2026'  # Mude em produção

# ── POST /api/dados — ESP32 envia leitura ──────────────────────
@api_bp.route('/dados', methods=['POST'])
def receber_dados():
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'erro': 'API Key inválida'}), 401

    d = request.get_json(silent=True)
    if not d or d.get('circuito') not in CIRCUITOS:
        return jsonify({'erro': 'JSON inválido ou circuito incorreto'}), 400

    try:
        l = Leitura(
            circuito       = d['circuito'],
            tensao         = float(d.get('tensao', 0)),
            corrente       = float(d.get('corrente', 0)),
            potencia       = float(d.get('potencia', 0)),
            energia_kwh    = float(d.get('energia_kwh', 0)),
            fator_potencia = float(d.get('fator_potencia', 0)),
            frequencia     = float(d.get('frequencia', 0)),
        )
    except (TypeError, ValueError) as e:
        return jsonify({'erro': str(e)}), 400

    db.session.add(l)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': l.id}), 201

# ── GET /api/ultima/<circuito> ─────────────────────────────────
@api_bp.route('/ultima/<circuito>')
def ultima_leitura(circuito):
    if circuito not in CIRCUITOS:
        return jsonify({'erro': 'circuito inválido'}), 400
    l = Leitura.query.filter_by(circuito=circuito).order_by(Leitura.timestamp.desc()).first()
    return jsonify(l.to_dict()) if l else jsonify({'erro': 'sem dados'}), 404

# ── GET /api/historico/<circuito>?horas=24 ─────────────────────
@api_bp.route('/historico/<circuito>')
def historico(circuito):
    if circuito not in CIRCUITOS:
        return jsonify({'erro': 'circuito inválido'}), 400
    horas = int(request.args.get('horas', 24))
    desde = datetime.utcnow() - timedelta(hours=horas)
    ls = (Leitura.query
          .filter(Leitura.circuito == circuito, Leitura.timestamp >= desde)
          .order_by(Leitura.timestamp.asc()).all())
    return jsonify([l.to_dict() for l in ls])

# ── GET /api/resumo — Todas as últimas leituras ────────────────
@api_bp.route('/resumo')
def resumo():
    res = {}
    for c in CIRCUITOS:
        l = Leitura.query.filter_by(circuito=c).order_by(Leitura.timestamp.desc()).first()
        res[c] = l.to_dict() if l else None
    return jsonify(res)

# ── GET /api/anomalias ─────────────────────────────────────────
@api_bp.route('/anomalias')
def anomalias():
    circuito = request.args.get('circuito')
    limite   = int(request.args.get('limite', 20))
    q = AnomaliaML.query.filter_by(eh_anomalia=True)
    if circuito:
        q = q.filter_by(circuito=circuito)
    return jsonify([a.to_dict() for a in q.order_by(AnomaliaML.timestamp.desc()).limit(limite)])

# ── POST /api/simular — Gera dados de teste (só para TCC) ──────
@api_bp.route('/simular', methods=['POST'])
def simular():
    """Insere dados simulados no banco para testar o ML sem o ESP32."""
    import random, math
    from datetime import timedelta

    n = int(request.args.get('n', 200))  # ?n=200
    base = datetime.utcnow() - timedelta(hours=n//6)

    for i in range(n):
        for circuito in CIRCUITOS:
            hora = (base + timedelta(minutes=i*10)).hour
            # Simula padrão: mais consumo em horário escolar
            fator = 1.5 if 7 <= hora <= 17 else 0.3
            pot   = random.uniform(500, 3000) * fator + math.sin(i/10)*100
            l = Leitura(
                circuito       = circuito,
                tensao         = round(random.uniform(235, 245), 1),
                corrente       = round(pot / 240, 3),
                potencia       = round(max(0, pot), 1),
                energia_kwh    = round(i * pot / 360000, 4),
                fator_potencia = round(random.uniform(0.88, 0.98), 2),
                frequencia     = round(random.uniform(59.8, 60.2), 1),
                timestamp      = base + timedelta(minutes=i*10),
            )
            db.session.add(l)
    db.session.commit()
    return jsonify({'status': 'ok', 'leituras': n * 3})
