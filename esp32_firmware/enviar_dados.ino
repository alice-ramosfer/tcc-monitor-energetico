#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PZEM004Tv30.h>

// ── Configurações ─────────────────────────────────────────────
const char* WIFI_SSID     = "Ravic";
const char* WIFI_PASSWORD = "19941613";
const char* SERVER_URL    = "https://https://monitor-energetico.onrender.com.app/api/dados";
const char* API_KEY       = "tcc-esp32-2026";
const unsigned long INTERVALO = 10000; // 10 segundos

// ── 3 PZEMs no mesmo barramento Serial2 (GPIO 16/17) ─────────
PZEM004Tv30 pzem1(Serial2, 16, 17, 0x01); // Sala de Aula
PZEM004Tv30 pzem2(Serial2, 16, 17, 0x02); // Robótica
PZEM004Tv30 pzem3(Serial2, 16, 17, 0x03); // Recepção

unsigned long t0 = 0;
int erros = 0;

// ── Wi-Fi ─────────────────────────────────────────────────────
void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando Wi-Fi");
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500); Serial.print("."); tentativas++;
  }
  if (WiFi.status() == WL_CONNECTED)
    Serial.println("\nConectado! IP: " + WiFi.localIP().toString());
  else
    Serial.println("\nFalhou. Tentando novamente em breve...");
}

// ── Envia 1 leitura ───────────────────────────────────────────
bool enviar(const char* circuito, float v, float i, float p,
            float e, float pf, float hz) {
  StaticJsonDocument<200> doc;
  doc["circuito"]       = circuito;
  doc["tensao"]         = v;
  doc["corrente"]       = i;
  doc["potencia"]       = p;
  doc["energia_kwh"]    = e;
  doc["fator_potencia"] = isnan(pf) ? 0.0 : pf;
  doc["frequencia"]     = isnan(hz) ? 60.0 : hz;

  String payload;
  serializeJson(doc, payload);

  HTTPClient http;
  http.begin(SERVER_URL);
  http.setTimeout(8000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  int code = http.POST(payload);
  http.end();
  return (code == 200 || code == 201);
}

// ── Lê e envia 1 PZEM ─────────────────────────────────────────
void lerEEnviar(PZEM004Tv30 &pzem, const char* nome) {
  float v = pzem.voltage();

  // Retry se NaN
  if (isnan(v)) { delay(1500); v = pzem.voltage(); }

  if (isnan(v)) {
    Serial.printf("[%s] NaN — pulando\n", nome);
    erros++;
    return;
  }

  erros = 0;
  float i  = pzem.current();
  float p  = pzem.power();
  float e  = pzem.energy();
  float pf = pzem.pf();
  float hz = pzem.frequency();

  bool ok = enviar(nome, v, i, p, e, pf, hz);
  Serial.printf("[%s] V:%.1f I:%.3f P:%.0fW → %s\n",
                nome, v, i, p, ok ? "OK" : "FALHOU");
}

// ── Setup ─────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Monitor Energético · Ensina Mais ===");

  // Aguarda PZEMs estabilizarem após ligar
  Serial.println("Aguardando PZEMs inicializarem...");
  delay(5000);

  conectarWiFi();
}

// ── Loop ──────────────────────────────────────────────────────
void loop() {
  // Reconecta Wi-Fi se cair
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi caiu — reconectando...");
    conectarWiFi();
    return;
  }

  // Controla intervalo
  if (millis() - t0 < INTERVALO) return;
  t0 = millis();

  // Lê e envia os 3 circuitos em sequência
  lerEEnviar(pzem1, "quarto_sala");
  delay(500); // pausa entre leituras no barramento
  lerEEnviar(pzem2, "cozinha_servico");
  delay(500);
  lerEEnviar(pzem3, "chuveiro");

  // Reinicia automaticamente após 10 erros seguidos
  if (erros >= 10) {
    Serial.println("Muitos erros — reiniciando...");
    delay(1000);
    ESP.restart();
  }
}