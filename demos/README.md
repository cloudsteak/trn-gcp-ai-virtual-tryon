# Virtuális próbafülke, helyi Python

Egy személy fotója és egy ruhadarab. A `b_virtual_try_on.py` ugyanazt a `virtual-try-on-001` predict hívást küldi el, mint az `a_virtual_try_on.ipynb` notebook.

A modell nem szöveggel válaszol, hanem egy képet generál. A kész kép a `demos/output/result.png` fájlba kerül.

## Előfeltétel

- Python 3
- Telepített `gcloud` CLI
- GCP projekt, bekapcsolt Vertex AI API (`aiplatform.googleapis.com`)
- A fiókodnak `roles/aiplatform.user` joga van a projekten

## 1. Szükséges komponensek telepítése

A `demos` mappából:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

A `google-auth` kéri le a belépési tokent. A `requests` tölti le a képeket, és küldi el a predict hívást.

## 2. Bejelentkezés a Google Cloud projektbe (ADC)

Application Default Credentials (ADC): a szkript innen olvassa a belépést, külön kulcsfájl nélkül.

Azt a Google-fiókot válaszd, amelyiknek hozzáférése van a GCP projekthez.

```bash
gcloud auth login
gcloud auth application-default login
```

- `gcloud auth login` a `gcloud` parancsokhoz kell.
- `gcloud auth application-default login` az ADC. Ezt használja a szkript.

Utána állítsd be a projektet és a kvótaprojektet. A `GCP_PROJECT_ID` a saját projektazonosítód.

```bash
export GCP_PROJECT_ID=a-projekt-id
gcloud config set project "${GCP_PROJECT_ID}"
gcloud auth application-default set-quota-project "${GCP_PROJECT_ID}"
```

A `set-quota-project` csak az ADC belépés után működik. A hívás számlázása és kvótája ehhez a projekthez tartozik.

## 3. Környezeti változók

A szkript ezeket olvassa. A két kép `https://` link. A link egyenesen a jpg vagy png fájlra mutasson.

```bash
export GCP_PROJECT_ID=a-projekt-id
export GOOGLE_CLOUD_LOCATION=europe-west1
export PERSON_IMAGE_URL=https://raw.githubusercontent.com/cloudsteak/trn-gcp-ai-virtual-tryon/main/images/modell/ferfi_1.jpg
export GARMENT_IMAGE_URL=https://raw.githubusercontent.com/cloudsteak/trn-gcp-ai-virtual-tryon/main/images/ruha/f_ing.jpg
```

| Változó | Mit ad meg |
| --- | --- |
| `GCP_PROJECT_ID` | A GCP projekt azonosítója. Ha üres, a `GOOGLE_CLOUD_PROJECT` értéke is jó. |
| `GOOGLE_CLOUD_LOCATION` | Régió. Alapérték: `europe-west1`. Ezt használd, hacsak a modellt nem másik régióban kapcsoltad be. |
| `PERSON_IMAGE_URL` | A személy fotójának linkje. Erre kerül a ruha. |
| `GARMENT_IMAGE_URL` | Egy ruhadarab linkje. A képen a ruhadarab legyen, egyszerű, világos háttér előtt. |

Egyszerre csak egy ruhadarab megy a személyre.

## 4. Futtatás

A virtuális környezet legyen aktív, a változók legyenek exportálva, majd:

```bash
python b_virtual_try_on.py
```

A generálás körülbelül egy perc. A parancs kiírja a projektet, a két link letöltését, a végpontot, a kérés vázát (a képek helyén helyőrzővel) és a HTTP választ. A végén ez a fájl készül el:

```text
demos/output/result.png
```
