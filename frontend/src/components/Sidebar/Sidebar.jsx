import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/index.js';
import './Sidebar.css';

const Sidebar = ({ onSelectDoc, selectedDoc }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [documents, setDocuments] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/api/documents');
      setDocuments(response.data);
    } catch {
      // silently fail — user may not have any docs yet
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploadProgress(0);
    try {
      const response = await api.post('/api/documents', formData, {
        onUploadProgress: (event) => {
          setUploadProgress(Math.round((event.loaded / event.total) * 100));
        },
      });
      setDocuments(prev => [...prev, response.data]);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setUploadProgress(null);
      e.target.value = '';
    }
  };

  const handleExport = async (docId, filename) => {
    try {
      const response = await api.get(`/api/documents/${docId}/export`, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename.replace('.pdf', '.xlsx');
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Failed to export document.');
    }
  };

  const handleDelete = async (docId) => {
    try {
      await api.delete(`/api/documents/${docId}`);
      setDocuments(prev => prev.filter(d => d.id !== docId));
      if (selectedDoc?.id === docId) onSelectDoc(null);
    } catch {
      alert('Failed to delete document.');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const displayName = user?.firstname
    ? `${user.firstname} ${user.lastname ?? ''}`.trim()
    : user?.email ?? 'User';

  const initials = user?.firstname
    ? `${user.firstname[0]}${user.lastname?.[0] ?? ''}`.toUpperCase()
    : (user?.email?.[0] ?? 'U').toUpperCase();

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-logo">
          <span className="sidebar-logo-icon">T</span>
          <span className="sidebar-logo-text">TQA</span>
        </div>
      </div>

      <div className="sidebar-documents">
        <div className="sidebar-documents-header">
          <span className="sidebar-documents-title">Documents</span>
          <button
            className="sidebar-upload-btn"
            onClick={() => fileInputRef.current.click()}
            disabled={uploadProgress !== null}
            title="Upload PDF"
          >
            + Upload
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
        </div>

        {uploadProgress !== null && (
          <div className="sidebar-upload-progress">
            <div className="sidebar-upload-progress-bar" style={{ width: `${uploadProgress}%` }} />
            <span className="sidebar-upload-progress-label">
              {uploadProgress < 100 ? `Uploading… ${uploadProgress}%` : 'Processing…'}
            </span>
          </div>
        )}

        <ul className="sidebar-documents-list">
          {documents.length === 0 && (
            <li className="sidebar-documents-empty">No documents yet</li>
          )}
          {documents.map(doc => (
            <li
              key={doc.id}
              className={`sidebar-document-item ${selectedDoc?.id === doc.id ? 'sidebar-document-item--active' : ''}`}
              onClick={() => onSelectDoc(doc)}
            >
              <span className="sidebar-document-name" title={doc.filename}>
                {doc.filename}
              </span>
              <button
                className="sidebar-document-export"
                onClick={(e) => { e.stopPropagation(); handleExport(doc.id, doc.filename); }}
                title="Export to Excel"
              >
                ↓
              </button>
              <button
                className="sidebar-document-delete"
                onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }}
                title="Delete"
              >
                x
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <span className="sidebar-username">{displayName}</span>
        </div>
        <button className="sidebar-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
