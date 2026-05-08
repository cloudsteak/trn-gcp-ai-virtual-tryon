# Virtuális Próbafülke – GCP AI Demo

## Mi ez az alkalmazás?

Ez egy demo alkalmazás, amellyel kipróbálhatod, hogyan néznél ki egy ruhában – anélkül, hogy fel kellene próbálnod. Feltöltöd a saját képedet és egy ruhadarab képét, az AI pedig megmutatja, hogyan nézne ki rajtad. A varázslatot a Google Vertex AI `virtual-try-on-001` modellje végzi.

---

## Hogyan működik?

1. **Feltöltöd a képeket** – a bal oldalra a saját fotód, a jobb oldalra a ruhadarab képe kerül.
2. **Az AI dolgozik** – a „Próbáld fel!" gombra kattintva a szerver elküldi a képeket a Google mesterséges intelligenciájának.
3. **Megjelenik az eredmény** – néhány másodpercen belül látod, hogyan áll rajtad a ruha.

---

## Előfeltételek

- Google Cloud Platform (GCP) projekt
- A Vertex AI API engedélyezve a projektben
- `gcloud` CLI telepítve (lásd lent)
- Node.js 20+ és Python 3.12+ telepítve helyileg
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

A szerver a Google ADC (Application Default Credentials) rendszert használja – ez azt jelenti, hogy a gépeden tárolt bejelentkezési tokened alapján hitelesíti magát, nem pedig egy hardkódolt jelszóval. A `GCP_PROJECT_ID` csak megmondja, melyik projektbe küldje a kéréseket – önmagában nem jelent hozzáférést.

```bash
gcloud auth login
gcloud config set project PROJEKT_ID
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
# Szerkeszd a .env fájlt: add meg a GCP_PROJECT_ID és MODEL_NAME értékét

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

## Cloud Run deployment lépésről lépésre

### Backend deploy

```bash
cd server

# Docker image build és push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/virtual-tryon-server

# Cloud Run service létrehozása
gcloud run deploy virtual-tryon-server \
  --image gcr.io/YOUR_PROJECT_ID/virtual-tryon-server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID,ALLOWED_ORIGIN=https://YOUR_CLIENT_URL
```

### Frontend deploy

```bash
cd client

# Docker image build és push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/virtual-tryon-client

# Cloud Run service létrehozása
gcloud run deploy virtual-tryon-client \
  --image gcr.io/YOUR_PROJECT_ID/virtual-tryon-client \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=https://YOUR_SERVER_URL
```

---

## A „törött" állapotról

Az alkalmazás alapállapotban szándékosan nem működik teljesen: a `server/.env` fájlban a `MODEL_NAME` értéke üresen van hagyva – ezt a képzésen töltjük ki együtt a résztvevőkkel a Vertex AI Model Garden adatlapja alapján.
