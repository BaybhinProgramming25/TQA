import { useState, useRef, useEffect } from 'react';
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

  const handleSelectDoc = async (doc) => {
    setInputValue('');
    setSelectedDoc(doc);
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

    try {
      setMessages(prev => [...prev, userMessage]);
      setInputValue('');
      setIsLoading(true);

      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }

      const response = await api.post('/parse', formData);

      if (response.data.action === 'export') {
        const blob = await api.get(`/api/documents/${selectedDoc.id}/export`, { responseType: 'blob' });
        const url = URL.createObjectURL(blob.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = selectedDoc.filename.replace('.pdf', '.xlsx');
        a.click();
        URL.revokeObjectURL(url);
      }

      const aiMessage = {
        id: Date.now() + 1,
        text: response.data.message,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    } catch {
      const aiMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I am unable to answer that. Please try something else',
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
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

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-page">
      <Sidebar onSelectDoc={handleSelectDoc} selectedDoc={selectedDoc} />

      <div className="chat-main">

        {selectedDoc && (
          <div className="chat-doc-banner">
            <span>📄 {selectedDoc.filename}</span>
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
                  <p className="message-text">{message.text}</p>
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
    </div>
  );
};

export default Chat;
