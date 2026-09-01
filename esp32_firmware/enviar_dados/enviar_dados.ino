#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PZEM004Tv30.h>

const char* WIFI_SSID     = "Ravic";
const char* WIFI_PASSWORD = "19941613";
const char* SERVER_URL    = "https://web-production-0994b.up.railway.app/api/dados";
const char* API_KEY       = "tcc-esp32-2026";
const unsigned long INTERVALO = 10000;

PZEM004Tv30 pzem(Serial2, 16, 17, PZEM_DEFAULT_ADDR);

unsigned long t0 = 0;
int erros_consecutivos = 0;

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.print("Conectando Wi-Fi...");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConectado! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWi-Fi falhou, tentando novamente em breve...");
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n\nIniciando sistema...");

  // Aguarda PZEM estabilizar após ligar
  Serial.println("Aguardando PZEM...");
  delay(5000);

  conectarWiFi();
}

void loop() {
  // Reconecta Wi-Fi se cair
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi caiu, reconectando...");
    conectarWiFi();
    return;
  }

  // Controla intervalo de envio
  if (millis() - t0 < INTERVALO) return;
  t0 = millis();

  // Leitura do PZEM com retry
  float v = pzem.voltage();
  if (isnan(v)) {
    delay(2000);
    v = pzem.voltage();
  }

  if (isnan(v)) {
    erros_consecutivos++;
    Serial.printf("PZEM sem resposta (%d erros consecutivos)\n", erros_consecutivos);
    // A cada 10 erros reinicia o ESP32 automaticamente
    if (erros_consecutivos >= 10) {
      Serial.println("Muitos erros — reiniciando ESP32...");
      delay(1000);
      ESP.restart();
    }
    return;
  }

  // Leitura bem sucedida
  erros_consecutivos = 0;
  float i  = pzem.current();
  float p  = pzem.power();
  float e  = pzem.energy();
  float pf = pzem.pf();
  float hz = pzem.frequency();

  Serial.printf("V:%.1f I:%.3f P:%.0f Hz:%.1f\n", v, i, p, hz);

  // Monta JSON
  StaticJsonDocument<200> doc;
  doc["circuito"]       = "sala_aula";
  doc["tensao"]         = v;
  doc["corrente"]       = i;
  doc["potencia"]       = p;
  doc["energia_kwh"]    = e;
  doc["fator_potencia"] = isnan(pf) ? 0.0 : pf;
  doc["frequencia"]     = isnan(hz) ? 60.0 : hz;

  String payload;
  serializeJson(doc, payload);

  // Envia para o servidor
  HTTPClient http;
  http.begin(SERVER_URL);
  http.setTimeout(8000); // timeout de 8 segundos
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  int code = http.POST(payload);

  if (code == 200 || code == 201) {
    Serial.printf("POST OK → HTTP %d\n", code);
  } else {
    Serial.printf("POST falhou → HTTP %d\n", code);
  }

  http.end();
}
