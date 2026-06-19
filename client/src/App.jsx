import { useState } from "react";
import ImageUploader from "./components/ImageUploader";
import ResultDisplay from "./components/ResultDisplay";

// Backend URL: ures = same-origin /try-on (nginx proxy prod-ban, Vite proxy dev-ben)
function getApiUrl() {
  const runtime = window.__RUNTIME_CONFIG__?.apiUrl;
  if (runtime) return runtime;
  return import.meta.env.VITE_API_URL ?? "";
}

// Ruhadarab slotok definicioja – sorrendben kerulnek feldolgozasra az AI-ban
const GARMENT_SLOTS = [
  { key: "top", label: "Felső (póló, ing, pulóver)" },
  { key: "bottom", label: "Nadrág (farmer, szoknya, rövidnadrág)" },
  { key: "shoes", label: "Lábbeli (cipő, szandál, papucs)" },
];

export default function App() {
  const [personImage, setPersonImage] = useState(null);
  const [garments, setGarments] = useState({ top: null, bottom: null, shoes: null });
  const [resultUrl, setResultUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showModelResponse, setShowModelResponse] = useState(false);
  const [modelResponseText, setModelResponseText] = useState("");

  // Csak a kitoltott ruhadarabok kerulnek elkuldésre
  const filledGarments = GARMENT_SLOTS.map((s) => garments[s.key]).filter(Boolean);

  // A gomb csak akkor aktiv, ha van szemelykep es legalabb egy ruhadarab
  const canSubmit = personImage && filledGarments.length > 0 && !loading;

  function updateGarment(key, file) {
    setGarments((prev) => ({ ...prev, [key]: file }));
  }

  async function handleTryOn() {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setResultUrl(null);
    setModelResponseText("");

    // multipart/form-data osszeallitasa – szemelykep + ruhadarabok
    const formData = new FormData();
    formData.append("person_image", personImage);
    filledGarments.forEach((img) => formData.append("product_images", img));
    formData.append("show_model_response", showModelResponse ? "true" : "false");

    try {
      const response = await fetch(`${getApiUrl()}/try-on`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const msg = await response.text();
        throw new Error(msg || "Ismeretlen hiba történt.");
      }

      if (showModelResponse) {
        const data = await response.json();
        const binary = atob(data.image_base64);
        const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
        const blob = new Blob([bytes], { type: "image/png" });
        setResultUrl(URL.createObjectURL(blob));
        setModelResponseText(JSON.stringify(data.model_summary, null, 2));
      } else {
        // A szerver PNG kepet ad vissza – helyi URL-le alakitjuk a megjeleníteshez
        const blob = await response.blob();
        setResultUrl(URL.createObjectURL(blob));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-indigo-700 mb-2">
          Virtuális Próbafülke
        </h1>
        <p className="text-center text-gray-500 mb-8 text-sm">
          Töltsd fel a személyed képét és a ruhadarabokat – az AI megmutatja, hogyan állnak!
        </p>

        {/* Ket oszlopos layout: bal – szemely, jobb – ruhadarabok */}
        <div className="grid grid-cols-2 gap-6 mb-6 items-stretch">
          <ImageUploader
            label="Személy képe"
            image={personImage}
            onImageSelect={setPersonImage}
            tall
          />
          <div className="flex flex-col gap-4">
            {GARMENT_SLOTS.map((slot) => (
              <ImageUploader
                key={slot.key}
                label={slot.label}
                image={garments[slot.key]}
                onImageSelect={(file) => updateGarment(slot.key, file)}
              />
            ))}
          </div>
        </div>

        <div className="flex flex-col items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={showModelResponse}
              onChange={(event) => setShowModelResponse(event.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            Mutasd az AI modell válaszát (képzéshez)
          </label>

          {showModelResponse && (
            <div className="w-full max-w-2xl">
              <label htmlFor="model-response" className="block text-sm font-medium text-gray-700 mb-1">
                API hívás összefoglaló (kérés / válasz struktúra)
              </label>
              <textarea
                id="model-response"
                readOnly
                value={modelResponseText}
                placeholder="Itt jelenik meg az endpoint, a JSON váz, a képméretek és az időzítés..."
                rows={12}
                className="w-full rounded-lg border border-gray-300 bg-gray-50 p-3 font-mono text-xs text-gray-800 shadow-sm"
              />
            </div>
          )}

          <button
            onClick={handleTryOn}
            disabled={!canSubmit}
            className="px-8 py-3 rounded-full text-white font-semibold text-lg transition-all
              bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? "Az AI dolgozik..." : "Próbáld fel!"}
          </button>

          {/* Betoltes jelzo – amig az AI feldolgozza a kereseket */}
          {loading && (
            <div className="flex items-center gap-2 text-indigo-600 text-sm">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Kérjük várj, ez néhány másodperc lehet...
            </div>
          )}

          {error && (
            <p className="text-red-500 text-sm text-center max-w-md">{error}</p> 
          )}
        </div>

        {/* Generalt kep megjelenitese */}
        <ResultDisplay imageUrl={resultUrl} />
      </div>
    </div>
  );
}
