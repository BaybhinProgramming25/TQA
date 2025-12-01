import { useState, useRef } from 'react';
import axios from 'axios';

import './Chat.css';

const Chat = () => {

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const fileInputRef = useRef(null);

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

    const formData = new FormData()
    formData.append('message', inputValue)

    if (uploadedFiles.length > 0) {
      formData.append('file', uploadedFiles[0].file)
    }

    try {

      setMessages(prev => [...prev, userMessage]);
      setInputValue('');
      setIsLoading(true);

      const response = await axios.post('http://localhost:3000/parse', formData, { withCredentials: true });
 
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
    }
    catch {

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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>TQA Chat</h2>
        <p>Ask me anything about your transcript!</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Upload your transcript and start asking questions!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}
            >
              <div className="message-content">
                <p>{message.text}</p>
                {message.files && (
                  <div className="message-files">
                    {message.files.map(file => (
                      <div key={file.id} className="message-file-tag">
                        📄 {file.name}
                      </div>
                    ))}
                  </div>
                )}
                <span className="message-time">{message.timestamp}</span>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message ai-message">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-container">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />

        <button
          className="plus-button"
          onClick={handlePlusClick}
          aria-label="Upload file"
          title="Upload PDF transcript"
        >
          +
        </button>

        <div className="input-wrapper">
          {uploadedFiles.length > 0 && (
            <div className="attached-files">
              {uploadedFiles.map(file => (
                <div key={file.id} className="attached-file-chip">
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

          <textarea
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question here..."
            rows="1"
          />
        </div>

        <button
          className="send-button"
          onClick={handleSendMessage}
          disabled={isLoading || (inputValue.trim() === '' && uploadedFiles.length === 0)}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;