import { useState } from 'react';
import api from '../api';
import './AuthForms.css';

export default function Auth({ onLoginSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await api.post('/auth/login', {
                email_phone: email,
                password,
            });

            localStorage.setItem('access_token', response.data.access_token);
            onLoginSuccess();
        } catch (err) {
            const message = err.response?.data?.detail;
            setError(
                typeof message === 'string'
                    ? message
                    : 'Login failed. Please check your credentials.'
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <section className="auth-card" aria-label="Login form">
                <p className="auth-eyebrow">Dermatology AI Platform</p>
                <h2 className="auth-title">Welcome back</h2>
                <p className="auth-subtitle">
                Sign in to access AI-powered diagnosis, treatment insights, and your medical dashboard.
                </p>

                {error && <p className="auth-alert error">{error}</p>}

                <form onSubmit={handleLogin} className="auth-form">
                    <label className="field-label" htmlFor="login-email-phone">
                        Email or phone
                    </label>
                    <input
                        id="login-email-phone"
                        className="field-input"
                        type="text"
                        placeholder="example@hospital.vn"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="username"
                        required
                    />

                    <label className="field-label" htmlFor="login-password">
                        Password
                    </label>
                    <input
                        id="login-password"
                        className="field-input"
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                        required
                    />

                    <button type="submit" className="primary-btn" disabled={loading}>
                        {loading ? 'Signing in...' : 'Login'}
                    </button>
                </form>
            </section>
        </div>
    );
}