import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const SECTIONS = [
  "featured",
  "series",
  "minisodes",
  "songs",
];

const LANGUAGES = [
  {
    value: "en",
    label: "English",
  },
  {
    value: "hi",
    label: "Hindi",
  },
];

const CATEGORIES = [
  "adventure",
  "folk",
  "friendship",
  "india",
  "language",
  "learning",
  "maths",
  "music",
  "nature",
  "reading",
  "science",
  "singalong",
  "stories",
  "travel",
  "values",
];

const ARTWORK_SLOTS = [
  {
    slot: "poster",
    label: "Poster",
    width: 600,
    height: 900,
  },
  {
    slot: "banner",
    label: "Banner",
    width: 1280,
    height: 720,
  },
  {
    slot: "thumbnail",
    label: "Thumbnail",
    width: 640,
    height: 360,
  },
];

function getStoredAuth() {
  try {
    const value = localStorage.getItem(
      "peblo_cms_auth",
    );

    if (!value) {
      return null;
    }

    return JSON.parse(value);
  } catch {
    return null;
  }
}

function setStoredAuth(auth) {
  if (!auth) {
    localStorage.removeItem("peblo_cms_auth");
    return;
  }

  localStorage.setItem(
    "peblo_cms_auth",
    JSON.stringify(auth),
  );
}

async function apiRequest(path, options = {}) {
  const auth = getStoredAuth();

  const headers = new Headers(
    options.headers || {},
  );

  if (
    options.body &&
    !(options.body instanceof FormData)
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (auth?.access_token) {
    headers.set(
      "Authorization",
      `Bearer ${auth.access_token}`,
    );
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  let payload;

try {
  payload = await response.json();
} catch {
  // Response body is not JSON.
}

  if (!response.ok) {
    if (response.status === 401) {
      setStoredAuth(null);
      window.location.href = "/";
    }

    let detail = "Request failed.";

    if (typeof payload?.detail === "string") {
      detail = payload.detail;
    } else if (
      payload?.detail?.message
    ) {
      detail = payload.detail.message;

      if (
        Array.isArray(
          payload.detail.errors,
        )
      ) {
        detail +=
          "\n" +
          payload.detail.errors.join("\n");
      }
    }

    throw new Error(detail);
  }

  return payload;
}

function formatError(error) {
  if (!error) {
    return "";
  }

  return error.message || String(error);
}

function StatusBadge({ status }) {
  return (
    <span
      className={`status-badge status-${
        status || "draft"
      }`}
    >
      {status || "draft"}
    </span>
  );
}

function LoadingState({
  text = "Loading...",
}) {
  return (
    <div className="loading">
      <div className="spinner" />
      <div>{text}</div>
    </div>
  );
}

function ErrorState({
  message,
  onRetry,
}) {
  return (
    <div className="error-state">
      <h2>Something went wrong</h2>

      <p>{message}</p>

      {onRetry && (
        <button
          className="button button-primary"
          onClick={onRetry}
        >
          Try again
        </button>
      )}
    </div>
  );
}

function EmptyState({
  title,
  message,
  action,
}) {
  return (
    <div className="empty">
      <h2>{title}</h2>

      <p>{message}</p>

      {action}
    </div>
  );
}

function LoginPage({ onLogin }) {
  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function submit(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const body = new URLSearchParams();

      body.set("username", username);
      body.set("password", password);

      const response = await fetch(
        `${API_URL}/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
          body,
        },
      );

      const payload =
        await response.json();

      if (!response.ok) {
        throw new Error(
          payload?.detail ||
            "Invalid username or password.",
        );
      }

      const auth = {
        access_token:
          payload.access_token,
        token_type:
          payload.token_type,
        username:
          payload.username,
        role: payload.role,
      };

      setStoredAuth(auth);
      onLogin(auth);
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="login-logo">
          <div className="cms-brand-mark">
            P
          </div>

          Peblo TV CMS
        </div>

        <h1>Sign in</h1>

        <p>
          Manage shows, episodes, artwork
          and catalogue publication.
        </p>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <form
          className="login-form"
          onSubmit={submit}
        >
          <div className="form-field">
            <label htmlFor="username">
              Username
            </label>

            <input
              id="username"
              className="input"
              value={username}
              onChange={(event) =>
                setUsername(
                  event.target.value,
                )
              }
              autoComplete="username"
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              className="input"
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value,
                )
              }
              autoComplete="current-password"
              required
            />
          </div>

          <button
            className="button button-primary login-submit"
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

function Layout({
  auth,
  onLogout,
  children,
}) {
  return (
    <div className="cms-shell">
      <header className="cms-header">
        <Link
          to="/shows"
          className="cms-brand"
        >
          <span className="cms-brand-mark">
            P
          </span>

          Peblo TV CMS
        </Link>

        <div className="cms-header-right">
          <span className="role-badge">
            {auth.role}
          </span>

          <span className="user-name">
            {auth.username}
          </span>

          <button
            className="button button-small"
            onClick={onLogout}
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="cms-layout">
        <aside className="cms-sidebar">
          <nav>
            <NavLink
              to="/shows"
              className={({ isActive }) =>
                `nav-link ${
                  isActive ? "active" : ""
                }`
              }
            >
              Shows
            </NavLink>

            <NavLink
              to="/publish"
              className={({ isActive }) =>
                `nav-link ${
                  isActive ? "active" : ""
                }`
              }
            >
              Publish
            </NavLink>
          </nav>
        </aside>

        <main className="cms-main">
          {children}
        </main>
      </div>
    </div>
  );
}

function ShowsPage() {
  const navigate = useNavigate();

  const [query, setQuery] =
    useState("");

  const [section, setSection] =
    useState("");

  const [status, setStatus] =
    useState("");

  const [page, setPage] =
    useState(1);

  const [data, setData] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const pageSize = 10;

  async function loadShows() {
    setLoading(true);
    setError("");

    try {
      const params =
        new URLSearchParams();

      if (query.trim()) {
        params.set(
          "q",
          query.trim(),
        );
      }

      if (section) {
        params.set(
          "section",
          section,
        );
      }

      if (status) {
        params.set(
          "status",
          status,
        );
      }

      params.set(
        "page",
        String(page),
      );

      params.set(
        "page_size",
        String(pageSize),
      );

      const response =
        await apiRequest(
          `/shows/?${params.toString()}`,
        );

      setData(response);
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadShows();
  }, [
    query,
    section,
    status,
    page,
  ]);

  function resetFilters() {
    setQuery("");
    setSection("");
    setStatus("");
    setPage(1);
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Shows</h1>

          <p>
            Manage show metadata and
            editorial status.
          </p>
        </div>

        <div className="page-actions">
          <button
            className="button button-primary"
            onClick={() =>
              navigate("/shows/new")
            }
          >
            + New show
          </button>
        </div>
      </div>

      <div className="filters">
        <input
          className="input"
          placeholder="Search title, synopsis or slug..."
          value={query}
          onChange={(event) => {
            setQuery(
              event.target.value,
            );
            setPage(1);
          }}
        />

        <select
          className="select"
          value={section}
          onChange={(event) => {
            setSection(
              event.target.value,
            );
            setPage(1);
          }}
        >
          <option value="">
            All sections
          </option>

          {SECTIONS.map((value) => (
            <option
              key={value}
              value={value}
            >
              {value}
            </option>
          ))}
        </select>

        <select
          className="select"
          value={status}
          onChange={(event) => {
            setStatus(
              event.target.value,
            );
            setPage(1);
          }}
        >
          <option value="">
            All statuses
          </option>

          <option value="draft">
            Draft
          </option>

          <option value="published">
            Published
          </option>
        </select>

        <button
          className="button"
          onClick={resetFilters}
        >
          Reset
        </button>
      </div>

      <div className="card">
        {loading ? (
          <LoadingState text="Loading shows..." />
        ) : error ? (
          <ErrorState
            message={error}
            onRetry={loadShows}
          />
        ) : !data?.items?.length ? (
          <EmptyState
            title="No shows found"
            message="Try changing your filters or create a new show."
            action={
              <button
                className="button button-primary"
                onClick={() =>
                  navigate(
                    "/shows/new",
                  )
                }
              >
                Create show
              </button>
            }
          />
        ) : (
          <>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Show</th>
                    <th>Section</th>
                    <th>Status</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {data.items.map(
                    (show) => (
                      <tr
                        key={show.id}
                      >
                        <td>
                          <div className="table-title">
                            {show.title}
                          </div>

                          <div className="table-secondary">
                            {show.slug}
                          </div>
                        </td>

                        <td>
                          {show.section ||
                            "—"}
                        </td>

                        <td>
                          <StatusBadge
                            status={
                              show.status
                            }
                          />
                        </td>

                        <td>
                          <button
                            className="button button-small"
                            onClick={() =>
                              navigate(
                                `/shows/${show.id}`,
                              )
                            }
                          >
                            Open
                          </button>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>

            <Pagination
              page={data.page}
              pageSize={
                data.page_size
              }
              count={data.count}
              onPrevious={() =>
                setPage(
                  Math.max(
                    1,
                    page - 1,
                  ),
                )
              }
              onNext={() =>
                setPage(
                  page + 1,
                )
              }
            />
          </>
        )}
      </div>
    </div>
  );
}

function Pagination({
  page,
  pageSize,
  count,
  onPrevious,
  onNext,
}) {
  const canGoNext =
    count >= pageSize;

  return (
    <div className="pagination">
      <div className="pagination-info">
        Page {page} · {count} result
        {count === 1 ? "" : "s"}
      </div>

      <div className="pagination-buttons">
        <button
          className="button button-small"
          onClick={onPrevious}
          disabled={page <= 1}
        >
          Previous
        </button>

        <button
          className="button button-small"
          onClick={onNext}
          disabled={!canGoNext}
        >
          Next
        </button>
      </div>
    </div>
  );
}

function ShowFormPage() {
  const { showId } =
    useParams();

  const navigate =
    useNavigate();

  const isNew =
    showId === "new";

  const [form, setForm] =
    useState({
      slug: "",
      title: "",
      synopsis: "",
      section: "",
    });

  const [show, setShow] =
    useState(null);

  const [episodes, setEpisodes] =
    useState([]);

  const [loading, setLoading] =
    useState(!isNew);

  const [saving, setSaving] =
    useState(false);

  const [publishing, setPublishing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  async function loadShow() {
    if (!showId || isNew) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response =
        await apiRequest(
          `/shows/${showId}`,
        );

      setShow(response);

      setForm({
        slug: response.slug || "",
        title:
          response.title || "",
        synopsis:
          response.synopsis || "",
        section:
          response.section || "",
      });

      const episodeResponse =
        await apiRequest(
          `/episodes/?show_id=${showId}&page=1&page_size=100`,
        );

      setEpisodes(
        episodeResponse.items || [],
      );
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadShow();
  }, [showId]);

  function updateField(
    field,
    value,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function saveShow(
    event,
  ) {
    event.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      if (!showId || isNew) {
      setLoading(false);
        const created =
          await apiRequest(
            "/shows/",
            {
              method: "POST",
              body: JSON.stringify({
                slug: form.slug,
                title: form.title,
                synopsis:
                  form.synopsis,
                section:
                  form.section ||
                  null,
              }),
            },
          );

        navigate(
          `/shows/${created.id}`,
        );

        return;
      }

      const updated =
        await apiRequest(
          `/shows/${showId}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              slug: form.slug,
              title: form.title,
              synopsis:
                form.synopsis,
              section:
                form.section ||
                null,
            }),
          },
        );

      setShow(updated);

      setSuccess(
        "Show changes saved successfully.",
      );
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setSaving(false);
    }
  }

  async function publishShow() {
    setPublishing(true);
    setError("");
    setSuccess("");

    try {
      const updated =
        await apiRequest(
          `/shows/${showId}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              status:
                "published",
            }),
          },
        );

      setShow(updated);

      setSuccess(
        "Show published successfully. You can now publish the catalogue from the Publish page.",
      );
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setPublishing(false);
    }
  }

  if (loading) {
    return (
      <div className="page">
        <LoadingState text="Loading show..." />
      </div>
    );
  }

  if (
    error &&
    !show &&
    !isNew
  ) {
    return (
      <div className="page">
        <ErrorState
          message={error}
          onRetry={loadShow}
        />
      </div>
    );
  }

  const isPublished =
    show?.status ===
    "published";

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button
            className="button button-small"
            onClick={() =>
              navigate("/shows")
            }
          >
            ← Shows
          </button>

          <h1
            style={{
              marginTop: 16,
            }}
          >
            {isNew
              ? "Create show"
              : show?.title ||
                "Show"}
          </h1>

          {!isNew && show && (
            <p>
              <StatusBadge
                status={
                  show.status
                }
              />
            </p>
          )}
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="detail-grid">
        <div>
          <form
            className="card"
            onSubmit={
              saveShow
            }
          >
            <div className="card-header">
              <h2>
                Show details
              </h2>
            </div>

            <div className="card-body">
              {isPublished && (
                <div className="alert alert-info">
                  This show is published and cannot be edited directly.
                </div>
              )}

              <div className="form-grid">
                <div className="form-field">
                  <label htmlFor="slug">
                    Slug
                  </label>

                  <input
                    id="slug"
                    className="input"
                    value={
                      form.slug
                    }
                    disabled={
                      isPublished
                    }
                    onChange={(
                      event,
                    ) =>
                      updateField(
                        "slug",
                        event.target
                          .value,
                      )
                    }
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="section">
                    Section
                  </label>

                  <select
                    id="section"
                    className="select"
                    value={
                      form.section
                    }
                    disabled={
                      isPublished
                    }
                    onChange={(
                      event,
                    ) =>
                      updateField(
                        "section",
                        event.target
                          .value,
                      )
                    }
                  >
                    <option value="">
                      Select section
                    </option>

                    {SECTIONS.map(
                      (value) => (
                        <option
                          key={value}
                          value={
                            value
                          }
                        >
                          {value}
                        </option>
                      ),
                    )}
                  </select>

                  <div className="form-help">
                    Required before publishing a show.
                  </div>
                </div>

                <div className="form-field full">
                  <label htmlFor="title">
                    Title
                  </label>

                  <input
                    id="title"
                    className="input"
                    value={
                      form.title
                    }
                    disabled={
                      isPublished
                    }
                    onChange={(
                      event,
                    ) =>
                      updateField(
                        "title",
                        event.target
                          .value,
                      )
                    }
                    required
                  />
                </div>

                <div className="form-field full">
                  <label htmlFor="synopsis">
                    Synopsis
                  </label>

                  <textarea
                    id="synopsis"
                    className="textarea"
                    value={
                      form.synopsis
                    }
                    disabled={
                      isPublished
                    }
                    onChange={(
                      event,
                    ) =>
                      updateField(
                        "synopsis",
                        event.target
                          .value,
                      )
                    }
                    required
                  />
                </div>
              </div>

              {!isPublished && (
                <div className="form-actions">
                  <button
                    type="submit"
                    className="button button-primary"
                    disabled={
                      saving
                    }
                  >
                    {saving
                      ? "Saving..."
                      : isNew
                        ? "Create show"
                        : "Save changes"}
                  </button>
                </div>
              )}
            </div>
          </form>

          {!isNew && (
            <EpisodeManager
              show={show}
              episodes={
                episodes
              }
            />
          )}
        </div>

        {!isNew && (
          <div className="publish-action">
            <h2>
              Editorial status
            </h2>

            <p>
              Content status controls
              whether this show can be
              included in the published
              catalogue.
            </p>

            {show?.status ===
            "draft" ? (
              <>
                {!show.section && (
                  <div className="publish-warning">
                    Select a section before publishing this show.
                  </div>
                )}

                <button
                  className="button button-success"
                  onClick={
                    publishShow
                  }
                  disabled={
                    publishing ||
                    !show.section
                  }
                >
                  {publishing
                    ? "Publishing..."
                    : "Mark show as published"}
                </button>
              </>
            ) : (
              <StatusBadge
                status="published"
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function EpisodeManager({
  show,
  episodes,
}) {
  const navigate =
    useNavigate();

  return (
    <div
      className="card detail-section"
      style={{
        marginTop: 20,
      }}
    >
      <div className="card-header">
        <div>
          <h2>
            Episodes
          </h2>

          <div className="table-secondary">
            {episodes.length} episode
            {episodes.length ===
            1
              ? ""
              : "s"}
          </div>
        </div>

        <button
          className="button button-primary button-small"
          onClick={() =>
            navigate(
              `/shows/${show.id}/episodes/new`,
            )
          }
        >
          + Add episode
        </button>
      </div>

      <div className="card-body">
        {episodes.length ===
        0 ? (
          <EmptyState
            title="No episodes"
            message="Create an episode for this show."
          />
        ) : (
          <div className="episode-list">
            {episodes.map(
              (episode) => (
                <div
                  className="episode-row"
                  key={
                    episode.id
                  }
                >
                  <div>
                    <div className="episode-title">
                      E
                      {
                        episode.episode_number
                      }{" "}
                      ·{" "}
                      {
                        episode.title
                      }
                    </div>

                    <div className="episode-meta">
                      <span>
                        {
                          episode.language
                        }
                      </span>

                      <span>
                        {episode.duration_seconds
                          ? `${episode.duration_seconds}s`
                          : "No duration"}
                      </span>

                      <span>
                        {
                          episode.content_group
                        }
                      </span>

                      <StatusBadge
                        status={
                          episode.status
                        }
                      />
                    </div>
                  </div>

                  <button
                    className="button button-small"
                    onClick={() =>
                      navigate(
                        `/episodes/${episode.id}`,
                      )
                    }
                  >
                    Edit
                  </button>
                </div>
              ),
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function EpisodeFormPage() {
  const { episodeId, showId } = useParams();

  const navigate = useNavigate();

  const isNew =
    episodeId === "new" || Boolean(showId);

  const [episode, setEpisode] =
    useState(null);

  const [form, setForm] =
    useState({
      episode_id: "",
      season_id: "",
      episode_number: "",
      title: "",
      duration_seconds: "",
      language: "en",
      content_group: "",
      categories: [],
    });

  const [artworks, setArtworks] =
    useState([]);

  const [loading, setLoading] =
    useState(!isNew);

  const [saving, setSaving] =
    useState(false);

  const [publishing, setPublishing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  async function loadEpisode() {
    if (!showId || isNew) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response =
        await apiRequest(
          `/episodes/${episodeId}`,
        );

      setEpisode(response);

      setForm({
        episode_id:
          response.episode_id ||
          "",
        season_id:
          String(
            response.season_id ||
              "",
          ),
        episode_number:
          String(
            response.episode_number ||
              "",
          ),
        title:
          response.title ||
          "",
        duration_seconds:
          response.duration_seconds ==
          null
            ? ""
            : String(
                response.duration_seconds,
              ),
        language:
          response.language ||
          "en",
        content_group:
          response.content_group ||
          "",
        categories:
          response.categories ||
          [],
      });

      const artworkResponse =
        await apiRequest(
          `/artworks/episode/${episodeId}`,
        );

      setArtworks(
        artworkResponse || [],
      );
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEpisode();
  }, [episodeId]);

  function updateField(
    field,
    value,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function toggleCategory(
    category,
  ) {
    setForm((current) => ({
      ...current,
      categories:
        current.categories.includes(
          category,
        )
          ? current.categories.filter(
              (item) =>
                item !==
                category,
            )
          : [
              ...current.categories,
              category,
            ],
    }));
  }

  async function saveEpisode(
    event,
  ) {
    event.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      if (!showId || isNew) {
      setLoading(false);
        const created =
          await apiRequest(
            "/episodes/",
            {
              method: "POST",
              body: JSON.stringify({
                episode_id:
                  form.episode_id,
                season_id:
                  Number(
                    form.season_id,
                  ),
                episode_number:
                  Number(
                    form.episode_number,
                  ),
                title:
                  form.title,
                duration_seconds:
                  form.duration_seconds
                    ? Number(
                        form.duration_seconds,
                      )
                    : null,
                language:
                  form.language,
                content_group:
                  form.content_group,
                status:
                  "draft",
                categories:
                  form.categories,
              }),
            },
          );

        navigate(
          `/episodes/${created.id}`,
        );

        return;
      }

      const updated =
        await apiRequest(
          `/episodes/${episodeId}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              episode_number:
                Number(
                  form.episode_number,
                ),
              title:
                form.title,
              duration_seconds:
                form.duration_seconds
                  ? Number(
                      form.duration_seconds,
                    )
                  : null,
              language:
                form.language,
              content_group:
                form.content_group,
              categories:
                form.categories,
            }),
          },
        );

      setEpisode(updated);

      const artworkResponse =
        await apiRequest(
          `/artworks/episode/${episodeId}`,
        );

      setArtworks(
        artworkResponse || [],
      );

      setSuccess(
        "Episode changes saved successfully.",
      );
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setSaving(false);
    }
  }

  async function publishEpisode() {
    setPublishing(true);
    setError("");
    setSuccess("");

    try {
      const updated =
        await apiRequest(
          `/episodes/${episodeId}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              status:
                "published",
            }),
          },
        );

      setEpisode(updated);

      setSuccess(
        "Episode published successfully.",
      );
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setPublishing(false);
    }
  }

  async function uploadArtwork(
    slot,
    file,
  ) {
    if (!file) {
      return;
    }

    setError("");
    setSuccess("");

    try {
      const body =
        new FormData();

      body.append(
        "episode_id",
        String(
          episode?.id ||
            episodeId,
        ),
      );

      body.append(
        "slot",
        slot,
      );

      body.append(
        "file",
        file,
      );

      await apiRequest(
        "/artworks/upload",
        {
          method: "POST",
          body,
        },
      );

      const artworkResponse =
        await apiRequest(
          `/artworks/episode/${
            episode?.id ||
            episodeId
          }`,
        );

      setArtworks(
        artworkResponse || [],
      );

      setSuccess(
        `${slot} artwork uploaded successfully.`,
      );
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    }
  }

  if (loading) {
    return (
      <div className="page">
        <LoadingState text="Loading episode..." />
      </div>
    );
  }

  if (
    error &&
    !episode &&
    !isNew
  ) {
    return (
      <div className="page">
        <ErrorState
          message={error}
          onRetry={loadEpisode}
        />
      </div>
    );
  }

  const isPublished =
    episode?.status ===
    "published";

  const artworkBySlot =
    Object.fromEntries(
      artworks.map((item) => [
        item.slot,
        item,
      ]),
    );

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button
            className="button button-small"
            onClick={() =>
              navigate(-1)
            }
          >
            ← Back
          </button>

          <h1
            style={{
              marginTop: 16,
            }}
          >
            {isNew
              ? "Create episode"
              : episode?.title ||
                "Episode"}
          </h1>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h2>
            Episode details
          </h2>

          {!isNew && (
            <StatusBadge
              status={
                episode?.status
              }
            />
          )}
        </div>

        <div className="card-body">
          {isPublished && (
            <div className="alert alert-info">
              This episode is published and cannot be edited directly.
            </div>
          )}

          {isNew && (
            <div className="alert alert-info">
              New episodes are created as drafts. Add artwork and complete the required fields before publishing.
            </div>
          )}

          <form
            onSubmit={
              saveEpisode
            }
          >
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="episode-id">
                  Episode ID
                </label>

                <input
                  id="episode-id"
                  className="input"
                  value={
                    form.episode_id
                  }
                  disabled={
                    isPublished ||
                    !isNew
                  }
                  onChange={(
                    event,
                  ) =>
                    updateField(
                      "episode_id",
                      event.target
                        .value,
                    )
                  }
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="season-id">
                  Season ID
                </label>

                <input
                  id="season-id"
                  className="input"
                  type="number"
                  min="1"
                  value={
                    form.season_id
                  }
                  disabled={
                    isPublished
                  }
                  onChange={(
                    event,
                  ) =>
                    updateField(
                      "season_id",
                      event.target
                        .value,
                    )
                  }
                  required
                />

                <div className="form-help">
                  The current backend does not yet expose a Seasons management endpoint, so this is the existing database season ID.
                </div>
              </div>

              <div className="form-field">
                <label htmlFor="episode-number">
                  Episode number
                </label>

                <input
                  id="episode-number"
                  className="input"
                  type="number"
                  min="1"
                  value={
                    form.episode_number
                  }
                  disabled={
                    isPublished
                  }
                  onChange={(
                    event,
                  ) =>
                    updateField(
                      "episode_number",
                      event.target
                        .value,
                    )
                  }
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="duration">
                  Duration (seconds)
                </label>

                <input
                  id="duration"
                  className="input"
                  type="number"
                  min="1"
                  value={
                    form.duration_seconds
                  }
                  disabled={
                    isPublished
                  }
                  onChange={(
                    event,
                  ) =>
                    updateField(
                      "duration_seconds",
                      event.target
                        .value,
                    )
                  }
                />

                <div className="form-help">
                  Optional for drafts. Required when publishing.
                </div>
              </div>

              <div className="form-field full">
                <label htmlFor="episode-title">
                  Title
                </label>

                <input
                  id="episode-title"
                  className="input"
                  value={
                    form.title
                  }
                  disabled={
                    isPublished
                  }
                  onChange={(
                    event,
                  ) =>
                    updateField(
                      "title",
                      event.target
                        .value,
                    )
                  }
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="language">
                  Language
                </label>

                <select
                  id="language"
                  className="select"
                  value={
                    form.language
                  }
                  disabled={
                    isPublished
                  }
                  onChange={(
                    event,
                  ) =>
                    updateField(
                      "language",
                      event.target
                        .value,
                    )
                  }
                >
                  {LANGUAGES.map(
                    (
                      language,
                    ) => (
                      <option
                        key={
                          language.value
                        }
                        value={
                          language.value
                        }
                      >
                        {
                          language.label
                        }
                      </option>
                    ),
                  )}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="content-group">
                  Content group
                </label>

                <input
                  id="content-group"
                  className="input"
                  value={
                    form.content_group
                  }
                  disabled={
                    isPublished
                  }
                  onChange={(
                    event,
                  ) =>
                    updateField(
                      "content_group",
                      event.target
                        .value,
                    )
                  }
                  required
                />

                <div className="form-help">
                  Same content group across languages becomes one catalogue episode.
                </div>
              </div>

              <div className="form-field full">
                <label>
                  Categories
                </label>

                <div
                  style={{
                    display:
                      "flex",
                    flexWrap:
                      "wrap",
                    gap: 8,
                  }}
                >
                  {CATEGORIES.map(
                    (
                      category,
                    ) => (
                      <label
                        key={
                          category
                        }
                        style={{
                          display:
                            "flex",
                          alignItems:
                            "center",
                          gap: 6,
                          padding:
                            "7px 10px",
                          border:
                            "1px solid #d5dae5",
                          borderRadius:
                            7,
                          fontSize:
                            12,
                          background:
                            form.categories.includes(
                              category,
                            )
                              ? "#eeeaff"
                              : "white",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={form.categories.includes(
                            category,
                          )}
                          disabled={
                            isPublished
                          }
                          onChange={() =>
                            toggleCategory(
                              category,
                            )
                          }
                        />

                        {category}
                      </label>
                    ),
                  )}
                </div>
              </div>
            </div>

            {!isPublished && (
              <div className="form-actions">
                <button
                  type="submit"
                  className="button button-primary"
                  disabled={
                    saving
                  }
                >
                  {saving
                    ? "Saving..."
                    : isNew
                      ? "Create draft"
                      : "Save changes"}
                </button>
              </div>
            )}
          </form>
        </div>
      </div>

      {!isNew && (
        <>
          <div
            className="card"
            style={{
              marginTop: 20,
            }}
          >
            <div className="card-header">
              <div>
                <h2>
                  Artwork
                </h2>

                <div className="table-secondary">
                  Required dimensions and 200 KB maximum are enforced by the backend.
                </div>
              </div>
            </div>

            <div className="card-body">
              <div className="artwork-grid">
                {ARTWORK_SLOTS.map(
                  (
                    definition,
                  ) => {
                    const artwork =
                      artworkBySlot[
                        definition.slot
                      ];

                    return (
                      <div
                        className="artwork-slot"
                        key={
                          definition.slot
                        }
                      >
                        <div className="artwork-preview">
                          {artwork ? (
                            <img
                              src={`${API_URL}/artworks/file/${encodeURIComponent(
                                artwork.object_key,
                              )}`}
                              alt={`${definition.label} artwork`}
                            />
                          ) : (
                            <div className="artwork-empty">
                              No{" "}
                              {definition.label.toLowerCase()}{" "}
                              uploaded
                            </div>
                          )}
                        </div>

                        <div className="artwork-info">
                          <strong>
                            {
                              definition.label
                            }
                          </strong>

                          <span>
                            Required:{" "}
                            {
                              definition.width
                            }
                            ×
                            {
                              definition.height
                            }
                          </span>

                          {artwork && (
                            <span>
                              Uploaded:{" "}
                              {
                                artwork.width
                              }
                              ×
                              {
                                artwork.height
                              }{" "}
                              ·{" "}
                              {Math.round(
                                artwork.size_bytes /
                                  1024,
                              )}{" "}
                              KB
                            </span>
                          )}

                          {!isPublished && (
                            <input
                              className="upload-input"
                              type="file"
                              accept="image/jpeg,image/png,image/webp"
                              onChange={(
                                event,
                              ) =>
                                uploadArtwork(
                                  definition.slot,
                                  event
                                    .target
                                    .files?.[0],
                                )
                              }
                            />
                          )}
                        </div>
                      </div>
                    );
                  },
                )}
              </div>
            </div>
          </div>

          <div
            className="publish-action"
            style={{
              marginTop: 20,
            }}
          >
            <h2>
              Editorial status
            </h2>

            <p>
              An episode must have valid
              duration and all three artwork
              slots before it can become
              published.
            </p>

            {isPublished ? (
              <StatusBadge
                status="published"
              />
            ) : (
              <button
                className="button button-success"
                onClick={
                  publishEpisode
                }
                disabled={
                  publishing
                }
              >
                {publishing
                  ? "Publishing..."
                  : "Mark episode as published"}
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function PublishPage() {
  const auth =
    getStoredAuth();

  const [report, setReport] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [publishing, setPublishing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  async function loadValidation() {
    setLoading(true);
    setError("");

    try {
      const response =
        await apiRequest(
          "/validation/report",
        );

      setReport(response);
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadValidation();
  }, []);

  async function publishCatalogue() {
    if (
      auth.role !== "admin"
    ) {
      setError(
        "Only an admin can publish the catalogue.",
      );

      return;
    }

    setPublishing(true);
    setError("");
    setSuccess("");

    try {
      const response =
        await apiRequest(
          "/publish",
          {
            method: "POST",
          },
        );

      if (!response.success) {
        setError(
          response.errors?.join(
            "\n",
          ) ||
            "Catalogue publication failed.",
        );

        return;
      }

      setSuccess(
        `Catalogue published successfully. ${
          response.published_show_count ||
          0
        } shows and ${
          response.published_episode_count ||
          0
        } episodes.`,
      );

      await loadValidation();
    } catch (requestError) {
      setError(
        formatError(requestError),
      );
    } finally {
      setPublishing(false);
    }
  }

  const errors =
    report?.errors || [];

  const valid =
    report?.valid === true;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>
            Publish catalogue
          </h1>

          <p>
            Validate published content before
            atomically updating the viewer
            catalogue.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="publish-layout">
        <div className="card">
          <div className="card-header">
            <h2>
              Validation report
            </h2>

            <button
              className="button button-small"
              onClick={
                loadValidation
              }
              disabled={
                loading
              }
            >
              Refresh
            </button>
          </div>

          <div className="card-body">
            {loading ? (
              <LoadingState text="Validating catalogue..." />
            ) : (
              <>
                <div
                  className={`validation-summary ${
                    valid
                      ? "validation-valid"
                      : "validation-invalid"
                  }`}
                >
                  <strong>
                    {valid
                      ? "Catalogue is ready to publish"
                      : `${
                          report?.error_count ||
                          errors.length
                        } validation error${
                          errors.length ===
                          1
                            ? ""
                            : "s"
                        }`}
                  </strong>
                </div>

                {valid ? (
                  <EmptyState
                    title="No validation errors"
                    message="All currently published content passed the catalogue validation checks."
                  />
                ) : (
                  <ul className="validation-list">
                    {errors.map(
                      (
                        item,
                        index,
                      ) => (
                        <li
                          className="validation-error"
                          key={
                            index
                          }
                        >
                          {item}
                        </li>
                      ),
                    )}
                  </ul>
                )}
              </>
            )}
          </div>
        </div>

        <div className="publish-action">
          <h2>
            Catalogue publication
          </h2>

          <p>
            Publishing replaces the live
            catalogue atomically. The viewer
            never receives a half-written JSON
            file.
          </p>

          {auth.role !==
            "admin" && (
            <div className="publish-warning">
              You are signed in as an editor.
              Catalogue publication requires the
              admin role.
            </div>
          )}

          {auth.role ===
            "admin" &&
            !valid && (
              <div className="publish-warning">
                Resolve all validation errors
                before publishing.
              </div>
            )}

          <button
            className="button button-primary"
            onClick={
              publishCatalogue
            }
            disabled={
              publishing ||
              loading ||
              !valid ||
              auth.role !==
                "admin"
            }
          >
            {publishing
              ? "Publishing catalogue..."
              : "Publish catalogue"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ProtectedApp() {
  const [auth, setAuth] =
    useState(
      getStoredAuth(),
    );

  function logout() {
    setStoredAuth(null);
    setAuth(null);
  }

  if (
    !auth?.access_token
  ) {
    return (
      <LoginPage
        onLogin={setAuth}
      />
    );
  }

  return (
    <Layout
      auth={auth}
      onLogout={logout}
    >
      <Routes>
        <Route
          path="/"
          element={
            <ShowsPage />
          }
        />

        <Route
          path="/shows"
          element={
            <ShowsPage />
          }
        />

        <Route
          path="/shows/new"
          element={
            <ShowFormPage />
          }
        />

        <Route
          path="/shows/:showId"
          element={
            <ShowFormPage />
          }
        />

        <Route
          path="/shows/:showId/episodes/new"
          element={
            <EpisodeFormPage />
          }
        />

        <Route
          path="/episodes/:episodeId"
          element={
            <EpisodeFormPage />
          }
        />

        <Route
          path="/publish"
          element={
            <PublishPage />
          }
        />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ProtectedApp />
    </BrowserRouter>
  );
}




