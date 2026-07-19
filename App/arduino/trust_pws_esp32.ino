/*
 * TRUST-PWS — envoi T/H/P vers l'API FastAPI
 * Matériel typique : ESP32 + BME280 (I2C)
 *
 * Bibliothèques Arduino IDE :
 *  - WiFi (intégré ESP32)
 *  - HTTPClient (intégré ESP32)
 *  - Adafruit BME280 + Adafruit Unified Sensor
 *  - ArduinoJson (optionnel ici : JSON construit à la main)
 *
 * 1) Remplir WIFI_SSID / WIFI_PASS
 * 2) Remplir API_HOST = IP locale du PC qui lance uvicorn
 * 3) uvicorn : python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_BME280.h>

const char* WIFI_SSID = "VOTRE_WIFI";
const char* WIFI_PASS = "VOTRE_MOT_DE_PASSE";

// IP du PC sur le LAN (pas 127.0.0.1 depuis l'ESP32)
const char* API_HOST = "192.168.1.20";
const int   API_PORT = 8000;
const char* DEVICE_ID = "esp32-salon";

Adafruit_BME280 bme;
unsigned long lastSend = 0;
const unsigned long INTERVAL_MS = 10000; // 10 s

void setup() {
  Serial.begin(115200);
  delay(500);

  if (!bme.begin(0x76) && !bme.begin(0x77)) {
    Serial.println("BME280 introuvable — vérifiez le câblage I2C.");
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (millis() - lastSend < INTERVAL_MS) return;
  lastSend = millis();

  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    return;
  }

  float t = bme.readTemperature();
  float h = bme.readHumidity();
  float p = bme.readPressure() / 100.0F; // Pa -> hPa

  if (isnan(t) || isnan(h) || isnan(p)) {
    Serial.println("Lecture capteur invalide");
    return;
  }

  String url = String("http://") + API_HOST + ":" + API_PORT + "/iot/ingest";
  String body = "{";
  body += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  body += "\"temperature\":" + String(t, 2) + ",";
  body += "\"humidity\":" + String(h, 2) + ",";
  body += "\"pressure\":" + String(p, 2);
  body += "}";

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  Serial.printf("POST %s -> %d | %s\n", url.c_str(), code, body.c_str());
  if (code > 0) {
    Serial.println(http.getString());
  }
  http.end();
}
