import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import api from '../api/index.js';

import Sidebar from '../components/Sidebar/Sidebar';
import './Chat.css';

const Chat = () => {

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async () => {
    if (inputValue.trim() === '' || !selectedDoc) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
    };

    const formData = new FormData();
    formData.append('message', inputValue);
    formData.append('document_id', selectedDoc.id);

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const response = await fetch('/parse', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Request failed');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      const aiMessageId = Date.now() + 1;
      let buffer = '';
      let streamStarted = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (raw === '[DONE]') continue;

          try {
            const parsed = JSON.parse(raw);

            if (parsed.sources !== undefined) {
              streamStarted = true;
              setIsLoading(false);
              setMessages(prev => [...prev, {
                id: aiMessageId,
                text: '',
                sender: 'ai',
                timestamp: new Date().toLocaleTimeString(),
                sources: parsed.sources,
              }]);
            } else if (parsed.error) {
              setIsLoading(false);
              setMessages(prev => [...prev, {
                id: aiMessageId,
                text: 'Sorry, I am unable to answer that. Please try something else',
                sender: 'ai',
                timestamp: new Date().toLocaleTimeString(),
                sources: [],
              }]);
            } else if (parsed.token !== undefined) {
              if (!streamStarted) {
                streamStarted = true;
                setIsLoading(false);
                setMessages(prev => [...prev, {
                  id: aiMessageId,
                  text: parsed.token,
                  sender: 'ai',
                  timestamp: new Date().toLocaleTimeString(),
                  sources: [],
                }]);
              } else {
                setMessages(prev => prev.map(m =>
                  m.id === aiMessageId ? { ...m, text: m.text + parsed.token } : m
                ));
              }
            }
          } catch {
            // ignore malformed events
          }
        }
      }
    } catch {
      setIsLoading(false);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: 'Sorry, I am unable to answer that. Please try something else',
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
      }]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTextareaChange = (e) => {
    setInputValue(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  const handleClearChat = async () => {
    if (!selectedDoc) return;
    try {
      await api.delete(`/api/messages/${selectedDoc.id}`);
      setMessages([]);
    } catch {
      // silently fail
    }
  };

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pdfOpen, setPdfOpen] = useState(true);
  const isEmpty = messages.length === 0;

  const handleSelectDoc = async (doc) => {
    setSidebarOpen(false);
    setInputValue('');
    setSelectedDoc(doc);
    setPdfOpen(true);
    if (!doc) { setMessages([]); return; }
    try {
      const response = await api.get(`/api/messages/${doc.id}`);
      setMessages(response.data.map(m => ({
        id: m.id,
        text: m.text,
        sender: m.sender,
        timestamp: new Date(m.created_at).toLocaleTimeString(),
      })));
    } catch {
      setMessages([]);
    }
  };

  return (
    <div className="chat-page">
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <Sidebar
        onSelectDoc={handleSelectDoc}
        selectedDoc={selectedDoc}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="chat-main">

        <div className="chat-mobile-header">
          <button
            className="chat-menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            ☰
          </button>
          <span className="chat-mobile-title">
            {selectedDoc ? `📄 ${selectedDoc.filename}` : 'TQA'}
          </span>
        </div>

        {selectedDoc && (
          <div className="chat-doc-banner chat-doc-banner--desktop">
            <span>📄 {selectedDoc.filename}</span>
            <div className="chat-doc-banner-actions">
              <button className="chat-doc-banner-toggle" onClick={() => setPdfOpen(o => !o)}>
                {pdfOpen ? 'Hide PDF' : 'Show PDF'}
              </button>
              <button className="chat-doc-banner-close" onClick={handleClearChat}>
                Clear chat
              </button>
            </div>
          </div>
        )}

        <div className="chat-messages">
          {isEmpty ? (
            <div className="chat-empty">
              <div className="chat-empty-icon">T</div>
              <h2 className="chat-empty-title">TQA</h2>
              <p className="chat-empty-desc">
                {selectedDoc
                  ? `Ask anything about ${selectedDoc.filename}`
                  : 'Upload your transcript and ask anything about your academic records.'}
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`message-row message-row--${message.sender === 'user' ? 'user' : 'ai'}`}
              >
                {message.sender === 'ai' && (
                  <div className="message-avatar">T</div>
                )}
                <div className="message-bubble">
                  <div className="message-text"><ReactMarkdown>{message.text}</ReactMarkdown></div>
                  {message.files && (
                    <div className="message-files">
                      {message.files.map(file => (
                        <span key={file.id} className="message-file-tag">
                          📄 {file.name}
                        </span>
                      ))}
                    </div>
                  )}
                  <span className="message-time">{message.timestamp}</span>
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="message-row message-row--ai">
              <div className="message-avatar">T</div>
              <div className="message-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <div className="chat-input-box">
            <div className="chat-input-row">
              <textarea
                ref={textareaRef}
                className="chat-textarea"
                value={inputValue}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder={selectedDoc ? `Ask about ${selectedDoc.filename}...` : 'Ask about your transcript...'}
                rows="1"
              />

              <button
                className="input-send-btn"
                onClick={handleSendMessage}
                disabled={isLoading || inputValue.trim() === '' || !selectedDoc}
                aria-label="Send message"
              >
                ↑
              </button>
            </div>
          </div>

          <p className="chat-input-hint">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
      {pdfOpen && selectedDoc && (
        <div className="pdf-panel">
          <div className="pdf-panel-header">
            <span title={selectedDoc.filename}>📄 {selectedDoc.filename}</span>
            <button className="pdf-panel-close" onClick={() => setPdfOpen(false)}>✕</button>
          </div>
          <iframe
            key={selectedDoc.id}
            className="pdf-panel-frame"
            src={`/api/documents/${selectedDoc.id}/file`}
            title={selectedDoc.filename}
          />
        </div>
      )}
    </div>
  );
};

export default Chat;
