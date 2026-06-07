import { useState } from 'react';
import api from '../api';

export default function Register({ onSwitchToLogin }) {
    const [role, setRole] = useState('patient');
    const [formData, setFormData] = useState({
        email_phone: '', 
        password: '', 
        full_name: '', 
        otp_code: 'string',
        date_of_birth: '2005-01-01', // Mặc định
        gender: 'MALE',              // Mặc định
        address: 'Hanoi'             // Thêm trường này nếu schema yêu cầu
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        const endpoint = role === 'patient' ? '/auth/register/patient' : '/auth/register/doctor';
        try {
            await api.post(endpoint, formData);
            alert('Đăng ký thành công!');
            onSwitchToLogin();
        } catch (err) {
            console.error("Lỗi đăng ký:", err.response?.data);
            alert("Lỗi: " + JSON.stringify(err.response?.data?.detail || "Đăng ký thất bại"));
        }
    };

    return (
        <div style={{ maxWidth: '400px', margin: '50px auto' }}>
            <h2>Register</h2>
            <select onChange={(e) => setRole(e.target.value)}>
                <option value="patient">Patient</option>
                <option value="doctor">Doctor</option>
            </select>
            <form onSubmit={handleSubmit}>
                <input placeholder="Email/Phone" onChange={e => setFormData({...formData, email_phone: e.target.value})} required />
                <input type="password" placeholder="Password" onChange={e => setFormData({...formData, password: e.target.value})} required />
                <input placeholder="Full Name" onChange={e => setFormData({...formData, full_name: e.target.value})} required />
                <input placeholder="Date of Birth (YYYY-MM-DD)" onChange={e => setFormData({...formData, date_of_birth: e.target.value})} required />
                <select onChange={e => setFormData({...formData, gender: e.target.value})}>
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                </select>
                <input placeholder="Address" onChange={e => setFormData({...formData, address: e.target.value})} required />
                <button type="submit">Register</button>
            </form>
            <button onClick={onSwitchToLogin}>Back to Login</button>
        </div>
    );
}