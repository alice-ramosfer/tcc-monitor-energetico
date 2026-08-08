// ================================================================
//  ESP32 → Servidor Flask — Envio dos 3 PZEMs
//  Biblioteca: PZEM004Tv30 + ArduinoJson (Library Manager)
// ================================================================
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PZEM004Tv30.h>

const char* WIFI_SSID     = "Nome_da_Rede";
const char* WIFI_PASSWORD = "Senha_da_Rede";
const char* SERVER_URL    = "http://SEU_IP:5000/api/dados"; // ou URL Railway
const char* API_KEY       = "tcc-esp32-2026";
const unsigned long INTERVALO = 10000;

PZEM004Tv30 pzem1(Serial2, 16, 17);  // Sala de Aula

unsigned long t0 = 0;

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 16, 17);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nConectado! IP: " + WiFi.localIP().toString());
}

void loop() {
  if (millis() - t0 < INTERVALO) return;
  t0 = millis();

  float v  = pzem1.voltage();
  float i  = pzem1.current();
  float p  = pzem1.power();
  float e  = pzem1.energy();
  float pf = pzem1.pf();
  float hz = pzem1.frequency();

  if (isnan(v)) { Serial.println("NaN — verifique conexões"); return; }

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

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  int code = http.POST(payload);
  Serial.printf("POST %s → HTTP %d | V:%.1f I:%.3f P:%.0f\n",
                SERVER_URL, code, v, i, p);
  http.end();
}
