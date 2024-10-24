import React, { useState } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom'; // Nhập useNavigate
import './Register.css'; // Nhập CSS

const Register = () => {
    const [registerData, setRegisterData] = useState({ name: '', email: '', password: '' });
    const navigate = useNavigate(); // Khởi tạo useNavigate

    const handleRegister = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`http://127.0.0.1:5000/register`, registerData);
            navigate('/logout');
        } catch (error) {
            console.error("Register failed:", error);
        }
    };

    return (
        <div className="register-container">
            <h2 className="register-title">User Registration</h2>
            <form className="register-form" onSubmit={handleRegister}>
                <input
                    className="register-input"
                    type="text"
                    value={registerData.name}
                    onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                    placeholder="Name"
                    required
                />
                <input
                    className="register-input"
                    type="email"
                    value={registerData.email}
                    onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                    placeholder="Email"
                    required
                />
                <input
                    className="register-input"
                    type="password"
                    value={registerData.password}
                    onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                    placeholder="Password"
                    required
                />
                <button className="register-button" type="submit">Register</button>
            </form>
            <Link className="login-link" to='/logout'>Login</Link>
        </div>
    );
};

export default Register;
