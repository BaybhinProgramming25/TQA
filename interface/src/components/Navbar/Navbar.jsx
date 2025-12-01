import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

import { Link } from 'react-router-dom';
import axios from 'axios'
import './Navbar.css'

const Navbar = () => {
    
    const { user, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const navigate = useNavigate();

    const logout_wrapper = async () => {
        try {
            await axios.post('http://localhost:3000/api/logout', user, { withCredentials: true });
            logout();
            setIsMenuOpen(false);
            navigate('/');
        }
        catch (error) {
            console.error('Error logging out', error);
            alert('Unable to logout')
        }
    }

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen);
    }

    const closeMenu = () => {
        setIsMenuOpen(false);
    }
        
    return (
        <div>
            <header className='top-grid'>
                <h1 className='tg-header'>TQA</h1>
                <div className='tg-contact'>+1 (800) TQA </div>
            </header>
            <header className='bottom-grid'>
                <nav className='middle-tabs'>
                    <button 
                        className={`hamburger-button ${isMenuOpen ? 'open' : ''}`}
                        onClick={toggleMenu}
                        aria-label="Toggle menu"
                    >
                        {isMenuOpen ? (
                            <span className="close-icon">✕</span>
                        ) : (
                            <>
                                <span></span>
                                <span></span>
                                <span></span>
                            </>
                        )}
                    </button>

                    <div className={`hamburger-content ${isMenuOpen ? 'show' : ''}`}>
                        {(user) && (
                            <>
                                <Link to="/logout" onClick={logout_wrapper}>Logout</Link>
                            </>
                        )}
                        {(!user) && (
                            <>
                                <Link to="/" onClick={closeMenu}>Home</Link>
                                <Link to="/contact" onClick={closeMenu}>Contact Us</Link>
                                <Link to="/login" onClick={closeMenu}>Login</Link>
                                <Link to="/signup" onClick={closeMenu}>Sign Up</Link>
                            </>
                        )}
                    </div>
                </nav>
            </header>
        </div>
    )
}
export default Navbar;