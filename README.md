# Monitor Energético Escolar — TCC 2026

Sistema completo de monitoramento de energia com Machine Learning.  
**Stack:** Python Flask · SQLite/MySQL · Scikit-learn · Chart.js · Bootstrap 5

---

## 🚀 Como rodar no VS Code

### 1. Abrir no VS Code
```bash
# No terminal do Windows:
cd C:\tcc_energia
code .
```

### 2. Criar ambiente virtual (Ctrl+`)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Rodar o servidor
```bash
python app.py
```

### 5. Acessar no navegador
```
http://localhost:5000
Login: admin@escola.com / admin123
```

---

## 📁 Estrutura de arquivos

```
tcc_energia/
├── app.py              ← ponto de entrada principal
├── extensions.py       ← db e login_manager
├── models.py           ← tabelas do banco (Usuario, Leitura, AnomaliaML)
├── requirements.txt    ← bibliotecas Python
├── Procfile            ← deploy Railway/Render
│
├── routes/
│   ├── auth.py         ← login, logout, criar usuário
│   ├── api.py          ← API REST para o ESP32
│   ├── dashboard.py    ← páginas do site
│   └── ml_routes.py    ← rotas e scheduler do ML
│
├── ml/
│   └── engine.py       ← Isolation Forest + K-Means + Regressão
│
├── templates/
│   ├── base.html       ← layout base com navbar
│   ├── login.html      ← página de login
│   ├── dashboard.html  ← visão geral dos 3 circuitos
│   ├── circuito.html   ← gráficos detalhados por circuito
│   ├── ml.html         ← resultados do Machine Learning
│   └── novo_usuario.html
│
├── static/
│   ├── css/style.css   ← estilos personalizados (tema escuro)
│   └── js/dashboard.js ← Chart.js configuração global
│
└── esp32_firmware/
    └── enviar_dados.ino ← código do ESP32
```

---

## 🧪 Testar sem o ESP32

Com o servidor rodando, abra outro terminal e execute:
```bash
# Insere 200 leituras simuladas
curl -X POST http://localhost:5000/api/simular?n=200

# Depois no site, clique em "Rodar ML"
```

Ou clique no botão **"Simular dados"** no dashboard.

---

## 🤖 Machine Learning

| Algoritmo | O que detecta |
|-----------|---------------|
| **Isolation Forest** | Consumo anômalo (fora do horário, pico incomum) |
| **K-Means (k=3)** | Perfis de uso (matutino, vespertino, fora do expediente) |
| **Regressão Linear** | Tendência e previsão dos próximos 7 dias |

O ML roda automaticamente a cada 1 hora. Precisa de pelo menos 20 leituras por circuito.

---

## 🌐 Deploy gratuito — Railway.app

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login e deploy
railway login
railway init
railway up

# 3. Adicionar variáveis de ambiente no painel Railway:
#    DATABASE_URL = (gerado automaticamente pelo MySQL plugin)
#    SECRET_KEY   = uma-chave-segura-aqui
```

---

## 📡 API do ESP32

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/dados` | POST | Recebe leitura do ESP32 |
| `/api/ultima/<circuito>` | GET | Última leitura de um circuito |
| `/api/historico/<circuito>?horas=24` | GET | Histórico das últimas N horas |
| `/api/resumo` | GET | Últimas leituras dos 3 circuitos |
| `/api/anomalias` | GET | Anomalias detectadas pelo ML |
| `/api/simular?n=200` | POST | Gera dados simulados para teste |
