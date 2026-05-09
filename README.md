# Virtuális Próbafülke – GCP AI Demo

## Mi ez az alkalmazás?

Ez egy demo alkalmazás, amellyel kipróbálhatod, hogyan néznél ki különböző ruhákban – anélkül, hogy fel kellene próbálnod. Feltöltöd a saját képedet és a ruhadarabokat (felső, nadrág, lábeli), az AI pedig megmutatja, hogyan néznének ki rajtad. A varázslatot a Google Agent Platform `virtual-try-on-001` modellje végzi.

---

## Hogyan működik?

1. **Feltöltöd a képeket** – bal oldalra a saját fotód, jobb oldalra a ruhadarabok (felső, nadrág, lábeli).
2. **Az AI dolgozik** – a „Próbáld fel!" gombra kattintva a szerver egymás után küldi el a ruhadarabokat a Google AI-nak; minden körben az előző eredménykép lesz az új alap.
3. **Megjelenik az eredmény** – néhány másodpercen belül látod, hogyan állnak rajtad a ruhák.

---

## Előfeltételek

- Google Cloud Platform (GCP) projekt
- Agent Platform API engedélyezve a projektben (`aiplatform.googleapis.com`)
- `gcloud` CLI telepítve (lásd lent)
- Node.js 22 vagy 24 és Python 3.12+ telepítve helyileg
- `uv` Python csomagkezelő (`pip install uv`)

---

## A gcloud CLI telepítése

### Windows

1. Töltsd le a telepítőt: [https://cloud.google.com/sdk/docs/install#windows](https://cloud.google.com/sdk/docs/install#windows)
2. Futtasd a `.exe` telepítőt, kövesd a lépéseket
3. A telepítő végén indítsd el a `gcloud init` parancsot az inicializáláshoz

Vagy PowerShell-lel:
```powershell
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

### macOS

Homebrew-val (ajánlott):
```bash
brew install --cask google-cloud-sdk
```

Vagy manuálisan:
```bash
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-x86_64.tar.gz
tar -xf google-cloud-cli-darwin-x86_64.tar.gz
./google-cloud-sdk/install.sh
```

### Linux

```bash
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
tar -xf google-cloud-cli-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
source ~/.bashrc
```

### Telepítés után (minden platformon)

```bash
gcloud init
```

---

## Lokális futtatás lépésről lépésre

### 1. Google Cloud bejelentkezés

A szerver ADC (Application Default Credentials) autentikációt használ – a gépeden tárolt bejelentkezési tokened alapján hitelesíti magát. A `GCP_PROJECT_ID` megmondja, melyik projektbe küldje a kéréseket – önmagában nem jelent hozzáférést.

```bash
gcloud auth login
gcloud config set project PROJECT_ID
gcloud auth application-default login
```

Ezeket csak egyszer kell futtatni. Cloud Run-on ezt a Service Account végzi automatikusan.

### 2. Backend (server)

```bash
cd server

# Függőségek telepítése uv-vel
uv sync

# Környezeti változók beállítása
cp .env.example .env
# Szerkeszd a .env fájlt: add meg a GCP_PROJECT_ID értékét

# Szerver indítása
uv run uvicorn virtual_tryon.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env
```

### 3. Frontend (client)

```bash
cd client

# Függőségek telepítése
npm install

# Fejlesztői szerver indítása
npm run dev
```

Nyisd meg a böngészőben: [http://localhost:5173](http://localhost:5173)

---

## Repo struktúra

```
trn-gcp-ai-virtual-tryon/
├── client/                          # Cloud Run #1 – React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ImageUploader.jsx    # Kép feltöltő komponens
│   │   │   └── ResultDisplay.jsx    # Eredmény megjelenítő komponens
│   │   ├── App.jsx                  # Fő alkalmazás komponens
│   │   └── main.jsx                 # Belépési pont
│   ├── vite.config.js               # Vite konfiguráció + API proxy
│   ├── Dockerfile                   # Nginx + React build
│   └── nginx.conf                   # Nginx konfiguráció
│
├── server/                          # Cloud Run #2 – Python FastAPI backend
│   ├── src/
│   │   └── virtual_tryon/
│   │       ├── config.py            # Környezeti változók
│   │       ├── main.py              # FastAPI app és endpoint
│   │       └── agent_platform.py   # Agent Platform API hívás
│   ├── pyproject.toml               # uv csomagkezelő konfiguráció
│   └── Dockerfile                   # Python Cloud Run konténer
│
└── test_images/                     # Demo képek a képzéshez
    ├── persons/                     # Személy fotók (ferfi_1.jpg, no_1.jpg, ...)
    └── dress/                       # Ruhadarabok (ing, nadrág, cipő, ...)
```

---

## Környezeti változók

### Server (`server/.env`)

| Változó | Leírás | Alapértelmezett |
|---|---|---|
| `GCP_PROJECT_ID` | GCP projekt azonosító | – |
| `GOOGLE_CLOUD_LOCATION` | GCP régió | `europe-west1` |
| `ALLOWED_ORIGIN` | Frontend URL (CORS) | `http://localhost:5173` |
| `MODEL_NAME` | Vertex AI modell neve | `virtual-try-on-001` |

### Client (`client/.env`)

| Változó | Leírás | Alapértelmezett |
|---|---|---|
| `VITE_API_URL` | Backend URL | _(üres, proxy használ)_ |

---

## Cloud Run deployment lépésről lépésre

### Backend deploy

```bash
cd server

# Project ID és egyéb környezeti változók beállítása a build során
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export ALLOWED_ORIGIN=https://YOUR_CLIENT_URL

# Docker image build és push
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/virtual-tryon-server

# Cloud Run service létrehozása
gcloud run deploy virtual-tryon-server \
  --image gcr.io/$GCP_PROJECT_ID/virtual-tryon-server \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,ALLOWED_ORIGIN=$ALLOWED_ORIGIN
```

### Frontend deploy

```bash
cd client

# Project ID és egyéb környezeti változók beállítása a build során
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export VITE_API_URL=https://YOUR_SERVER_URL

# Docker image build és push
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/virtual-tryon-client

# Cloud Run service létrehozása
gcloud run deploy virtual-tryon-client \
  --image gcr.io/$GCP_PROJECT_ID/virtual-tryon-client \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=$VITE_API_URL
```

---

## A „törött" állapotról

Az alkalmazás alapállapotban szándékosan nem működik teljesen: a `server/.env` fájlban a `GCP_PROJECT_ID` értéke üresen van hagyva – ezt a képzésen töltjük ki együtt a résztvevőkkel.
