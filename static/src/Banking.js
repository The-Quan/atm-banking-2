import React, { useEffect, useState } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import './Banking.css';
import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';  // Import jwtDecode


const App = () => {
    const token = localStorage.getItem('authToken');
    const decoded = jwtDecode(token);
    const user_id = decoded.user_id
    const accountId = decoded.account_id

    const [messages, setMessages] = useState('');
    const [formData, setFormData] = useState({
        balanceId: accountId,
        deposit: { account_id: accountId, amount: '' },
        withdraw: { account_id: accountId, amount: '' },
        transfer: { sender_id: accountId, receiver_id: '', amount: '' },
        historyId: '',
        changePassword: { user_id: '', old_password: '', new_password: '' },
    });
    const [transactionHistory, setTransactionHistory] = useState([]);
    const [userData, setUserData] = useState(null);

    const navigate = useNavigate();


    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get(`http://127.0.0.1:5000/user/${user_id}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                setUserData(response.data);
            } catch (error) {
                console.error("Error fetching user data:", error);
            }
        };
        fetchData();
    }, []);

    const handleSubmitGet = async (e, endpoint, data, resetFields = () => { }) => {
        e.preventDefault();
        try {
            const response = await axios.get(`http://127.0.0.1:5000/${endpoint}`, {
                params: data,
                headers: {
                    'Authorization': `Bearer ${token}` // Add token to headers
                }
            });

            const formattedBalance = new Intl.NumberFormat('vi-VN', {
                style: 'decimal',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            }).format(response.data.balance);

            setMessages(<div className="alert alert-success">{formattedBalance} VND</div>);
            resetFields();
        } catch (error) {
            setMessages(<div className="alert alert-danger">{error.response?.data?.message || 'An error occurred'}</div>);
        }
    };

    const handleSubmit = async (e, endpoint, data, resetFields = () => { }) => {
        e.preventDefault();
        try {
            const response = await axios.post(`http://127.0.0.1:5000${endpoint}`, data, {
                headers: {
                    'Authorization': `Bearer ${token}` // Add token to headers for POST
                }
            });

            let successMessage;
            switch (endpoint) {
                case '/deposit':
                    successMessage = "Deposit successful!";
                    break;
                case '/withdraw':
                    successMessage = "Withdraw successful!";
                    break;
                case '/transfer':
                    successMessage = "Transfer successful!";
                    break;
                default:
                    successMessage = response.data.message;
            }
            setMessages(<div className="alert alert-success">{successMessage}</div>);
            resetFields();
        } catch (error) {
            setMessages(<div className="alert alert-danger">{error.response?.data?.message || 'An error occurred'}</div>);
        }
    };

    const logout = () => {
        localStorage.removeItem('authToken')
        navigate('/logout')
    };

    const handleChange = (e, key, nestedKey) => {
        if (nestedKey) {
            setFormData({ ...formData, [key]: { ...formData[key], [nestedKey]: e.target.value } });
        } else {
            setFormData({ ...formData, [key]: e.target.value });
        }
    };

    const fetchTransactionHistory = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.get(`http://127.0.0.1:5000/transactions/${accountId}`, {
                headers: {
                    'Authorization': `Bearer ${token}` // Add token to headers for GET
                }
            });
            setTransactionHistory(response.data);
            setMessages(<div className="alert alert-success">Transaction history fetched successfully!</div>);
        } catch (error) {
            setMessages(<div className="alert alert-danger">{error.response?.data?.message || 'An error occurred'}</div>);
        }
    };

    return (
        <div className="container mt-5">
            <h3>Hi, {userData?.name || "User"}</h3>
            <button onClick={logout} >Log Out</button>
            <h1 className="text-center">Banking Application</h1>
            <div id="messages">{messages}</div>

            <h2>Check Balance</h2>
            <form onSubmit={(e) => handleSubmitGet(e, `balance/${formData.balanceId}`, {})}>
                <button type="submit">Check Balance</button>
            </form>

            <h2>Deposit Money</h2>
            <form onSubmit={(e) => handleSubmit(e, '/deposit', formData.deposit, () => setFormData(prev => ({ ...prev, deposit: { account_id: accountId, amount: '' } })))}>
                <input
                    type="number"
                    value={formData.deposit.amount}
                    onChange={(e) => handleChange(e, 'deposit', 'amount')}
                    placeholder="Amount"
                    required
                />
                <button type="submit">Deposit</button>
            </form>

            <h2>Withdraw Money</h2>
            <form onSubmit={(e) => handleSubmit(e, '/withdraw', formData.withdraw, () => setFormData(prev => ({ ...prev, withdraw: { account_id: accountId, amount: '' } })))}>
                <input
                    type="number"
                    value={formData.withdraw.amount}
                    onChange={(e) => handleChange(e, 'withdraw', 'amount')}
                    placeholder="Amount"
                    required
                />
                <button type="submit">Withdraw</button>
            </form>


            <h2>Transfer Money</h2>
            <form onSubmit={(e) => handleSubmit(e, '/transfer', formData.transfer, () => setFormData({ ...formData, transfer: { receiver_id: '', amount: '' } }))}>
                <input
                    type="number"
                    value={formData.transfer.receiver_id}
                    onChange={(e) => handleChange(e, 'transfer', 'receiver_id')}
                    placeholder="Receiver Account ID"
                    required
                />
                <input
                    type="number"
                    value={formData.transfer.amount}
                    onChange={(e) => handleChange(e, 'transfer', 'amount')}
                    placeholder="Amount"
                    required
                />
                <button type="submit">Transfer</button>
            </form>

            <h2>Transaction History</h2>
            <form onSubmit={fetchTransactionHistory}>
                <button type="submit">Get Transaction History</button>
            </form>

            {transactionHistory.length > 0 && (
                <div className="mt-4">
                    <h3>Transaction History Details</h3>
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Transaction ID</th>
                                <th>Account ID</th>
                                <th>Amount</th>
                                <th>Date</th>
                                <th>Transaction Type</th>
                            </tr>
                        </thead>
                        <tbody>
                            {transactionHistory.map((transaction) => (
                                <tr key={transaction.transaction_id}>
                                    <td>{transaction.transaction_id}</td>
                                    <td>{transaction.account_id}</td>
                                    <td>{new Intl.NumberFormat('vi-VN', {
                                        style: 'decimal',
                                        minimumFractionDigits: 0,
                                        maximumFractionDigits: 0,
                                    }).format(transaction.amount)}</td>
                                    <td>{transaction.date}</td>
                                    <td>{transaction.transaction_type}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default App;
