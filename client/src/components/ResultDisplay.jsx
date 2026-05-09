// Ha nincs meg eredmeny, semmit sem jelenítunk meg
export default function ResultDisplay({ imageUrl }) {
  if (!imageUrl) return null;

  return (
    <div className="mt-8 flex flex-col items-center">
      <h2 className="text-lg font-semibold text-gray-700 mb-4">Eredmény</h2>
      {/* Az AI altal generalt kep teljes szelessegben */}
      <img
        src={imageUrl}
        alt="Virtuális próba eredménye"
        className="w-full max-w-2xl rounded-2xl shadow-lg"
      />
    </div>
  );
}
