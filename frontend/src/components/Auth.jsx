import { useState } from 'react';
import api from '../api';

export default function Auth({ onLoginSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(''); // Reset error message
        try {
            const response = await api.post('/auth/login', {
                email_phone: email,
                password: password
            });
            
            // Save token to localStorage
            localStorage.setItem('access_token', response.data.access_token);
            
            // Notify parent component to update UI
            onLoginSuccess();
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
        }
    };

    return (
        <div style={{ maxWidth: '300px', margin: '50px auto' }}>
            <h2>Welcome Back</h2>
            {error && <p style={{ color: 'red', fontSize: '14px' }}>{error}</p>}
            <form onSubmit={handleLogin}>
                <input 
                    type="text" 
                    placeholder="Email or Phone" 
                    value={email} 
                    onChange={(e) => setEmail(e.target.value)} 
                    required 
                />
                <input 
                    type="password" 
                    placeholder="Password" 
                    value={password} 
                    onChange={(e) => setPassword(e.target.value)} 
                    required 
                />
                <button type="submit" style={{ width: '100%' }}>Login</button>
            </form>
        </div>
    );
}