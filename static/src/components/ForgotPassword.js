import React, { useState } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import './ForgotPassword.css'; // Import your CSS file here

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    // Function to handle password change
    const handleChangePassword = async (e) => {
        e.preventDefault(); // Prevent the default form submission

        // Prepare the payload with email, old password, and new password
        const payload = {
            email: email, // Use email from the state
            old_password: oldPassword,
            new_password: newPassword,
        };

        try {
            const response = await axios.post('http://127.0.0.1:5000/change-password', payload);
            console.log(response.data); // Log success message
            setMessage("Password changed successfully!"); // Update the message state
            navigate('/logout'); // Navigate to the login page
        } catch (error) {
            console.error("Error changing password:", error.response?.data);
            setMessage("Error: " + (error.response?.data.message || "Something went wrong.")); // Set error message
        }
    };

    return (
        <div className="forgot-password-container">
            <h3 className="title">Change Password</h3>
            <form className="change-password-form" onSubmit={handleChangePassword}>
                <input
                    type="email"
                    className="input-field"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                />
                <input
                    type="password"
                    className="input-field"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    placeholder="Enter old password"
                    required
                />
                <input
                    type="password"
                    className="input-field"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    required
                />
                <button type="submit" className="submit-button">Change Password</button>
            </form>
            <div className="message">{message}</div>
            <Link className="login-link" to='/logout'>Login</Link>
            <Link className="login-link" to='/register'>Register</Link>
        </div>
    );
};

export default ForgotPassword;
