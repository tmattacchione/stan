import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { contentSeriesApi, postsApi } from "../api/client";
import { format } from "date-fns";

export default function SeriesDetail() {
  const { id } = useParams();

  const [series, setSeries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Form state for adding a new post
  const [availablePosts, setAvailablePosts] = useState([]);
  const [selectedPostId, setSelectedPostId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [position, setPosition] = useState(1);
  const [adding, setAdding] = useState(false);

  const fetchSeries = async () => {
    try {
      const data = await contentSeriesApi.get(id);
      setSeries(data);
      // Auto-set next position
      setPosition((data.posts?.length || 0) + 1);
    } catch (err) {
      setError("Failed to load series details");
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailablePosts = async () => {
    try {
      const allPosts = await postsApi.list();
      const existingIds = new Set(series?.posts?.map((p) => p.post_id) || []);
      const filtered = allPosts.filter((p) => !existingIds.has(p.id));
      setAvailablePosts(filtered);
    } catch (err) {
      console.error("Failed to fetch available posts", err);
    }
  };

  useEffect(() => {
    fetchSeries();
  }, [id]);

  useEffect(() => {
    if (series) {
      fetchAvailablePosts();
    }
  }, [series]);

  const handleAddPost = async (e) => {
    e.preventDefault();
    if (!selectedPostId || !scheduledAt) {
      setError("Please select a post and a scheduled time");
      return;
    }

    setAdding(true);
    setError("");
    setSuccess("");

    try {
      await contentSeriesApi.addPost(id, {
        post_id: parseInt(selectedPostId),
        position: parseInt(position),
        scheduled_at: new Date(scheduledAt).toISOString(),
      });

      setSuccess("Post successfully added to series!");
      setSelectedPostId("");
      setScheduledAt("");

      // Refresh the series data
      await fetchSeries();
    } catch (err) {
      setError(err.message || "Failed to add post to series");
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <div className="loading">Loading series details...</div>;
  if (!series) return <div className="error">Series not found</div>;

  return (
    <div className="series-detail-page">
      <div className="page-header">
        <div>
          <h1>{series.name}</h1>
          {series.root_scheduled_at && (
            <p className="calendar-hint">
              Root scheduled: {format(new Date(series.root_scheduled_at), "MMM d, yyyy HH:mm")}
            </p>
          )}
        </div>
        <Link to="/series" className="btn">
          ← Back to Series
        </Link>
      </div>

      {error && <div className="error">{error}</div>}
      {success && (
        <div style={{ background: "#d1fae5", color: "#065f46", padding: "0.75rem", borderRadius: "6px", marginBottom: "1.5rem" }}>
          {success}
        </div>
      )}

      {/* Add Post Form */}
      <div className="post-form" style={{ marginBottom: "2.5rem" }}>
        <h2 style={{ marginTop: 0 }}>Add Post to Series</h2>
        <form onSubmit={handleAddPost}>
          <label>
            Select Post
            <select
              value={selectedPostId}
              onChange={(e) => setSelectedPostId(e.target.value)}
              required
            >
              <option value="">— Choose a post —</option>
              {availablePosts.length === 0 ? (
                <option disabled>No posts available to add</option>
              ) : (
                availablePosts.map((post) => (
                  <option key={post.id} value={post.id}>
                    {post.title} — {post.platform}
                  </option>
                ))
              )}
            </select>
          </label>

          <label>
            Scheduled At
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              required
            />
          </label>

          <label>
            Position in Series
            <input
              type="number"
              value={position}
              onChange={(e) => setPosition(Math.max(1, parseInt(e.target.value) || 1))}
              min="1"
              required
            />
          </label>

          <div className="form-actions">
            <button
              type="submit"
              disabled={adding || !selectedPostId || !scheduledAt}
              className="btn primary"
            >
              {adding ? "Adding Post..." : "Add Post to Series"}
            </button>
          </div>
        </form>
      </div>

      {/* Posts in this Series - Improved Display */}
      <h2>Posts in Series ({series.posts?.length || 0})</h2>

      <div className="table-wrap">
        <table className="posts-table">
          <thead>
            <tr>
              <th style={{ width: "80px" }}>Position</th>
              <th>Title</th>
              <th>Platform</th>
              <th>Scheduled At</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {series.posts && series.posts.length > 0 ? (
              series.posts
                .sort((a, b) => a.position - b.position)
                .map((entry) => {
                  const post = entry.post || {};
                  return (
                    <tr key={entry.id}>
                      <td><strong>{entry.position}</strong></td>
                      <td>{post.title || "Untitled Post"}</td>
                      <td>
                        <span className="platform">{post.platform || "—"}</span>
                      </td>
                      <td>
                        {entry.scheduled_at ? (
                          format(new Date(entry.scheduled_at), "MMM d, yyyy HH:mm")
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        <span className={`status status-${post.status || "draft"}`}>
                          {post.status || "draft"}
                        </span>
                      </td>
                    </tr>
                  );
                })
            ) : (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", padding: "2rem" }}>
                  No posts added to this series yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
