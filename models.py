from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from zoneinfo import ZoneInfo
BRASILIA = ZoneInfo('America/Sao_Paulo')

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id         = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil     = db.Column(db.String(20), default='viewer')  # admin | viewer
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)

class Leitura(db.Model):
    __tablename__ = 'leituras'
    id             = db.Column(db.Integer, primary_key=True)
    circuito       = db.Column(db.String(30), nullable=False, index=True)
    tensao         = db.Column(db.Float)
    corrente       = db.Column(db.Float)
    potencia       = db.Column(db.Float)
    energia_kwh    = db.Column(db.Float)
    fator_potencia = db.Column(db.Float)
    frequencia     = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.utcnow(), index=True)
    anomalias      = db.relationship('AnomaliaML', backref='leitura', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'circuito': self.circuito,
            'tensao': self.tensao, 'corrente': self.corrente,
            'potencia': self.potencia, 'energia_kwh': self.energia_kwh,
            'fator_potencia': self.fator_potencia, 'frequencia': self.frequencia,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }

class AnomaliaML(db.Model):
    __tablename__ = 'anomalias_ml'
    id          = db.Column(db.Integer, primary_key=True)
    circuito    = db.Column(db.String(50), nullable=False, index=True)
    leitura_id  = db.Column(db.Integer, db.ForeignKey('leituras.id'), nullable=True)
    algoritmo   = db.Column(db.String(50))
    score       = db.Column(db.Float)
    eh_anomalia = db.Column(db.Boolean, default=False)
    descricao   = db.Column(db.Text)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'circuito': self.circuito,
            'leitura_id': self.leitura_id, 'algoritmo': self.algoritmo,
            'score': self.score, 'eh_anomalia': self.eh_anomalia,
            'descricao': self.descricao,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }
