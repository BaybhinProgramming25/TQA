import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home-page">
      {/* Hero */}
      <section className="home-hero">
        <h1 className="home-hero-title">Your transcript, answered instantly</h1>
        <p className="home-hero-sub">
          TQA lets Stony Brook CS students upload their transcripts and ask any question
          about their academic records — powered by AI.
        </p>
        <div className="home-hero-ctas">
          <Link to="/signup" className="home-cta home-cta--primary">Get Started</Link>
          <Link to="/login" className="home-cta home-cta--secondary">Log In</Link>
        </div>
      </section>

      {/* Feature cards */}
      <section className="home-features">
        <div className="home-feature-card">
          <div className="home-feature-icon">📄</div>
          <h2>Upload Your Transcript</h2>
          <p>
            Drop your Stony Brook CS transcript PDF into the chat. TQA parses it
            in-memory instantly — no files stored on disk, keeping your data private.
          </p>
        </div>

        <div className="home-feature-card">
          <div className="home-feature-icon">💬</div>
          <h2>Ask Anything</h2>
          <p>
            Ask natural-language questions like "What's my GPA?", "How many credits
            do I have?", or "What did I take in Fall 2023?" and get instant answers.
          </p>
        </div>

        <div className="home-feature-card">
          <div className="home-feature-icon">🔒</div>
          <h2>Private by Design</h2>
          <p>
            Your transcript data is never written to disk. Everything is processed
            in-memory and discarded when your session ends.
          </p>
        </div>
      </section>
    </div>
  );
};

export default Home;
