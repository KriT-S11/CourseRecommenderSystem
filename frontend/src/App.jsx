import React, { useState } from "react";
import "./styles.css";

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Use environment variable if provided (Vercel), otherwise rely on local proxy "/recommend"
  const BACKEND = (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.replace(/\/$/, "")) || "/recommend";

  async function doSearch(e) {
    if (e) e.preventDefault();
    setError(null);

    const q = query.trim();
    if (!q) {
      setError("Type a course name to search");
      return;
    }

    setLoading(true);
    setResults([]);

    try {
      // If REACT_APP_API_URL points directly to the endpoint (e.g. https://api.example.com/recommend),
      // use it as-is. If it's a host (like https://api.example.com), append /recommend.
      let url = BACKEND;
      if (!url.includes("/recommend")) {
        // BACKEND could be "/recommend" or "http(s)://host" - handle both
        url = url === "/recommend" ? "/recommend" : `${url}/recommend`;
      }

      url = `${url}?q=${encodeURIComponent(q)}&top_n=4`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      const items = data.results || data || [];
      setResults(items);
    } catch (err) {
      console.error(err);
      setError("Could not fetch results from backend. Check backend is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-root">
      <header className="header">
        <h1 className="title">Course Recommendation System</h1>

        <nav className="nav">
          <a
            href="https://www.udemy.com/courses/search/?q=data%20science"
            target="_blank"
            rel="noreferrer"
          >
            Data Science Mastery
          </a>

          <a
            href="https://www.udemy.com/courses/search/?q=full%20stack%20web%20development"
            target="_blank"
            rel="noreferrer"
          >
            Full Stack Web Development
          </a>

          <a
            href="https://www.udemy.com/courses/search/?q=machine%20learning"
            target="_blank"
            rel="noreferrer"
          >
            AI &amp; Machine Learning
          </a>

          <a
            href="https://www.udemy.com/courses/search/?q=python%20for%20beginners"
            target="_blank"
            rel="noreferrer"
          >
            Python for Beginners
          </a>
        </nav>
      </header>

      <main className="container">
        <div className="hint">Enter prerequisites e.g., Algorithm</div>

        <form className="search-row" onSubmit={doSearch}>
          <input
            className="search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter prerequisites e.g., Algorithm"
            aria-label="Search courses"
          />
          <button className="btn-search" type="submit" aria-label="Search">
            Search
          </button>
        </form>

        {loading && <div className="status">Searching…</div>}
        {error && <div className="status error">{error}</div>}

        <div className="results" aria-live="polite">
          {/* sample cards when no results yet */}
          {results.length === 0 && !loading && !error && (
            <>
              <div className="card sample">
                <div className="accent" />
                <div className="card-body">
                  <div className="card-title">Algorithms and Data Structures</div>
                  <div className="card-sub">Master algorithms and data structures in depth.</div>
                </div>
                <div className="card-meta">
                  <div>Rating: 4.7</div>
                </div>
              </div>

              <div className="card sample">
                <div className="accent" />
                <div className="card-body">
                  <div className="card-title">Competitive Programming</div>
                  <div className="card-sub">Learn algorithms to solve problems quickly.</div>
                </div>
                <div className="card-meta">
                  <div>Rating: 4.6</div>
                </div>
              </div>
            </>
          )}

          {/* actual results from backend */}
          {results.map((r, i) => (
            <a
              key={i}
              className="card"
              href={r.url || "#"}
              target="_blank"
              rel="noreferrer"
            >
              <div className="accent" />
              <div className="card-body">
                <div className="card-title">{r.title}</div>
                <div className="card-sub">{r.description ?? r.headline ?? ""}</div>
              </div>
              <div className="card-meta">
                <div>Rating: {r.rating ?? "N/A"}</div>
                <div className="score">Score: {r.score ? r.score.toFixed(3) : "—"}</div>
              </div>
            </a>
          ))}
        </div>
      </main>
    </div>
  );
}
