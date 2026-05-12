import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home-page">
      {/* Hero */}
      <section className="home-hero">
        <h1 className="home-hero-title">Your Transcript, Answered Instantly</h1>
        <p className="home-hero-sub">
          Transcript QA lets Stony Brook CS students upload their transcripts and ask any question
          about their academic records.
        </p>
        <div className="home-hero-ctas">
          <Link to="/signup" className="home-cta home-cta--primary">Get Started</Link>
          <Link to="/login" className="home-cta home-cta--secondary">Log In</Link>
        </div>
      </section>

      {/* Feature cards */}
      <section className="home-features">
        <div className="home-feature-card">
          <h2>Upload Your Transcript</h2>
          <p>
            Upload a PDF of your Stony Brook transcript and TQA will instantly parse
            and analyze it — no account linking required, just drag and drop.
          </p>
        </div>

        <div className="home-feature-card">
          <h2>Ask Natural Language Questions</h2>
          <p>
            Ask anything about your transcript in plain English — like "What's my GPA?",
            "How many credits do I have?", or "Did I pass all my major requirements?"
          </p>
        </div>

        <div className="home-feature-card">
          <h2>Export Your Transcript</h2>
          <p>
            Need a formatted copy? Just ask TQA to export your transcript and get a
            clean, shareable version generated on the spot.
          </p>
        </div>
      </section>

      {/* Sample transcript preview */}
      <section className="home-preview">
        <div className="home-preview-header">
          <h2 className="home-preview-title">What does a transcript look like?</h2>
          <p className="home-preview-desc">
            Here's a sample Stony Brook transcript so you know exactly what to upload.
          </p>
        </div>
        <div className="home-preview-frame-wrap">
          <iframe
            className="home-preview-frame"
            src="/sample.pdf"
            title="Sample transcript"
          />
        </div>
        <p className="home-preview-note">
          Note: this is not a one-to-one copy of real Stony Brook student transcripts but rather a relative approximation of what the structure looks like.
        </p>
      </section>
    </div>
  );
};

export default Home;
