# Virtuális Próbafülke – MVP (élő kódépítés)

Ez az útmutató lépésről lépésre végigvezet a minimál prototípus felépítésén. A cél nem a production-ready kód, hanem az, hogy **lásd, hogyan hívja meg a backend a Vertex AI Virtual Try-On modellt**.

A végén ugyanazt csinálod, mint a nagy megoldás – csak sokkal kevesebb fájllal.

---

## 1. Mi ez?

Egy **egy fájlos FastAPI backend** + **egy darab HTML** frontend.

- Feltöltesz egy **személy képet** és egy **ruha képet**
- A backend meghívja a Google Vertex AI `virtual-try-on-001` modelljét
- Visszakapsz egy **generált PNG képet**, ahol a ruha „rá van téve” a modellre

Nincs React, nincs build lépés, nincs Docker – csak Python + böngésző.

```
prototype/
├── backend/
│   ├── main.py              ← minden backend logika itt van
│   ├── requirements.txt     ← pip függőségek
│   ├── example.env          ← másold .env-re és töltsd ki
│   └── .env                 ← lokális beállítások (gitignore!)
└── frontend/
    └── index.html           ← form + fetch hívás
```

---

## 2. Előfeltételek

| Eszköz | Miért kell? |
|---|---|
| **Python 3.12+** | FastAPI backend futtatása |
| **gcloud CLI** | GCP-be bejelentkezés, ADC token |
| **GCP projekt** | Vertex AI API engedélyezve |
| **Böngésző** | HTML frontend megnyitása |

### GCP oldali ellenőrzés

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
```

A `application-default login` adja az ADC tokent – **nem kell API kulcs** a kódba.

---

## 3. Előkészületek

### Mappák létrehozása

```bash
cd prototype
mkdir -p backend frontend
```

### Virtuális környezet (venv)

**macOS / Linux:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Aktiválás után a prompt elején megjelenik a `(.venv)`.

Kilépés a venv-ből (macOS / Linux / Windows – mindenhol ugyanaz):

```bash
deactivate
```

### Függőségek telepítése

Hozd létre a `requirements.txt` fájlt:

```
fastapi
uvicorn[standard]
python-multipart
google-auth
requests
python-dotenv
```

Telepítés:

```bash
pip install -r requirements.txt
```

### Környezeti változók

```bash
cp example.env .env
```

A `.env` tartalma:

```
GCP_PROJECT_ID=your-project-id
GOOGLE_CLOUD_LOCATION=europe-west1
```

A `GCP_PROJECT_ID` legyen a saját GCP projekted azonosítója.

---

## 4. Első lépés – Backend váz (FastAPI + health check)

Hozd létre a `backend/main.py` fájlt a legegyszerűbb tartalommal:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "ok"}
```

### Indítás és teszt

```bash
python -m uvicorn main:app --reload --port 8000
```

Nyisd meg a böngészőben: [http://localhost:8000/](http://localhost:8000/)

Várt eredmény:

```json
{"status": "ok"}
```

Ha ez megvan, a FastAPI fut.

---

## 5. Második lépés – Környezeti változók betöltése

Add hozzá a `.env` olvasást:

```python
import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")

app = FastAPI()
```

Indítsd újra a szervert. Ha hiba nélkül elindul, a `.env` beolvasás működik.

---

## 6. Harmadik lépés – CORS (hogy a HTML is tudjon hívni)

Amikor az `index.html`-t fájlként nyitod meg (`file://`), a böngésző más originről hívja a backendet. MVP-ben egyszerűen mindent engedünk:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 7. Negyedik lépés – A `/try-on` endpoint (fájl fogadás)

Itt kezdődik a lényeg: két képet fogadunk multipart form-data formában – **ugyanazokkal a mezőnevekkel**, mint a nagy megoldásban.

```python
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response

# ... app, CORS, env változók ...


@app.post("/try-on")
async def try_on(
    person_image: UploadFile = File(...),
    product_images: list[UploadFile] = File(...),
):
    person_bytes = await person_image.read()
    product_bytes = await product_images[0].read()

    # TODO: Vertex AI hívás ide kerül
    return Response(b"", media_type="image/png")
```

### Tesztelés curl-lel

Használj képeket a repo `images/` mappájából:

```bash
curl -X POST http://localhost:8000/try-on \
  -F "person_image=@../../images/modell/no_1.jpg" \
  -F "product_images=@../../images/ruha/n_top.jpg" \
  --output result.png
```

Ebben a lépésben még üres a válasz – de az endpoint már fogad fájlokat.

---

## 8. Ötödik lépés – Vertex AI hívás (ADC + predict)

Most jön az AI. A backend:

1. Lekéri az ADC tokent (`gcloud auth application-default login`)
2. Base64-re kódolja a két képet
3. POST-ot küld a Vertex AI `:predict` endpointjára
4. Visszakapott base64 képet PNG-ként adja tovább

```python
import base64

import google.auth
import google.auth.transport.requests
import requests

# ... try_on függvényen belül, a read után ...

credentials, _ = google.auth.default()
credentials.refresh(google.auth.transport.requests.Request())

url = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1"
    f"/projects/{PROJECT_ID}/locations/{LOCATION}"
    f"/publishers/google/models/virtual-try-on-001:predict"
)

response = requests.post(
    url,
    json={
        "instances": [
            {
                "personImage": {
                    "image": {
                        "bytesBase64Encoded": base64.b64encode(person_bytes).decode()
                    }
                },
                "productImages": [
                    {
                        "image": {
                            "bytesBase64Encoded": base64.b64encode(product_bytes).decode()
                        }
                    }
                ],
            }
        ],
        "parameters": {"baseSteps": 10},
    },
    headers={"Authorization": f"Bearer {credentials.token}"},
)

result = response.json()
return Response(
    base64.b64decode(result["predictions"][0]["bytesBase64Encoded"]),
    media_type="image/png",
)
```

### Mi történik itt?

```
Böngésző                    Backend                         Vertex AI
   │                           │                                │
   │  POST /try-on             │                                │
   │  (2 kép)                  │                                │
   │ ─────────────────────────>│                                │
   │                           │  POST .../virtual-try-on-001:predict
   │                           │  (base64 képek + ADC token)    │
   │                           │ ──────────────────────────────>│
   │                           │                                │
   │                           │  PNG (base64 a JSON-ban)       │
   │                           │ <──────────────────────────────│
   │  image/png                │                                │
   │ <─────────────────────────│                                │
```

Ha a curl parancs most már érvényes PNG-t ad vissza, a backend kész.

---

## 9. Hatodik lépés – Frontend (egyetlen HTML)

Hozd létre a `frontend/index.html` fájlt:

```html
<h1>Virtuális Próbafülke</h1>
<form id="form">
  <p>Személy képe: <input type="file" id="person" accept="image/jpeg,image/png"></p>
  <p>Ruha képe: <input type="file" id="product" accept="image/jpeg,image/png"></p>
  <button type="submit">Próbáld fel!</button>
</form>
<img id="result">
<script>
  const API_URL = window.location.protocol === "file:"
    ? "http://localhost:8000"
    : window.location.origin;

  document.getElementById("form").onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("person_image", document.getElementById("person").files[0]);
    formData.append("product_images", document.getElementById("product").files[0]);
    const response = await fetch(API_URL + "/try-on", { method: "POST", body: formData });
    document.getElementById("result").src = URL.createObjectURL(await response.blob());
  };
</script>
```

### Frontend megnyitása – két mód

**A) Fájlként** (legegyszerűbb az elején):

