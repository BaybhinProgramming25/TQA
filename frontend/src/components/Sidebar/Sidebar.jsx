import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import './Sidebar.css';

const Sidebar = ({ onNewChat }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await axios.post('/api/logout', user, { withCredentials: true });
      logout();
      navigate('/');
    } catch (error) {
      console.error('Error logging out', error);
      alert('Unable to logout');
    }
  };

  const initials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : 'U';

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-logo">
          <span className="sidebar-logo-icon">T</span>
          <span className="sidebar-logo-text">TQA</span>
        </div>
        <button className="sidebar-new-chat" onClick={onNewChat}>
          <span className="sidebar-new-chat-icon">+</span>
          New Chat
        </button>
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <span className="sidebar-username">{user?.username ?? 'User'}</span>
        </div>
        <button className="sidebar-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
