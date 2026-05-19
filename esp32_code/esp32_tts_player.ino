#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "Audio.h"

// Wi-Fi details
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// Laptop server endpoint
const char* nextUrl = "http://YOUR_LAPTOP_IP:5000/next";

// MAX98357A I2S pins
#define I2S_DOUT 22
#define I2S_BCLK 26
#define I2S_LRC  25

Audio audio;

unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 1000;

void checkForNewAudio() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected");
    return;
  }

  HTTPClient http;
  http.begin(nextUrl);

  int httpCode = http.GET();

  if (httpCode <= 0) {
    Serial.print("HTTP GET failed: ");
    Serial.println(http.errorToString(httpCode));
    http.end();
    return;
  }

  String response = http.getString();
  http.end();

  Serial.println("Server response:");
  Serial.println(response);

  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, response);

  if (error) {
    Serial.println("JSON parse failed");
    return;
  }

  bool available = doc["available"];

  if (available) {
    String audioUrl = doc["audio_url"].as<String>();

    Serial.println("New audio found:");
    Serial.println(audioUrl);

    audio.connecttohost(audioUrl.c_str());
  }
}

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());

  audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  audio.setVolume(12);
}

void loop() {
  audio.loop();

  if (millis() - lastCheckTime > checkInterval) {
    lastCheckTime = millis();
    checkForNewAudio();
  }
}
