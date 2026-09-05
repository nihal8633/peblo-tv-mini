import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

const SECTION_ORDER = {
  featured: 0,
  series: 1,
  minisodes: 2,
  songs: 3,
};

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return "";

  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;

  if (remaining === 0) {
    return `${minutes} min`;
  }

  return `${minutes}m ${remaining}s`;
}

/*
 * The catalogue already provides the correct artwork URL.
 * Example:
 *   /storage/artworks/example.jpg
 */
function artworkUrl(artwork) {
  if (!artwork) return "";

  if (typeof artwork === "object" && artwork.url) {
    return artwork.url.startsWith("http")
      ? artwork.url
      : `${API_URL}${artwork.url}`;
  }

  if (typeof artwork === "string") {
    return `${API_URL}/storage/${artwork}`;
  }

  return "";
}

function formatSection(section) {
  if (!section) return "";

  return section.charAt(0).toUpperCase() + section.slice(1);
}

function formatLanguage(language) {
  const names = {
    en: "English",
    hi: "Hindi",
  };

  return names[language] || language.toUpperCase();
}

function formatCategory(category) {
  if (!category) return "";

  return category
    .split("-")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() + word.slice(1)
    )
    .join(" ");
}

function getViewerSeasons(show) {
  return (show?.seasons || [])
    .filter(
      (season) => Number(season.season_number) !== 0
    )
    .sort(
      (a, b) =>
        Number(a.season_number) -
        Number(b.season_number)
    );
}

function getEpisodeArtwork(episode, slot) {
  if (episode?.artwork?.[slot]) {
    return episode.artwork[slot];
  }

  if (
    episode?.artwork_by_language &&
    typeof episode.artwork_by_language === "object"
  ) {
    if (episode.artwork_by_language.en?.[slot]) {
      return episode.artwork_by_language.en[slot];
    }

    for (const language of Object.keys(
      episode.artwork_by_language
    )) {
      if (
        episode.artwork_by_language[language]?.[slot]
      ) {
        return episode.artwork_by_language[language][slot];
      }
    }
  }

  return null;
}

function findShowArtwork(show, slot) {
  for (const season of getViewerSeasons(show)) {
    for (const episode of season.episodes || []) {
      const artwork = getEpisodeArtwork(
        episode,
        slot
      );

      if (artwork) {
        return artwork;
      }
    }
  }

  return null;
}

function getAllEpisodes(show) {
  return getViewerSeasons(show).flatMap(
    (season) => season.episodes || []
  );
}