```bash
open frontend/index.html        # macOS
xdg-open frontend/index.html    # Linux
start frontend/index.html       # Windows
```

A script automatikusan a `http://localhost:8000` címre küldi a kérést.

**B) A backend szolgálja ki** (lásd 10. lépés):

[http://localhost:8000/](http://localhost:8000/)

---

## 10. Hetedik lépés – Frontend kiszolgálása a backendből (opcionális)

Ha nem akarod külön megnyitni az HTML-t, a FastAPI statikusan kiszolgálja:

```python
from pathlib import Path

from fastapi.staticfiles import StaticFiles

# A route-ok UTÁN add hozzá:
app.mount(
    "/",
    StaticFiles(directory=str(Path(__file__).parent.parent / "frontend"), html=True),
    name="frontend",
)
```

> **Figyelem:** Ha ez megvan, töröld (vagy kommenteld ki) a korábbi `@app.get("/")` health check route-ot – különben a `/` továbbra is JSON-t ad vissza az HTML helyett.

Most már elég a [http://localhost:8000/](http://localhost:8000/) megnyitása.

---

## 11. Végleges ellenőrzőlista

- [ ] `gcloud auth application-default login` lefutott
- [ ] `.env`-ben helyes a `GCP_PROJECT_ID`
- [ ] `pip install -r requirements.txt` lefutott
- [ ] `python -m uvicorn main:app --reload --port 8000` fut
- [ ] `GET /` vagy a frontend betöltődik
- [ ] Két kép feltöltése + „Próbáld fel!” → generált kép megjelenik

---

## 12. Hibakeresés

| Tünet | Valószínű ok | Megoldás |
|---|---|---|
| `ModuleNotFoundError: No module named 'google'` | A venv nincs aktiválva, vagy a rendszer Python fut | `source .venv/bin/activate`, majd `pip install -r requirements.txt`, végül `python -m uvicorn ...` (ne sima `uvicorn`) |
| `KeyError: GCP_PROJECT_ID` | Hiányzó `.env` | `cp example.env .env` és töltsd ki |
| `403 Forbidden` Vertex AI-tól | Nincs jogosultság / API | `aiplatform.googleapis.com` engedélyezése, IAM ellenőrzés |
| `DefaultCredentialsError` | Nincs ADC token | `gcloud auth application-default login` |
| CORS hiba a böngészőben | CORS middleware hiányzik | 6. lépés CORS blokk |
| Üres vagy hibás kép | Rossz képfájl / API hiba | Nézd a backend terminál kimenetét |
| `/` JSON-t ad HTML helyett | Health check route még aktív | Töröld a `read_root`-ot a static mount után |

---

## 13. Mi a különbség a nagy megoldáshoz képest?

| | MVP (prototype) | Nagy megoldás (server + client) |
|---|---|---|
| Backend fájlok | 1 db `main.py` | FastAPI modulok, config, agent_platform |
| Frontend | 1 db HTML | React + Vite + Tailwind |
| Auth | ADC (gcloud login) | ADC (Cloud Run-on Service Account) |
| Ruhadarabok | 1 db | Több, láncolt próbafülke |
| API összefoglaló stream | nincs | van (képzéshez) |
| Deploy | lokálisan fut | Cloud Run + GitHub Actions |

Az API szerződés (`POST /try-on`, `person_image`, `product_images`, PNG válasz) **megegyezik** – innen érthető, miért skálázható a nagy verzió.

---

## Gyors indítás (ha már megvan minden fájl)

```bash
cd prototype/backend
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
# Kilépés: deactivate
cp example.env .env                # töltsd ki!
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Böngésző: [http://localhost:8000/](http://localhost:8000/) vagy nyisd meg a `frontend/index.html`-t.
