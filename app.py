from flask import Flask, request, jsonify, render_template
from config import get_db_connection
from flask_bcrypt import Bcrypt
import jwt
from datetime import datetime, timedelta  
from flask_mail import Mail, Message
from decimal import Decimal, InvalidOperation
from flask_cors import CORS
from functools import wraps


app = Flask(__name__)
bcrypt = Bcrypt(app)

SECRET_KEY = 'qiamfjvyslrbvtxkj'

CORS(app)

@app.route("/")
def home():
    return render_template('index.html')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing!"}), 403
        
        try:
            token = token.split(" ")[1]  # Token is expected as "Bearer <token>"
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = data['account_id']
        except Exception as e:
            return jsonify({"message": "Token is invalid!"}), 403
        
        return f(*args, **kwargs)
    return decorated

@app.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id= %s", (user_id,))
    account = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if account:
        return jsonify(account)
    return jsonify({"error": "Account not found"}), 404


@app.route('/balance/<int:account_id>', methods=['GET'])
@token_required
def get_balance(account_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT balance FROM accounts WHERE account_id= %s", (account_id,))
    account = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if account:
        return jsonify(account)
    return jsonify({"error": "Account not found"}), 404

# API for deposit (nạp tiền)
@app.route('/deposit', methods=['POST'])
@token_required
def deposit(*args, **kwargs):
    try:
        data = request.json
        account_id = data['account_id']
        amount = data['amount'] 

        # Kết nối cơ sở dữ liệu
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra tài khoản
        cursor.execute("SELECT * FROM accounts WHERE account_id = %s", (account_id,))
        account = cursor.fetchone()

        if account:
            user_id = account[1]  # Lấy 'user_id' từ tài khoản
            print(f"User ID: {user_id}")
        else:
            return jsonify({"error": "Account not found"}), 404

        # Lấy thông tin người dùng từ user_id
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            email = user[2]  # Lấy email từ kết quả truy vấn (giả sử email ở vị trí thứ 3)
            print(f"User Email: {email}")
        else:
            return jsonify({"error": "User not found"}), 404

        # Cập nhật số dư tài khoản
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s", (amount, account_id))

        # Ghi nhật ký giao dịch
        cursor.execute("INSERT INTO transactions (account_id, transaction_type, amount) VALUES (%s, %s, %s)", (account_id, 'deposit', amount))

        # Gửi email xác nhận giao dịch
        send_transaction_email(email, 'deposit', amount)

        # Xác nhận cập nhật cơ sở dữ liệu
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Deposit successful"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred"}), 500


