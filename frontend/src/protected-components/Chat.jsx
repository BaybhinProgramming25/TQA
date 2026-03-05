import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

import Sidebar from '../components/Sidebar/Sidebar';
import './Chat.css';

const Chat = () => {

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleNewChat = () => {
    setMessages([]);
    setInputValue('');
    setUploadedFiles([]);
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');

    if (pdfFiles.length !== files.length) {
      alert('Only PDF files are allowed!');
    }

    const newFiles = pdfFiles.map(file => ({
      id: Date.now() + Math.random(),
      file: file,
      name: file.name,
      size: (file.size / 1024).toFixed(2)
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const handleRemoveFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const handlePlusClick = () => {
    fileInputRef.current.click();
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() === '' && uploadedFiles.length === 0) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue || '📎 Uploaded file(s)',
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      files: uploadedFiles.length > 0 ? uploadedFiles : null
    };

    const formData = new FormData();
    formData.append('message', inputValue);

    if (uploadedFiles.length > 0) {
      formData.append('file', uploadedFiles[0].file);
    }

    try {
      setMessages(prev => [...prev, userMessage]);
      setInputValue('');
      setUploadedFiles([]);
      setIsLoading(true);

      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }

      const response = await axios.post('/parse', formData, { withCredentials: true });

      setTimeout(() => {
        const aiMessage = {
          id: Date.now() + 1,
          text: response.data.message,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, aiMessage]);
        setIsLoading(false);
      }, 1000);
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
      <Sidebar onNewChat={handleNewChat} />

      <div className="chat-main">
        <div className="chat-messages">
          {isEmpty ? (
            <div className="chat-empty">
              <div className="chat-empty-icon">T</div>
              <h2 className="chat-empty-title">TQA</h2>
              <p className="chat-empty-desc">
                Upload your transcript and ask anything about your academic records.
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
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            multiple
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />

          <div className="chat-input-box">
            {uploadedFiles.length > 0 && (
              <div className="chat-file-chips">
                {uploadedFiles.map(file => (
                  <div key={file.id} className="file-chip">
                    <span className="file-chip-name">📄 {file.name}</span>
                    <button
                      className="file-chip-remove"
                      onClick={() => handleRemoveFile(file.id)}
                      aria-label="Remove file"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="chat-input-row">
              <button
                className="input-attach-btn"
                onClick={handlePlusClick}
                aria-label="Upload PDF"
                title="Upload PDF transcript"
              >
                📎
              </button>

              <textarea
                ref={textareaRef}
                className="chat-textarea"
                value={inputValue}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your transcript..."
                rows="1"
              />

              <button
                className="input-send-btn"
                onClick={handleSendMessage}
                disabled={isLoading || (inputValue.trim() === '' && uploadedFiles.length === 0)}
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
