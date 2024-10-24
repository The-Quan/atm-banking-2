import React, { useState } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import './Login.css'; // Nhập file CSS

const Login = () => {
    const [loginData, setLoginData] = useState({ email: '', password: '' });
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const data = await axios.post(`http://127.0.0.1:5000/login`, loginData);
            const token = data.data;
            localStorage.setItem('authToken', token.token);
            navigate('/banking');
        } catch (error) {
            console.error("Login failed:", error);
        }
    };

    return (
        <div className="login-container">
            <h2 className="login-title">User Login</h2>
            <form className="login-form" onSubmit={handleLogin}>
                <input
                    className="login-input"
                    type="email"
                    value={loginData.email}
                    onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                    placeholder="Email"
                    required
                />
                <input
                    className="login-input"
                    type="password"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    placeholder="Password"
                    required
                />
                <button className="login-button" type="submit">Login</button>
            </form>
            <Link className="login-link" to='/register'>Register</Link>
            <Link className="login-link" to='/forgot-password'>Forgot Password</Link>
        </div>
    );
};

export default Login;
