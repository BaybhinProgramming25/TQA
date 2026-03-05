import { Link } from 'react-router-dom';
import './VerifyEmailSent.css';

const EmailSent = () => {
  return (
    <div className="auth-page">
      <div className="auth-card verify-card">
        <div className="auth-logo">
          <span className="auth-logo-icon">T</span>
          <span className="auth-logo-text">TQA</span>
        </div>

        <h1 className="auth-title">Check your email</h1>
        <p className="auth-subtitle">We've sent a verification link to your inbox</p>

        <ol className="verify-steps">
          <li>
            <strong>Open Mailhog</strong> and find our verification message
          </li>
          <li>
            <strong>Click the verification link</strong> in the email to activate your account
          </li>
          <li>
            <strong>You'll be redirected</strong> back to TQA with your account activated
          </li>
        </ol>

        <p className="verify-note">
          Don't see the email? Check your spam folder.
        </p>

        <p className="auth-switch">
          Having trouble? <Link to="/contact">Contact support</Link>
        </p>
      </div>
    </div>
  );
};

export default EmailSent;
