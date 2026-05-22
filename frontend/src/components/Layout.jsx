import { Link } from "react-router-dom";

function Layout({ children }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-leafy-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <Link to="/" className="font-display text-2xl text-leafy-800">
            LeafyMind
          </Link>
          <nav className="flex gap-4 text-sm font-medium text-leafy-700">
            <Link to="/" className="hover:text-leafy-900">
              Home
            </Link>
            <Link to="/chat" className="hover:text-leafy-900">
              Concierge
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
      <footer className="border-t border-leafy-200 py-4 text-center text-sm text-leafy-600">
        Leafy Cave · Sri Lanka · Warm welcomes, rooted in island hospitality
      </footer>
    </div>
  );
}

export default Layout;
