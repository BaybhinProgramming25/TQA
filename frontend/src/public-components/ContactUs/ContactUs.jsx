import { useState } from 'react';
import axios from 'axios';

import './ContactUs.css';

const ContactUs = () => {

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    const data = { name, email, subject, message };

    try {
      await axios.post('/api/contact', data);
      alert('Thank you for contacting us! We will get back to you soon.');
    } catch (error) {
      console.log('Error sending information', error);
      alert('Unable to send message. Please try again later');
    }
  };

  return (
    <div className="contact-page">
      <div className="auth-card contact-card">
        <h1 className="auth-title">Contact Us</h1>
        <p className="auth-subtitle">Have a question? We'd love to hear from you.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label htmlFor="name">Your Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="subject">Subject</label>
            <input
              type="text"
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="What's this about?"
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="message">Message</label>
            <textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Tell us more..."
              rows="5"
              required
            />
          </div>

          <button type="submit" className="auth-submit">Send Message</button>
        </form>

        <div className="contact-info">
          <p>📞 +1 (800) TQA</p>
          <p>✉️ support@tqa.com</p>
        </div>
      </div>
    </div>
  );
};

export default ContactUs;
