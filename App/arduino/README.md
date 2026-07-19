# Arduino / ESP32 → TRUST-PWS

Envoi direct des mesures **température, humidité, pression** vers l’API.

## 1. Lancer l’API accessible sur le WiFi

Sur le PC (même réseau que l’ESP32) :

```bash
cd App/api
.\.venv\Scripts\activate   # Windows
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Notez l’IP du PC (`ipconfig` / `ip a`), ex. `192.168.1.20`.

## 2. Flasher le sketch

Fichier : `trust_pws_esp32.ino`

1. Ouvrir dans Arduino IDE  
2. Renseigner `WIFI_SSID`, `WIFI_PASS`, `API_HOST`  
3. Carte : ESP32 Dev Module  
4. Téléverser  

## 3. Voir le flux

UI : http://localhost:5173/iot  
ou API : http://IP:8000/iot/status

## Endpoint

`POST /iot/ingest`

```json
{
  "device_id": "esp32-salon",
  "temperature": 22.5,
  "humidity": 55.0,
  "pressure": 1013.2
}
```

Sans JSON (GET) :

```
GET /iot/ingest?device_id=esp32&t=22.5&h=55&p=1013
```

Sans matériel : bouton **Simuler sans matériel** dans l’UI, ou `POST /iot/simulate`.
