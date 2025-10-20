import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const createInitialState = () => ({
  summary: '',
  potential_causes: [],
  safety_checks: [],
  recommended_actions: [],
});

const toStringList = (value) => {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => (typeof item === 'string' ? item : String(item ?? '')).trim())
    .filter(Boolean);
};

const normaliseResult = (payload = {}) => ({
  summary: typeof payload.summary === 'string' ? payload.summary : '',
  potential_causes: toStringList(payload.potential_causes),
  safety_checks: toStringList(payload.safety_checks),
  recommended_actions: toStringList(payload.recommended_actions),
});

const readFileAsBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => {
      const { result } = reader;
      if (typeof result !== 'string') {
        reject(new Error('Failed to read selected file.'));
        return;
      }

      const commaIndex = result.indexOf(',');
      const base64 = commaIndex >= 0 ? result.slice(commaIndex + 1) : result;
      resolve({ media: base64, filename: file.name });
    };

    reader.onerror = () => {
      reject(reader.error ?? new Error('Failed to read selected file.'));
    };

    reader.readAsDataURL(file);
  });

function formatList(items) {
  if (!items?.length) return <p className="muted">No items returned.</p>;
  return (
    <ul>
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

function isVideoFile(file) {
  return file?.type.startsWith('video/');
}

export default function App() {
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(createInitialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : ''), [file]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setResult(createInitialState());

    try {
      if (!API_URL) {
        throw new Error('API URL is not configured. Set VITE_API_URL in your environment.');
      }

      const trimmedDescription = description.trim();
      if (!trimmedDescription) {
        throw new Error('Please describe the issue before submitting.');
      }

      let media = null;
      let filename = null;

      if (file) {
        ({ media, filename } = await readFileAsBase64(file));
      }

      const payload = {
        description: trimmedDescription,
        media,
        filename,
      };

      const { data } = await axios.post(API_URL, payload, {
        headers: { 'Content-Type': 'application/json' },
      });

      setResult(normaliseResult(data));
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.error ||
          err.message ||
          'Something went wrong. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header>
        <h1>Online Mechanic AI</h1>
        <span className="badge">Beta</span>
      </header>

      <section className="upload-card">
        <h2>Describe your issue</h2>
        <p>
          Upload a photo or short video of the problem and describe the sounds, warning
          lights, or symptoms you&apos;re experiencing.
        </p>

        <form className="upload-controls" onSubmit={handleSubmit}>
          <textarea
            placeholder="Example: There is a rattling noise when the engine is idling."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
          />

          <input
            type="file"
            accept="image/*,video/*"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />

          {previewUrl && (
            isVideoFile(file) ? (
              <video
                key={previewUrl}
                src={previewUrl}
                controls
                style={{ maxWidth: '100%', borderRadius: 12 }}
              />
            ) : (
              <img
                key={previewUrl}
                src={previewUrl}
                alt={file?.name || 'Uploaded media preview'}
                style={{ maxWidth: '100%', borderRadius: 12 }}
              />
            )
          )}

          <button type="submit" className="primary" disabled={loading}>
            {loading ? 'Analysing…' : 'Run Diagnostic'}
          </button>
        </form>

        {error && <p style={{ color: '#dc2626' }}>{error}</p>}
      </section>

      <section className="response-card">
        <h2>Diagnostic result</h2>
        <div className="result-section">
          <div>
            <h3>Summary</h3>
            <p>{result.summary || 'No summary available yet.'}</p>
          </div>

          <div>
            <h3>Potential causes</h3>
            {formatList(result.potential_causes)}
          </div>

          <div>
            <h3>Safety checks</h3>
            {formatList(result.safety_checks)}
          </div>

          <div>
            <h3>Recommended actions</h3>
            {formatList(result.recommended_actions)}
          </div>
        </div>
      </section>

      <footer>
        <p>Built with AWS Lambda, S3, and OpenAI GPT-4o Vision.</p>
      </footer>
    </div>
  );
}
