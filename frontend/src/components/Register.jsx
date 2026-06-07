import { useState } from 'react';
import api from '../api';
import './AuthForms.css';

export default function Register({ onSwitchToLogin }) {
    const [role, setRole] = useState('patient');
    const [formData, setFormData] = useState({
        email_phone: '',
        password: '',
        full_name: '',
        otp_code: 'string',
        date_of_birth: '2005-01-01',
        gender: 'MALE',
        address: 'Hanoi',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleChange = (field, value) => {
        setFormData((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        const endpoint = role === 'patient' ? '/auth/register/patient' : '/auth/register/doctor';

        try {
            await api.post(endpoint, formData);
            setSuccess('Registration successful. Redirecting to login...');
            setTimeout(() => {
                onSwitchToLogin();
            }, 700);
        } catch (err) {
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                setError(detail);
            } else {
                setError('Registration failed. Please verify your information and try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <section className="auth-card" aria-label="Register form">
                <p className="auth-eyebrow">Dermatology AI Platform</p>
                <h2 className="auth-title">Create account</h2>
                <p className="auth-subtitle">
                    Register to start AI-assisted dermatology workflows with secure access.
                </p>

                <div className="role-switch" role="group" aria-label="Select role">
                    <button
                        type="button"
                        className={`role-btn ${role === 'patient' ? 'active' : ''}`}
                        onClick={() => setRole('patient')}
                    >
                        Patient
                    </button>
                    <button
                        type="button"
                        className={`role-btn ${role === 'doctor' ? 'active' : ''}`}
                        onClick={() => setRole('doctor')}
                    >
                        Doctor
                    </button>
                </div>

                {error && <p className="auth-alert error">{error}</p>}
                {success && <p className="auth-alert success">{success}</p>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <label className="field-label" htmlFor="register-email-phone">
                        Email or phone
                    </label>
                    <input
                        id="register-email-phone"
                        className="field-input"
                        placeholder="example@hospital.vn"
                        value={formData.email_phone}
                        onChange={(e) => handleChange('email_phone', e.target.value)}
                        required
                    />

                    <label className="field-label" htmlFor="register-password">
                        Password
                    </label>
                    <input
                        id="register-password"
                        className="field-input"
                        type="password"
                        placeholder="At least 8 characters"
                        value={formData.password}
                        onChange={(e) => handleChange('password', e.target.value)}
                        autoComplete="new-password"
                        required
                    />

                    <label className="field-label" htmlFor="register-full-name">
                        Full name
                    </label>
                    <input
                        id="register-full-name"
                        className="field-input"
                        placeholder="Nguyen Van A"
                        value={formData.full_name}
                        onChange={(e) => handleChange('full_name', e.target.value)}
                        required
                    />

                    <div className="split-fields">
                        <div>
                            <label className="field-label" htmlFor="register-dob">
                                Date of birth
                            </label>
                            <input
                                id="register-dob"
                                className="field-input"
                                type="date"
                                value={formData.date_of_birth}
                                onChange={(e) => handleChange('date_of_birth', e.target.value)}
                                required
                            />
                        </div>

                        <div>
                            <label className="field-label" htmlFor="register-gender">
                                Gender
                            </label>
                            <select
                                id="register-gender"
                                className="field-input"
                                value={formData.gender}
                                onChange={(e) => handleChange('gender', e.target.value)}
                            >
                                <option value="MALE">Male</option>
                                <option value="FEMALE">Female</option>
                            </select>
                        </div>
                    </div>

                    <label className="field-label" htmlFor="register-address">
                        Address
                    </label>
                    <input
                        id="register-address"
                        className="field-input"
                        placeholder="District, city"
                        value={formData.address}
                        onChange={(e) => handleChange('address', e.target.value)}
                        required
                    />

                    <button type="submit" className="primary-btn" disabled={loading}>
                        {loading ? 'Creating account...' : 'Register'}
                    </button>
                </form>

                <button type="button" className="text-btn" onClick={onSwitchToLogin}>
                    Back to Login
                </button>
            </section>
        </div>
    );
}