import { Link } from "react-router-dom";

function HomePage() {
  return (
    <section className="space-y-8 text-center">
      <div className="card mx-auto max-w-2xl">
        <h1 className="font-display text-4xl text-leafy-800">
          Welcome to Leafy Cave
        </h1>
        <p className="mt-4 text-lg text-leafy-700">
          Your personal AI concierge for an unforgettable Sri Lankan stay. Ask
          about packages, local cuisine, cultural sites, and tailor-made
          itineraries — all with warm, island hospitality.
        </p>
        <Link to="/chat" className="btn-primary mt-6 inline-block">
          Start chatting with LeafyMind
        </Link>
      </div>
    </section>
  );
}

export default HomePage;
