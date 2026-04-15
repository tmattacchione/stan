import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { contentSeriesApi } from "../api/client";
import { format } from "date-fns";

export default function ContentSeriesList() {
  const [seriesList, setSeriesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    root_scheduled_at: "",
  });
  const [creating, setCreating] = useState(false);

  const fetchSeries = async () => {
    try {
      const data = await contentSeriesApi.list();
      setSeriesList(data);
    } catch (err) {
      setError("Failed to load series");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSeries();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.root_scheduled_at) return;

    setCreating(true);
    setError("");

    try {
      await contentSeriesApi.create({
        name: formData.name,
        root_scheduled_at: new Date(formData.root_scheduled_at).toISOString(),
      });

      setFormData({ name: "", root_scheduled_at: "" });
      setShowForm(false);
      fetchSeries(); // refresh list
    } catch (err) {
      setError(err.message || "Failed to create series");
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div className="loading">Loading series...</div>;

  return (
    <div className="content-series-page">
      <div className="page-header">
        <h1>Content Series</h1>
        <button
          className="btn primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "New Series"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Create Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="post-form" style={{ marginBottom: "2rem" }}>
          <label>
            Series Name
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(f => ({ ...f, name: e.target.value }))}
              placeholder="Weekly Instagram Reels"
              required
            />
          </label>

          <label>
            Root Scheduled At
            <input
              type="datetime-local"
              value={formData.root_scheduled_at}
              onChange={(e) => setFormData(f => ({ ...f, root_scheduled_at: e.target.value }))}
              required
            />
          </label>

          <div className="form-actions">
            <button
              type="submit"
              disabled={creating}
              className="btn primary"
            >
              {creating ? "Creating..." : "Create Series"}
            </button>
          </div>
        </form>
      )}

      {/* Series List */}
      <div className="table-wrap">
        <table className="posts-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Root Scheduled At</th>
              <th>Posts Count</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {seriesList.length === 0 ? (
              <tr>
                <td colSpan={4}>No series yet. Create one above.</td>
              </tr>
            ) : (
              seriesList.map((series) => (
                <tr key={series.id}>
                  <td>{series.name}</td>
                  <td>
                    {series.root_scheduled_at
                      ? format(new Date(series.root_scheduled_at), "MMM d, yyyy HH:mm")
                      : "—"}
                  </td>
                  <td>{series.posts?.length || 0}</td>
                  <td>
                    <Link to={`/series/${series.id}`} className="btn small">
                      View / Add Posts
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
