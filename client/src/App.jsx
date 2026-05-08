import { useState } from "react";
import ImageUploader from "./components/ImageUploader";
import ResultDisplay from "./components/ResultDisplay";

const API_URL = import.meta.env.VITE_API_URL ?? "";

export default function App() {
  const [personImage, setPersonImage] = useState(null);
  const [garmentImage, setGarmentImage] = useState(null);
  const [resultUrl, setResultUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const canSubmit = personImage && garmentImage && !loading;

  async function handleTryOn() {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setResultUrl(null);

    const formData = new FormData();
    formData.append("person_image", personImage);
    formData.append("product_image", garmentImage);

    try {
      const response = await fetch(`${API_URL}/try-on`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const msg = await response.text();
        throw new Error(msg || "Ismeretlen hiba történt.");
      }

      const blob = await response.blob();
      setResultUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-indigo-700 mb-2">
          Virtuális Próbafülke
        </h1>
        <p className="text-center text-gray-500 mb-8 text-sm">
          Töltsd fel a személyed képét és a ruhadarabot – az AI megmutatja, hogyan áll!
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <ImageUploader
            label="Személy képe"
            image={personImage}
            onImageSelect={setPersonImage}
          />
          <ImageUploader
            label="Ruhadarab képe"
            image={garmentImage}
            onImageSelect={setGarmentImage}
          />
        </div>

        <div className="flex flex-col items-center mt-6 gap-3">
          <button
            onClick={handleTryOn}
            disabled={!canSubmit}
            className="px-8 py-3 rounded-full text-white font-semibold text-lg transition-all
              bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? "Az AI dolgozik..." : "Próbáld fel!"}
          </button>

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

        <ResultDisplay imageUrl={resultUrl} />
      </div>
    </div>
  );
}