function App() {
  const [catalogue, setCatalogue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [language, setLanguage] = useState("");
  const [category, setCategory] = useState("");

  const [selectedShow, setSelectedShow] = useState(null);

  async function loadCatalogue() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/catalog`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          `Catalogue request failed (${response.status}).`
        );
      }

      const data = await response.json();

      if (
        !data ||
        !Array.isArray(data.sections)
      ) {
        throw new Error(
          "The published catalogue format is invalid."
        );
      }

      setCatalogue(data);
    } catch (err) {
      console.error(
        "Catalogue loading error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load the published catalogue."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCatalogue();
  }, []);

  const allShows = useMemo(() => {
    if (!catalogue?.sections) {
      return [];
    }

    return catalogue.sections.flatMap(
      (section) =>
        (section.shows || []).map((show) => ({
          ...show,
          section:
            show.section || section.section,
        }))
    );
  }, [catalogue]);

  const languages = useMemo(() => {
    const result = new Set();

    for (const show of allShows) {
      for (const episode of getAllEpisodes(show)) {
        for (const item of episode.languages || []) {
          if (item) {
            result.add(item);
          }
        }
      }
    }

    return [...result].sort();
  }, [allShows]);

  const categories = useMemo(() => {
    const result = new Set();

    for (const show of allShows) {
      for (const episode of getAllEpisodes(show)) {
        for (const item of episode.categories || []) {
          if (item) {
            result.add(item);
          }
        }
      }
    }

    return [...result].sort();
  }, [allShows]);

  const filteredShows = useMemo(() => {
    const query = search.trim().toLowerCase();

    return allShows.filter((show) => {
      const episodes = getAllEpisodes(show);

      if (query) {
        const showMatches =
          show.title
            ?.toLowerCase()
            .includes(query) ||
          show.synopsis
            ?.toLowerCase()
            .includes(query) ||
          show.slug
            ?.toLowerCase()
            .includes(query);

        const episodeMatches = episodes.some(
          (episode) => {
            const titleMatches =
              episode.title
                ?.toLowerCase()
                .includes(query);

            const categoryMatches =
              (episode.categories || []).some(
                (item) =>
                  item
                    ?.toLowerCase()
                    .includes(query)
              );

            const languageMatches =
              (episode.languages || []).some(
                (item) =>
                  item
                    ?.toLowerCase()
                    .includes(query)
              );

            return (
              titleMatches ||
              categoryMatches ||
              languageMatches
            );
          }
        );

        if (
          !showMatches &&
          !episodeMatches
        ) {
          return false;
        }
      }

      if (language) {
        const matchesLanguage =
          episodes.some((episode) =>
            (episode.languages || []).includes(
              language
            )
          );

        if (!matchesLanguage) {
          return false;
        }
      }

      if (category) {
        const matchesCategory =
          episodes.some((episode) =>
            (episode.categories || []).includes(
              category
            )
          );

        if (!matchesCategory) {
          return false;
        }
      }

      return true;
    });
  }, [
    allShows,
    search,
    language,
    category,
  ]);

  const sections = useMemo(() => {
    const grouped = new Map();

    for (const show of filteredShows) {
      const section =
        show.section || "series";

      if (!grouped.has(section)) {
        grouped.set(section, []);
      }

      grouped.get(section).push(show);
    }

    return [...grouped.entries()]
      .sort(
        ([a], [b]) =>
          (SECTION_ORDER[a] ?? 999) -
          (SECTION_ORDER[b] ?? 999)
      )
      .map(([name, shows]) => ({
        name,
        shows: [...shows].sort((a, b) =>
          a.title.localeCompare(b.title)
        ),
      }));
  }, [filteredShows]);

  function clearFilters() {
    setSearch("");
    setLanguage("");
    setCategory("");
  }

  if (loading) {
    return (
      <div className="viewer-shell">
        <div className="loading-screen">
          <div className="spinner" />
          <p>Loading Peblo TV...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="viewer-shell">
        <header className="viewer-header">
          <div className="brand">
            <span className="brand-mark">
              P
            </span>

            <span>Peblo TV</span>
          </div>
        </header>

        <main className="error-screen">
          <h1>Unable to load Peblo TV</h1>

          <p>{error}</p>

          <button onClick={loadCatalogue}>
            Try again
          </button>
        </main>
      </div>
    );
  }

  if (selectedShow) {
    return (
      <ShowDetails
        show={selectedShow}
        onBack={() => setSelectedShow(null)}
      />
    );
  }

  return (
    <div className="viewer-shell">
      <header className="viewer-header">
        <div className="brand">
          <span className="brand-mark">
            P
          </span>

          <span>Peblo TV</span>
        </div>

        <nav className="viewer-nav">
          <a href="#home">Home</a>
          <a href="#explore">Explore</a>
        </nav>
      </header>

      <div id="home">
        {allShows.length > 0 && (
          <Hero
            show={allShows[0]}
            onOpen={() =>
              setSelectedShow(allShows[0])
            }
          />
        )}
      </div>

      <main
        className="viewer-content"
        id="explore"
      >
        <div className="search-area">
          <input
            type="search"
            placeholder="Search shows and episodes..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />

          <select
            value={language}
            onChange={(event) =>
              setLanguage(event.target.value)
            }
          >
            <option value="">
              All languages
            </option>

            {languages.map((item) => (
              <option
                key={item}
                value={item}
              >
                {formatLanguage(item)}
              </option>
            ))}
          </select>

          <select
            value={category}
            onChange={(event) =>
              setCategory(event.target.value)
            }
          >
            <option value="">
              All categories
            </option>

            {categories.map((item) => (
              <option
                key={item}
                value={item}
              >
                {formatCategory(item)}
              </option>
            ))}
          </select>
        </div>

        {(search || language || category) && (
          <div className="filter-summary">
            <span>
              {filteredShows.length}{" "}
              {filteredShows.length === 1
                ? "show"
                : "shows"}{" "}
              found
            </span>

            <button
              type="button"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          </div>
        )}

        {filteredShows.length === 0 ? (
          <div className="empty-state">
            <h2>No results found</h2>

            <p>
              Try another search or remove a
              filter.
            </p>

            <button
              type="button"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          </div>
        ) : (
          sections.map((section) => (
            <section
              className="content-section"
              key={section.name}
            >
              <div className="section-heading">
                <h2>
                  {formatSection(section.name)}
                </h2>

                <span>
                  {section.shows.length}{" "}
                  {section.shows.length === 1
                    ? "show"
                    : "shows"}
                </span>
              </div>

              <div className="show-row">
                {section.shows.map((show) => (
                  <ShowCard
                    key={show.slug}
                    show={show}
                    onOpen={() =>
                      setSelectedShow(show)
                    }
                  />
                ))}
              </div>
            </section>
          ))
        )}
      </main>

      <footer className="viewer-footer">
        <strong>Peblo TV</strong>

        <span>
          Kids content made simple.
        </span>
      </footer>
    </div>
  );
}

function Hero({ show, onOpen }) {
  const banner = findShowArtwork(
    show,
    "banner"
  );

  return (
    <section className="hero">
      {banner ? (
        <img
          className="hero-image"
          src={artworkUrl(banner)}
          alt={show.title}
          onError={(event) => {
            event.currentTarget.style.display =
              "none";
          }}
        />
      ) : (
        <div className="hero-placeholder">
          <div className="hero-placeholder-content">
            <span>
              {show.title?.charAt(0) || "P"}
            </span>
          </div>
        </div>
      )}

      <div className="hero-overlay" />

      <div className="hero-content">
        <span className="hero-label">
          {formatSection(
            show.section || "featured"
          )}
        </span>

        <h1>{show.title}</h1>

        <p>
          {show.synopsis ||
            "Discover great stories on Peblo TV."}
        </p>

        <button onClick={onOpen}>
          Watch now
        </button>
      </div>
    </section>
  );
}

function ShowCard({ show, onOpen }) {
  const poster =
    findShowArtwork(show, "poster") ||
    findShowArtwork(show, "thumbnail") ||
    findShowArtwork(show, "banner");

  const episodeCount =
    getAllEpisodes(show).length;

  return (
    <article
      className="show-card"
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (
          event.key === "Enter" ||
          event.key === " "
        ) {
          event.preventDefault();
          onOpen();
        }
      }}
    >
      <div className="poster-wrapper">
        {poster ? (
          <img
            src={artworkUrl(poster)}
            alt={show.title}
            loading="lazy"
            onError={(event) => {
              event.currentTarget.style.display =
                "none";
            }}
          />
        ) : (
          <div className="poster-placeholder">
            <span>
              {show.title?.charAt(0) || "P"}
            </span>
          </div>
        )}
      </div>

      <div className="show-card-body">
        <h3>{show.title}</h3>

        <p>
          {episodeCount}{" "}
          {episodeCount === 1
            ? "episode"
            : "episodes"}
        </p>
      </div>
    </article>
  );
}

function ShowDetails({ show, onBack }) {
  const banner =
    findShowArtwork(show, "banner") ||
    findShowArtwork(show, "poster") ||
    findShowArtwork(show, "thumbnail");

  const seasons = getViewerSeasons(show);

  return (
    <div className="viewer-shell">
      <header className="viewer-header">
        <div className="brand">
          <span className="brand-mark">
            P
          </span>

          <span>Peblo TV</span>
        </div>

        <nav className="viewer-nav">
          <button
            className="back-button"
            onClick={onBack}
          >
            ← Back
          </button>
        </nav>
      </header>

      <main className="details-page">
        <button
          className="back-button"
          onClick={onBack}
        >
          ← Back to shows
        </button>

        <section className="details-hero">
          {banner ? (
            <img
              src={artworkUrl(banner)}
              alt={show.title}
              className="details-banner"
              onError={(event) => {
                event.currentTarget.style.display =
                  "none";
              }}
            />
          ) : (
            <div className="details-banner-placeholder">
              <span>
                {show.title?.charAt(0) || "P"}
              </span>
            </div>
          )}

          <div className="details-overlay" />

          <div className="details-content">
            <span className="hero-label">
              {formatSection(
                show.section || "series"
              )}
            </span>

            <h1>{show.title}</h1>

            <p>
              {show.synopsis ||
                "Discover this show on Peblo TV."}
            </p>
          </div>
        </section>

        {seasons.length === 0 ? (
          <div className="empty-state">
            <h2>No episodes available</h2>

            <p>
              This show does not currently have
              published episodes.
            </p>
          </div>
        ) : (
          seasons.map((season) => (
            <section
              className="season-section"
              key={season.season_number}
            >
              <div className="section-heading">
                <h2>
                  Season{" "}
                  {season.season_number}
                </h2>

                <span>
                  {(season.episodes || []).length}{" "}
                  {(season.episodes || []).length ===
                  1
                    ? "episode"
                    : "episodes"}
                </span>
              </div>

              <div className="episode-grid">
                {(season.episodes || []).map(
                  (episode) => {
                    const thumbnail =
                      getEpisodeArtwork(
                        episode,
                        "thumbnail"
                      ) ||
                      getEpisodeArtwork(
                        episode,
                        "banner"
                      ) ||
                      getEpisodeArtwork(
                        episode,
                        "poster"
                      );

                    return (
                      <article
                        className="episode-card"
                        key={`${episode.content_group}-${episode.episode_number}`}
                      >
                        <div className="episode-image">
                          {thumbnail ? (
                            <img
                              src={artworkUrl(
                                thumbnail
                              )}
                              alt={episode.title}
                              loading="lazy"
                              onError={(event) => {
                                event.currentTarget.style.display =
                                  "none";
                              }}
                            />
                          ) : (
                            <div className="episode-placeholder">
                              {
                                episode.episode_number
                              }
                            </div>
                          )}
                        </div>

                        <div className="episode-body">
                          <span>
                            Episode{" "}
                            {
                              episode.episode_number
                            }
                          </span>

                          <h3>
                            {episode.title}
                          </h3>

                          <p>
                            {(episode.languages ||
                              []
                            )
                              .map((item) =>
                                formatLanguage(
                                  item
                                )
                              )
                              .join(" • ")}

                            {episode
                              .duration_seconds
                              ? ` • ${formatDuration(
                                  episode.duration_seconds
                                )}`
                              : ""}
                          </p>

                          {episode.categories
                            ?.length > 0 && (
                            <div className="category-list">
                              {episode.categories.map(
                                (item) => (
                                  <span
                                    className="category-badge"
                                    key={item}
                                  >
                                    {formatCategory(
                                      item
                                    )}
                                  </span>
                                )
                              )}
                            </div>
                          )}

                          {episode.languages
                            ?.length > 0 && (
                            <div className="language-list">
                              {episode.languages.map(
                                (item) => (
                                  <span
                                    className="language-badge"
                                    key={item}
                                  >
                                    {formatLanguage(
                                      item
                                    )}
                                  </span>
                                )
                              )}
                            </div>
                          )}
                        </div>
                      </article>
                    );
                  }
                )}
              </div>
            </section>
          ))
        )}
      </main>

      <footer className="viewer-footer">
        <strong>Peblo TV</strong>

        <span>
          Kids content made simple.
        </span>
      </footer>
    </div>
  );
}

export default App;
