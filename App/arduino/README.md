# Arduino / ESP32 → TRUST-PWS

Envoi direct des mesures **température, humidité, pression** vers l’API.

## 1. Lancer l’API (depuis `App/api`)

> Ne lancez **pas** uvicorn depuis la racine du dépôt.  
> Dossier obligatoire : `App/api` (sinon `No module named 'app'`).

Sur le PC (même WiFi que l’ESP32), depuis la racine du dépôt :

```powershell
cd App\api
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Notez l’IP du PC (`ipconfig` sous Windows), ex. `192.168.1.20`.

Vérifier depuis le PC : http://127.0.0.1:8000/iot/status

## 2. Flasher le sketch

Fichier : [`trust_pws_esp32.ino`](trust_pws_esp32.ino)

1. Ouvrir dans Arduino IDE  
2. Renseigner `WIFI_SSID`, `WIFI_PASS`, `API_HOST` (= IP du PC, **pas** `127.0.0.1`)  
3. Carte : ESP32 Dev Module  
4. Téléverser  

## 3. Voir le flux

- UI : http://localhost:5173/iot  
- API : http://IP_DU_PC:8000/iot/status  

Sans matériel : bouton **Simuler sans matériel** dans l’UI, ou :

```powershell
# depuis App/api, API déjà démarrée — via navigateur / curl
# POST http://127.0.0.1:8000/iot/simulate?n=30
```

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

```text
GET /iot/ingest?device_id=esp32&t=22.5&h=55&p=1013
```
