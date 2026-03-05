import { Link } from 'react-router-dom';
import './PublicLayout.css';

const PublicLayout = ({ children }) => {
  return (
    <div className="public-layout">
      <header className="public-nav">
        <Link to="/" className="public-nav-logo">
          <span className="public-nav-logo-icon">T</span>
          <span className="public-nav-logo-text">TQA</span>
        </Link>
        <nav className="public-nav-links">
          <Link to="/contact">Contact</Link>
          <Link to="/login">Login</Link>
          <Link to="/signup" className="public-nav-signup">Sign Up</Link>
        </nav>
      </header>
      <main className="public-main">
        {children}
      </main>
    </div>
  );
};

export default PublicLayout;
