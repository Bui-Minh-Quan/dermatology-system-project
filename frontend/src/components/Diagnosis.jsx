import { useEffect, useMemo, useState } from "react";
import api from "../api";
import "./Diagnosis.css";

const BODY_PARTS = [
  { label: "Face / Neck", index: 0 },
  { label: "Back / Abdomen", index: 1 },
  { label: "Upper Body", index: 2 },
  { label: "Lower Body", index: 3 },
  { label: "Genitals", index: 4 },
  { label: "Palms / Soles", index: 5 },
  { label: "Scalp", index: 6 },
  { label: "Unspecified", index: 7 },
];

export default function Diagnosis() {
  const [file, setFile] = useState(null);
  const [symptoms, setSymptoms] = useState("");
  const [vector, setVector] = useState(new Array(8).fill(0));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const previewUrl = useMemo(() => {
    if (!file) return "";
    return URL.createObjectURL(file);
  }, [file]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const selectedCount = vector.reduce((sum, item) => sum + item, 0);

  const toAssetUrl = (path) => {
    if (!path) return "";
    if (path.startsWith("http://") || path.startsWith("https://")) {
      return path;
    }
    const base = api.defaults.baseURL || "";
    return `${base}${path}`;
  };

  const togglePart = (index) => {
    const updated = [...vector];
    updated[index] = updated[index] ? 0 : 1;
    setVector(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError("Please select an image before running analysis.");
      return;
    }

    const formData = new FormData();
    formData.append("image", file);
    formData.append("symptoms", symptoms);
    formData.append("body_vector", JSON.stringify(vector));

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await api.post("/diagnosis/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setResult(response.data);
    } catch (error) {
      console.error(error);
      const message = error?.response?.data?.detail || "Diagnosis failed. Please try again.";
      setError(typeof message === "string" ? message : "Diagnosis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    setError("");
  };

  return (
    <div className="diagnosis-page">
      <div className="diagnosis-card">
        <header className="card-header">
          <p className="eyebrow">AI Dermatology Assistant</p>
          <h1 className="main-title">Skin Condition Diagnosis from Clinical Images</h1>
          <p className="subtitle">
            Upload an image, describe symptoms, and choose affected areas to receive AI analysis.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="diagnosis-form">
          <div className="form-section upload-box">
            <div className="section-head">
              <h2 className="section-title">1) Clinical Image</h2>
              <span className="section-tip">PNG, JPG, WEBP</span>
            </div>

            <label className="file-picker" htmlFor="diagnosis-image-input">
              <span className="picker-title">Choose image from your device</span>
              <span className="picker-subtitle">
                Use a sharp, well-lit image focused on the affected skin area for the best analysis quality.
              </span>
            </label>
            <input
              id="diagnosis-image-input"
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="file-input"
            />

            {previewUrl ? (
              <img src={previewUrl} alt="Uploaded image preview" className="preview-image" />
            ) : (
              <div className="preview-placeholder">No image selected yet</div>
            )}
          </div>

          <div className="form-section">
            <div className="section-head">
              <h2 className="section-title">2) Symptom Description</h2>
            </div>
            <textarea
              className="symptoms-input"
              placeholder="Example: severe night itching, flaky skin, redness, burning sensation..."
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              rows={4}
            />
          </div>

          <div className="form-section">
            <div className="section-head">
              <h2 className="section-title">3) Affected Areas</h2>
              <span className="section-tip">Selected: {selectedCount}</span>
            </div>
            <div className="body-grid">
              {BODY_PARTS.map((part) => (
                <button
                  key={part.index}
                  type="button"
                  className={`part-btn ${vector[part.index] ? "active" : ""}`}
                  onClick={() => togglePart(part.index)}
                >
                  {part.label}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="error-text">{error}</p>}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Now"}
          </button>
        </form>

        {result && (
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Prediction Result</p>
              <h2 className="disease-name">{result.predicted_disease || "Updating..."}</h2>
            </div>

            <div className="confidence-wrapper">
              <div
                className="confidence-bar"
                style={{ width: `${(result.confidence_score || 0) * 100}%` }}
              />
            </div>

            <p className="confidence-text">
              Confidence: <strong>{((result.confidence_score || 0) * 100).toFixed(2)}%</strong>
            </p>

            <div className="images-container">
              <div className="image-box original">
                <h3>Original Image</h3>
                {result.input_image_url ? (
                  <img
                    src={toAssetUrl(result.input_image_url)}
                    alt="Original"
                    className="result-img"
                  />
                ) : (
                  <div className="image-fallback">Original image not found</div>
                )}
              </div>

              <div className="image-box heatmap">
                <h3>Heatmap AI</h3>
                {result.heatmap_url ? (
                  <img
                    src={toAssetUrl(result.heatmap_url)}
                    alt="Heatmap"
                    className="result-img"
                  />
                ) : (
                  <div className="image-fallback">No heatmap available yet</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}