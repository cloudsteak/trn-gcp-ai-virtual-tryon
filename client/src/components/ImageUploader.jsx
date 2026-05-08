import { useRef } from "react";

export default function ImageUploader({ label, image, onImageSelect }) {
  const inputRef = useRef(null);

  function handleFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    onImageSelect(file);
  }

  function handleDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    onImageSelect(file);
  }

  function handleDragOver(e) {
    e.preventDefault();
  }

  return (
    <div
      className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-4 cursor-pointer hover:border-blue-400 transition-colors min-h-64 bg-gray-50"
      onClick={() => inputRef.current.click()}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png"
        className="hidden"
        onChange={handleFileChange}
      />
      <p className="text-sm font-semibold text-gray-500 mb-3">{label}</p>
      {image ? (
        <img
          src={URL.createObjectURL(image)}
          alt={label}
          className="max-h-56 rounded-lg object-contain"
        />
      ) : (
        <div className="flex flex-col items-center text-gray-400">
          <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5V18a2.25 2.25 0 002.25 2.25h13.5A2.25 2.25 0 0021 18v-1.5M16.5 12L12 7.5m0 0L7.5 12M12 7.5V21" />
          </svg>
          <span className="text-sm">Kattints vagy húzd ide a képet</span>
          <span className="text-xs mt-1">JPG, PNG – max 10MB</span>
        </div>
      )}
    </div>
  );
}
