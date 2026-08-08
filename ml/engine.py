# ================================================================
#  ml/engine.py — Motor de Machine Learning
#  Isolation Forest + K-Means + Regressão Linear
# ================================================================

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import json

CIRCUITOS = ('sala_aula', 'robotica', 'recepcao')

# ── FUNÇÃO PRINCIPAL ──────────────────────────────────────────
def run_all_ml(app):
    with app.app_context():
        from models import Leitura, AnomaliaML
        from extensions import db
        print(f"\n[ML] Iniciando análise — {datetime.now().strftime('%H:%M:%S')}")

        for circuito in CIRCUITOS:
            desde = datetime.utcnow() - timedelta(days=7)
            leituras = (Leitura.query
                        .filter(Leitura.circuito == circuito, Leitura.timestamp >= desde)
                        .order_by(Leitura.timestamp.asc()).all())

            if len(leituras) < 20:
                print(f"[ML] {circuito}: poucos dados ({len(leituras)}), pulando")
                continue

            df = _to_df(leituras)

            # 1. Isolation Forest
            anom_if = _isolation_forest(df, circuito)
            for a in anom_if:
                existe = AnomaliaML.query.filter_by(leitura_id=a['leitura_id'],
                                                    algoritmo='isolation_forest').first()
                if not existe:
                    db.session.add(AnomaliaML(**a))

            # 2. K-Means
            km = _kmeans(df, circuito)
            if km:
                db.session.add(AnomaliaML(
                    circuito='all', algoritmo='kmeans',
                    score=km['inercia'], eh_anomalia=False,
                    descricao=json.dumps(km, ensure_ascii=False)
                ))

            # 3. Regressão Linear
            rg = _regressao(df, circuito)
            if rg:
                db.session.add(AnomaliaML(
                    circuito=circuito, algoritmo='regressao',
                    score=rg['r2'], eh_anomalia=False,
                    descricao=json.dumps(rg, ensure_ascii=False)
                ))

            db.session.commit()
            print(f"[ML] {circuito}: {len(anom_if)} anomalias detectadas")


# ── 1. ISOLATION FOREST ───────────────────────────────────────
def _isolation_forest(df, circuito):
    features = ['potencia', 'corrente', 'hora_do_dia', 'dia_semana']
    X = StandardScaler().fit_transform(df[features].values)

    modelo = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    modelo.fit(X)

    df = df.copy()
    df['pred']  = modelo.predict(X)
    df['score'] = modelo.score_samples(X)

    anomalias = []
    for _, row in df[df['pred'] == -1].iterrows():
        hora = int(row['hora_do_dia'])
        pot  = row['potencia']
        if hora < 6 or hora > 22:
            desc = f"{circuito}: consumo de {pot:.0f}W fora do horário ({hora:02d}h)"
        else:
            desc = f"{circuito}: padrão incomum — {pot:.0f}W às {hora:02d}h"
        anomalias.append({
            'circuito': circuito, 'leitura_id': int(row['id']),
            'algoritmo': 'isolation_forest', 'score': float(row['score']),
            'eh_anomalia': True, 'descricao': desc,
        })
    return anomalias


# ── 2. K-MEANS ────────────────────────────────────────────────
def _kmeans(df, circuito):
    if len(df) < 30:
        return None
    features = ['potencia', 'hora_do_dia', 'dia_semana']
    X = StandardScaler().fit_transform(df[features].values)

    modelo = KMeans(n_clusters=3, random_state=42, n_init=10)
    df = df.copy()
    df['cluster'] = modelo.fit_predict(X)

    clusters = []
    for k in range(3):
        sub = df[df['cluster'] == k]
        hora_m = sub['hora_do_dia'].mean()
        pot_m  = sub['potencia'].mean()
        dia_m  = sub['dia_semana'].mean()

        if dia_m >= 5:
            perfil = f"Fim de semana — {pot_m:.0f}W médio"
        elif 7 <= hora_m <= 12:
            perfil = f"Matutino ({hora_m:.0f}h) — {pot_m:.0f}W"
        elif 13 <= hora_m <= 18:
            perfil = f"Vespertino ({hora_m:.0f}h) — {pot_m:.0f}W"
        else:
            perfil = f"Fora do expediente ({hora_m:.0f}h) — {pot_m:.0f}W"

        clusters.append({'cluster': k, 'n': len(sub),
                         'pot_media': round(pot_m, 1),
                         'hora_media': round(hora_m, 1),
                         'perfil': perfil})

    return {'circuito': circuito, 'k': 3,
            'inercia': round(modelo.inertia_, 2),
            'clusters': clusters,
            'timestamp': datetime.now().isoformat()}


# ── 3. REGRESSÃO LINEAR ───────────────────────────────────────
def _regressao(df, circuito):
    if len(df) < 10:
        return None

    df = df.copy()
    df['data'] = df['timestamp'].dt.date
    diario = df.groupby('data')['potencia'].mean().reset_index()
    diario.columns = ['data', 'pot']
    diario['dia_num'] = range(len(diario))

    if len(diario) < 3:
        return None

    X = diario[['dia_num']].values
    y = diario['pot'].values
    modelo = LinearRegression()
    modelo.fit(X, y)

    r2 = modelo.score(X, y)
    ult = len(diario)
    previsao_w   = [max(0, float(modelo.predict([[ult+i]])[0])) for i in range(1, 8)]
    previsao_kwh = [round(p * 10 / 1000, 3) for p in previsao_w]  # 10h/dia escola
    custo_7d     = round(sum(previsao_kwh) * 0.80, 2)

    return {
        'circuito': circuito, 'r2': round(r2, 3),
        'tendencia': 'crescente' if modelo.coef_[0] > 0 else 'decrescente',
        'coef': round(float(modelo.coef_[0]), 4),
        'previsao_7d_kwh': previsao_kwh,
        'custo_7d_reais': custo_7d,
        'pot_atual_w': round(float(y[-1]), 1),
        'timestamp': datetime.now().isoformat(),
    }


# ── UTILITÁRIO ────────────────────────────────────────────────
def _to_df(leituras):
    dados = [{
        'id': l.id, 'circuito': l.circuito,
        'tensao': l.tensao or 0, 'corrente': l.corrente or 0,
        'potencia': l.potencia or 0, 'energia_kwh': l.energia_kwh or 0,
        'fator_potencia': l.fator_potencia or 0, 'frequencia': l.frequencia or 0,
        'timestamp': l.timestamp,
    } for l in leituras]
    df = pd.DataFrame(dados)
    df['hora_do_dia'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60
    df['dia_semana']  = df['timestamp'].dt.dayofweek
    return df
