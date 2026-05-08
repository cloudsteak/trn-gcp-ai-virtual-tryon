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
- `gcloud` CLI telepítve és bejelentkezve (`gcloud auth application-default login`)
- Node.js 20+ és Python 3.12+ telepítve helyileg
- `uv` Python csomagkezelő (`pip install uv`)

---

## Lokális futtatás lépésről lépésre

### 1. Google Cloud bejelentkezés

A szerver a Google ADC (Application Default Credentials) rendszert használja – ez azt jelenti, hogy a gépeden tárolt bejelentkezési tokened alapján hitelesíti magát, nem pedig egy hardkódolt jelszóval. A `GCP_PROJECT_ID` csak megmondja, melyik projektbe küldje a kéréseket – önmagában nem jelent hozzáférést.

```bash
gcloud auth application-default login
```

Ezt csak egyszer kell futtatni. Cloud Run-on ezt a Service Account végzi automatikusan.

### 2. Backend (server)

```bash
cd server

# Függőségek telepítése uv-vel
uv sync

# Környezeti változók beállítása
cp .env.example .env
# Szerkeszd a .env fájlt: add meg a GCP_PROJECT_ID értékét

# Szerver indítása
uv run uvicorn virtual_tryon.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend (client)

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

Az alkalmazás alapállapotban szándékosan nem működik teljesen: a `server/src/virtual_tryon/vertex.py` fájlban a Vertex AI modell neve üresen van hagyva – ezt a képzésen töltjük ki együtt a résztvevőkkel.