# API for withdrawal (rút tiền)
@app.route('/withdraw', methods=['POST'])
@token_required
def withdraw():
    # Giới hạn số tiền rút trong ngày (10 triệu VND)
    DAILY_WITHDRAW_LIMIT = Decimal('100000000')
    
    data = request.json
    account_id = data['account_id']
    
    # Convert the amount to Decimal
    try:
        amount = Decimal(data['amount'])  # Convert to Decimal
    except (InvalidOperation, ValueError):
        return jsonify({"message": "Invalid amount provided."}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Lấy số dư tài khoản
    cursor.execute("SELECT * FROM accounts WHERE account_id = %s", (account_id,))
    account = cursor.fetchone()

    if account:
        user_id = account['user_id'] 
        print(f"User ID: {user_id}")
    else:
        return jsonify({"error": "Account not found"}), 404

    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if user:
        email = user['email']   
        print(f"User Email: {email}")
    else:
        return jsonify({"error": "User not found"}), 404
    
    # Kiểm tra tổng số tiền đã rút trong ngày
    today = datetime.now().date()
    cursor.execute("""
    SELECT SUM(amount) AS total_withdrawn 
    FROM transactions 
    WHERE account_id = %s AND transaction_type = 'withdraw' AND DATE(date) = %s """, (account_id, today))
    result = cursor.fetchone()
    total_withdrawn_today = result['total_withdrawn'] if result['total_withdrawn'] else Decimal('0')

    
    # Kiểm tra xem tổng số tiền rút hôm nay có vượt quá giới hạn hay không
    if (total_withdrawn_today + amount) > DAILY_WITHDRAW_LIMIT:
        cursor.close()
        conn.close()
        return jsonify({"message": "Exceeded daily withdrawal limit"}), 400

    # Kiểm tra số dư có đủ để rút không
    if account and account['balance'] >= amount:
        new_balance = account['balance'] - amount
        
        # Cập nhật số dư tài khoản
        cursor.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", (new_balance, account_id))
        
        # Thêm giao dịch rút tiền vào lịch sử
        cursor.execute("INSERT INTO transactions (account_id, transaction_type, amount) VALUES(%s, %s, %s)",
                       (account_id, 'withdraw', amount))
        conn.commit()
        cursor.close()
        conn.close()

        send_transaction_email(email, 'withdraw', amount)
        
        return jsonify({"message": "Withdrawal successful", "new_balance": str(new_balance)})
    else:
        cursor.close()
        conn.close()
        return jsonify({"message": "Insufficient funds"}), 400
    

# API cho lịch sử giao dịch
@app.route('/transactions/<int:account_id>', methods=['GET'])
@token_required
def get_transaction_history(account_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM transactions WHERE account_id = %s ORDER BY date DESC", (account_id,))
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if transactions:
        return jsonify(transactions)
    return jsonify({"error": "Không tìm thấy giao dịch nào"}), 404


@app.route('/transfer', methods=['POST'])
@token_required
def transfer():
    data = request.json
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    amount = data['amount']
    amount = Decimal(amount)  # Chuyển đổi amount thành Decimal

    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Kiểm tra số dư của người gửi
    cursor.execute("SELECT balance FROM accounts WHERE account_id = %s", (sender_id,))
    sender = cursor.fetchone()

    cursor.execute("SELECT * FROM accounts WHERE account_id = %s", (sender_id,))
    account = cursor.fetchone()

    if account:
        user_id = account['user_id'] 
        print(f"User ID: {user_id}")
    else:
        return jsonify({"error": "Account not found"}), 404

    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if user:
        email = user['email']   
        print(f"User Email: {email}")
    else:
        return jsonify({"error": "User not found"}), 404
    
    if sender and sender['balance'] >= amount:
        # Cập nhật số dư người gửi
        new_sender_balance = sender['balance'] - amount
        cursor.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", (new_sender_balance, sender_id))
        
        # Cập nhật số dư người nhận
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s", (amount, receiver_id))
        
        # Ghi lại giao dịch cho cả người gửi và người nhận
        cursor.execute("INSERT INTO transactions (account_id, transaction_type, amount) VALUES(%s, %s, %s)", 
                       (sender_id, 'transfer_out', amount))
        cursor.execute("INSERT INTO transactions (account_id, transaction_type, amount) VALUES(%s, %s, %s)", 
                       (receiver_id, 'transfer_in', amount))
        
        conn.commit()
        cursor.close()
        conn.close()

        send_transaction_email(email, 'transfer', amount)

        
        return jsonify({"message": "Chuyển tiền thành công"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"message": "Số dư không đủ"}), 400


# API cho đăng ký người dùng
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    email = data['email']
    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Chèn người dùng vào bảng users
    cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))

    # Lấy user_id của người dùng vừa được chèn
    user_id = cursor.lastrowid  # Lấy ID của bản ghi vừa chèn vào

    # Chèn tài khoản mới vào bảng accounts với user_id
    cursor.execute("INSERT INTO accounts (user_id, balance) VALUES (%s, %s)", (user_id, 0))

    # Xác nhận và đóng kết nối
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Người dùng đăng ký thành công"}), 201




# API cho đăng nhập người dùng
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Lấy thông tin người dùng từ bảng users
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user['password'], password):
        # Lấy thông tin tài khoản tương ứng với user_id
        cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (user['id'],))
        account = cursor.fetchone()
        
        token = jwt.encode({
            'account_id': account['account_id'],  
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(hours=24)  # Correctly use timedelta
        }, SECRET_KEY)
        
        # Trả về token và thông tin tài khoản
        return jsonify({"token": token}), 200
    
    cursor.close()
    conn.close()
    return jsonify({"message": "Thông tin đăng nhập không hợp lệ"}), 401



# API cho thay đổi mật khẩu
@app.route('/change-password', methods=['POST'])
def change_password():
    data = request.json
    email = data['email']  # Thay đổi từ user_id thành email
    old_password = data['old_password']
    new_password = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Tìm người dùng dựa trên email
    cursor.execute("SELECT password, id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user['password'], old_password):
        # Cập nhật mật khẩu cho người dùng
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, user['id']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Mật khẩu thay đổi thành công"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"message": "Mật khẩu cũ không đúng hoặc email không tồn tại"}), 400



# Cấu hình email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'selingbook@gmail.com'
app.config['MAIL_PASSWORD'] = 'vhjwmpxapduytwoq'
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False 


mail = Mail(app)

# Hàm gửi email thông báo giao dịch
def send_transaction_email(email, transaction_type, amount):
    try:
        amount = Decimal(amount)
    except InvalidOperation:
        return {"error": "Invalid amount"}

    formatted_amount = f"{amount:,.0f}"  
    
    msg = Message(f"{transaction_type.capitalize()} Notification", 
                  sender="selingbook@gmail.com", 
                  recipients=[email])
    
    msg.body = f"Giao dịch {transaction_type} với số tiền {formatted_amount} VND đã được thực hiện thành công."
    
    mail.send(msg)


if __name__ == "__main__":
    app.run(debug=True)