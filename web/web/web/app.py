import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector 
import json
from datetime import datetime
import time

#Initializing Flask Application
app = Flask(__name__)
app.secret_key = 'secretkey'
# app.config['PATH'] = 'http://localhost'
app.config['PATH'] = 'http://127.0.0.1:5000'

#Initializing database Object
conn = mysql.connector.connect(
    host='localhost',
    user = 'root',
    passwd = 'root',
    port = 3306,
    database = 'shoppingdb'
)
cursor = conn.cursor()

#
# ==========================================
#  Create Database and Table when id not exists
# ==========================================
#

cursor.execute("CREATE DATABASE IF NOT EXISTS shoppingdb") #ถ้ามีข้อมุูลจะสร้างdbชื่อ shoppingdb

cursor.execute("USE shoppingdb")

cursor.execute('''CREATE TABLE IF NOT EXISTS Account ( #สร้างdb account
        acc_id int(11) NOT NULL AUTO_INCREMENT,
        acc_username varchar(50) NOT NULL,
        acc_password varchar(255) NOT NULL,
        acc_email varchar(100) NOT NULL,
        acc_address varchar(50) NOT NULL,

        PRIMARY KEY (acc_id)
    );
''')    

cursor.execute('''CREATE TABLE IF NOT EXISTS Product (
        pct_id int(11) NOT NULL AUTO_INCREMENT,
        pct_name varchar(50) NOT NULL,
        pct_price float(10) NOT NULL,
        pct_amount int(10) NOT NULL,
        pct_image MEDIUMBLOB NULL,

        PRIMARY KEY (pct_id)
    );
''') 

cursor.execute('''CREATE TABLE IF NOT EXISTS Cart (
        crt_id int(11) NOT NULL AUTO_INCREMENT,
        crt_amount varchar(50) NOT NULL,
        crt_status float(10) NOT NULL,
        crt_update_date datetime NOT NULL,

        crt_acc_id int(11) NOT NULL,
        crt_pct_id int(11) NOT NULL,

        PRIMARY KEY (crt_id),

        FOREIGN KEY(crt_acc_id) REFERENCES Account(acc_id),
        FOREIGN KEY(crt_pct_id) REFERENCES Product(pct_id) ON DELETE CASCADE
    );
''') 

cursor.execute('''CREATE TABLE IF NOT EXISTS Payment (
        pay_id int(11) NOT NULL AUTO_INCREMENT,

        pay_acc_id int(11) NULL,

        PRIMARY KEY (pay_id),

        FOREIGN KEY(pay_acc_id) REFERENCES Account(acc_id)
    );
''') 

cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
        trs_id int(11) NOT NULL AUTO_INCREMENT,

        trs_pay_id int(11) NULL,
        trs_pct_id int(11) NULL,
        trs_acc_id int(11) NULL,

        PRIMARY KEY (trs_id),

        FOREIGN KEY(trs_pay_id) REFERENCES Payment(pay_id),
        FOREIGN KEY(trs_pct_id) REFERENCES Product(pct_id) ON DELETE CASCADE,
        FOREIGN KEY(trs_acc_id) REFERENCES Account(acc_id)
    );
''') 

conn.commit()

cursor.close() 

def clearSession():
    session.pop('loggedin', None) # pop คือ อ่านค่าของสมาชิกที่มีคีย์ตามที่ระบุ จากนั้นลบสมาชิกตัวนั้น

def auth():
    if 'loggedin' in session:
        return True
    return False

@app.route("/")
def index():
    if auth():
        return redirect('/home') #ประมาณว่าถ้า login ได้จะเข้าหน้าโฮม
    else:
        return redirect('/login') #login ไม่ได้มาหน้า login ใหม่
    
@app.route("/home")
def home():
    if auth():
        return render_template('pages/home.html') # render หน้า home.html ในกรณี login ผ่าน
    else:
        return redirect('/login')

@app.route("/login")
def login():
    clearSession()
    return render_template('pages/login.html') #render หน้า login

@app.route("/register")
def register():
    clearSession()
    return render_template('pages/register.html') #render หน้า register

@app.route("/cart")
def cart():
    if auth():
        return render_template('pages/cart.html') #render หน้า cart
    else:
        return redirect('/login')

@app.route("/admin")
def admin():
    return render_template('pages/admin.html') #render หน้า admin


@app.route("/get-login", methods=['POST']) 
def get_login():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()
        
        cursor = conn.cursor(dictionary=True, buffered=True)

        if request.method == "POST": #ถ้า url เป็น post
            criteria = request.form
            
            # เป็นการเรียก Database จากตาราง Account ในคอลลัม acc_username เเละ acc_password
            sql = '''SELECT * FROM Account WHERE acc_username = %s AND acc_password = %s''' #แสดงข้อมูลของ user ที่ login มา
            val = (criteria['username'], criteria['password'])
            cursor.execute(sql, val)  #อารมเหมือนรัน sql
            results = cursor.fetchone()

            if results:            
                session['loggedin'] = True
                session['id'] = results['acc_id'] #ตรวจสอบการ login ว่าถูกรึป่าว 

                status = {'message': "OK"}
            else:
                status = {'message': "ERROR"}
        else:
            status = {'message': "ERROR"}
    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status}

@app.route("/get-register", methods=['POST'])
def get_register():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()

        cursor = conn.cursor(dictionary=True, buffered=True)
        
        if request.method == "POST":
            criteria = request.form
                    
            sql = '''SELECT * FROM Account WHERE acc_username = %s'''
            val = (criteria['username'],)
            cursor.execute(sql, val)
            results = cursor.fetchone()

            if results:            
                status = {'message': "USERNAMA_ALREADY"}
                return {'status' : status, 'response' : response}
            
            sql = '''SELECT * FROM Account WHERE acc_email = %s'''
            val = (criteria['email'],)
            cursor.execute(sql, val)
            results = cursor.fetchone()

            if results:            
                status = {'message': "EMAIL_ALREADY"}
                return {'status' : status, 'response' : response} #ประมานว่าเช็คข้อมูล username ซ้ำรึป่าว

                # INSERT INTO การเชื่อมข้อมูลที่มีค่ามากกว่า 2 ตาราง
            sql = '''INSERT INTO Account (  
                acc_username,
                acc_password,
                acc_email,
                acc_address
            ) VALUES (%s, %s, %s, %s)''' #insert ข้อมูล user ใหม่
            val = (criteria['username'], criteria['password'], criteria['email'], criteria['address'])
            cursor.execute(sql, val) #รันคำสั่ง
            conn.commit() # บันทึก

            status = {'message': "OK"}
        else:
            status = {'message': "ERROR"}
    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status, 'response' : response}

@app.route("/get-all-product")
def get_all_product():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()

        cursor = conn.cursor(dictionary=True, buffered=True)
        
        sql = '''SELECT * FROM Product'''
        cursor.execute(sql)
        rows = cursor.fetchall() # ใช้สำหรับดึงเอาข้อมูลของ Database  มาแสดง
        
        response['products'] = []

        if rows:
            for row in rows:
                response['products'].append({
                    'pct_id'        : row['pct_id'],
                    'pct_name'      : row['pct_name'],
                    'pct_price'     : row['pct_price'],
                    'pct_amount'    : row['pct_amount'],
                    'pct_image'     : row['pct_image'].decode('utf-8'),
                }) #แสดงข้อมูลน่าจะเป็นตารางของสินค้า
        
        status = {'message': "OK"}

    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status, 'response' : response}

@app.route("/add-to-cart", methods=['POST'])
def add_to_cart():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()
        
        cursor = conn.cursor(dictionary=True, buffered=True)

        if request.method == "POST":
            criteria = request.form
                
            sql = '''SELECT * FROM Cart WHERE crt_status=0 AND crt_acc_id=%s AND crt_pct_id=%s''' #แสดงข้อมูลส้นค้าในตะกร้า
            val = (session['id'], criteria['pct_id'])
            cursor.execute(sql, val)
            item = cursor.fetchone()

            if item:
                sql = '''SELECT * FROM Product 
                         INNER JOIN Cart ON crt_pct_id = pct_id
                         WHERE crt_pct_id=%s''' #แสดงข้อมูลสิ้นค้าที่อยู่ในตาราง product และ cart คือประมานว่าสินค้าตัวเดียวกันใน 2 ตารางอะ
                val = (item['crt_pct_id'],)
                cursor.execute(sql, val) # cursor สำหรับใช้กับตาราง เพื่อเเสดงข้อมูล
                product = cursor.fetchone()

                #product < cart + product || product <= 0 = error ถ้ายอดสินค้าน้อยกว่าในตะกร้า+ยอดสินค้า(นอกตะกร้า) หรือ ยอดสินค้า <=0 จะ error

                
                if int(product['pct_amount']) < int(item['crt_amount'])+int(criteria['pct_amount']) or int(product['pct_amount']) <= 0:
                    status = {'message': "ERROR"}
                else:
                    if int(item['crt_amount']) == 0: # ถ้าไม่มีสินค้าในตะกร้า จะ update ตามคำสั่ง sql ด้านล่าง

                        sql = '''UPDATE Cart
                                SET crt_amount=%s,
                                    crt_update_date=%s
                                WHERE crt_status=0 AND crt_acc_id=%s AND crt_pct_id=%s'''
                        val = (int(item['crt_amount'])+int(criteria['pct_amount']), datetime.now(), session['id'], int(criteria['pct_id']))
                    else:
                        sql = '''UPDATE Cart
                                SET crt_amount=%s
                                WHERE crt_status=0 AND crt_acc_id=%s AND crt_pct_id=%s'''
                        val = (int(item['crt_amount'])+int(criteria['pct_amount']), session['id'], int(criteria['pct_id']))
                    cursor.execute(sql, val)
                    conn.commit()
                    status = {'message': "OK"}
            else:
                sql = '''SELECT * FROM Product WHERE pct_id=%s''' #ถ้ามีสินค้า จะ select ข้อมูล
                val = (criteria['pct_id'],)
                cursor.execute(sql, val) # cursor ใช้สำหรับชี้ลิงค์ต่างๆ ไปยังฐานข้อมูล
                product = cursor.fetchone() # fetchone ดึงข้อมูลมา 1 เเถว 

                if int(product['pct_amount']) < int(criteria['pct_amount']) or int(product['pct_amount']) == 0:
                    status = {'message': "ERROR"}
                else:
                    sql = '''INSERT INTO Cart( 
                            crt_amount,
                            crt_status,
                            crt_update_date,

                            crt_acc_id, 
                            crt_pct_id 
                        ) VALUES (%s, %s, %s, %s, %s)'''
                    val = (criteria['pct_amount'], 0, datetime.now(), session['id'], criteria['pct_id'])
                    cursor.execute(sql, val)
                    conn.commit()
                    
                    status = {'message': "OK"}
                    
    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status}

@app.route("/update-cart", methods=['POST'])  #update ตะกร้า
def update_cart():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()

        cursor = conn.cursor(dictionary=True, buffered=True)  # cursor สำหรับใช้กับตาราง เพื่อเเสดงข้อมูล
        
        if request.method == "POST":
            criteria = request.form
            
            sql = '''SELECT * FROM Cart WHERE crt_id=%s'''
            val = (criteria['crt_id'],)
            cursor.execute(sql, val) # cursor ใช้สำหรับชี้ลิงค์ต่างๆ ไปยังฐานข้อมูล
            item = cursor.fetchone() # fetchone ดึงข้อมูลมา 1 เเถว 
            #อ่านรายการทั้งหมด โดยคืนค่ากลับมาเป็นทูเพิล (Value)

            sql = '''SELECT * FROM Product 
                     INNER JOIN Cart ON crt_pct_id = pct_id
                     WHERE crt_id=%s'''
            val = (criteria['crt_id'],)
            cursor.execute(sql, val) # cursor ใช้สำหรับชี้ลิงค์ต่างๆ ไปยังฐานข้อมูล
            product = cursor.fetchone()

            if int(product['pct_amount']) < int(criteria['crt_amount']):
                status = {'message': "ERROR"}
                response['amount'] = int(item['crt_amount'])
            else:
                sql = '''UPDATE Cart
                         SET crt_amount=%s
                         WHERE crt_id=%s'''
                val = (criteria['crt_amount'], criteria['crt_id'])
                cursor.execute(sql, val) # cursor ใช้สำหรับชี้ลิงค์ต่างๆ ไปยังฐานข้อมูล
                conn.commit() # ทุกครั้งที่มีการ execute จะต้องมีการ Commit
                status = {'message': "OK"}
                response['amount'] = int(criteria['crt_amount'])

    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status, 'response' : response}

@app.route("/delete-cart", methods=['POST']) #ลบสินค้าในตะกร้า
def delete_cart():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()

        cursor = conn.cursor(dictionary=True, buffered=True)  # cursor สำหรับใช้กับตาราง เพื่อเเสดงข้อมูล
        
        if request.method == "POST":
            criteria = request.form
            
            sql = '''DELETE FROM Cart WHERE crt_id=%s''' # ลบสินค้า id ที่เท่านี้ๆ
            val = (criteria['crt_id'],)
            cursor.execute(sql, val)
            conn.commit()

            status = {'message': "OK"}

    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status, 'response' : response}

@app.route("/get-cart", methods=['POST', 'GET'])
def get_cart():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()

        cursor = conn.cursor(dictionary=True, buffered=True)
        
        sql = '''SELECT * 
                 FROM Cart 
                 INNER JOIN Product ON pct_id = crt_pct_id
                 WHERE crt_acc_id = %s AND crt_status=0
                 ORDER BY crt_update_date ASC'''  #แสดงสินค้าในตะกร้า ที่ pct_id = crt_pct_id ของทั้ง 2 ตาราง (Product,cart)
        val = (session['id'],)
        cursor.execute(sql, val)
        rows = cursor.fetchall()

        response['cart'] = []
        if rows:
            for row in rows:                    
                response['cart'].append({
                    'pct_id'        : row['pct_id'],
                    'pct_name'      : row['pct_name'],
                    'pct_price'     : row['pct_price'],
                    'pct_amount'    : row['pct_amount'],
                    'pct_image'     : row['pct_image'].decode('utf-8'),
                    'crt_id'        : row['crt_id'],
                    'crt_amount'    : row['crt_amount'], #เพิ่มข้อมูลสินค้าลงตะกร้า
                })
        
            status = {'message': "OK"}

    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status, 'response' : response}

@app.route("/get-payment", methods=['POST']) #จ่ายตัง
def get_payment():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()
            
        cursor = conn.cursor(dictionary=True, buffered=True)

        if request.method == "POST":
            
            sql = '''SELECT * 
                     FROM Cart 
                     WHERE crt_status=0 AND crt_acc_id=%s'''
            val = (session['id'],)
            cursor.execute(sql, val)
            items = cursor.fetchall()
            
            sql = '''INSERT INTO Payment(
                    pay_acc_id
                ) VALUES (%s)'''
            val = (session['id'],)
            cursor.execute(sql, val)
            conn.commit()
            
            sql = '''SELECT * FROM Payment WHERE pay_acc_id=%s ORDER BY pay_id DESC'''
            val = (session['id'],)
            cursor.execute(sql, val)
            pay = cursor.fetchall()

            
            if items:
                for item in items:
                    sql = '''INSERT INTO Transactions(
                            trs_pay_id,
                            trs_pct_id,
                            trs_acc_id
                        ) VALUES (%s, %s, %s)''' #แสดงข้อมูล transaction การจ่ายตัง
                    val = (pay[0]['pay_id'], item['crt_pct_id'], session['id'])
                    cursor.execute(sql, val)
                    conn.commit()

                    sql = '''UPDATE Cart
                            SET crt_status=1,
                                crt_update_date=%s
                            WHERE crt_id=%s'''
                    val = (datetime.now(), item['crt_id'],)
                    cursor.execute(sql, val)
                    conn.commit()

                    sql = '''SELECT * FROM Product WHERE pct_id=%s'''
                    val = (item['crt_pct_id'],)
                    cursor.execute(sql, val)
                    pro = cursor.fetchone()

                    sql = '''UPDATE Product
                            SET pct_amount=%s
                            WHERE pct_id=%s'''
                    val = (int(pro['pct_amount']) - int(item['crt_amount']), item['crt_pct_id'])
                    cursor.execute(sql, val)
                    conn.commit()

            status = {'message': "OK"}

    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status, 'response' : response}

@app.route("/update-product", methods=['POST'])
def update_product():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()
        
        cursor = conn.cursor(dictionary=True, buffered=True) 

        if request.method == "POST":
            criteria = request.form
            
            if criteria['pct_id'] == "":  #ถ้าไม่มีสินค้าตัวนี้ ก็เพิ่มใหม่
                sql = '''INSERT INTO Product(
                        pct_name,
                        pct_price,
                        pct_amount,
                        pct_image 
                    ) VALUES (%s, %s, %s, %s)'''
                val = (criteria['pct_name'], criteria['pct_price'], criteria['pct_amount'], criteria['pct_image'])
                cursor.execute(sql, val)
                conn.commit() #บันทึกข้อมูล
                status = {'message': "OK"}
            else:
                #แต่ถ้ามีจะ update
                sql = '''UPDATE Product  
                        SET pct_name=%s,
                            pct_price=%s,
                            pct_amount=%s,
                            pct_image=%s
                        WHERE pct_id=%s'''
                val = (criteria['pct_name'], criteria['pct_price'], criteria['pct_amount'], criteria['pct_image'], criteria['pct_id'])
                cursor.execute(sql, val)
                conn.commit()
                status = {'message': "OK"}
                    
    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status}

@app.route("/remove-product", methods=['POST'])
def remove_product():
    try:
        status = {}
        response = {}
        # conn = get_db_connection()
        # cursor = conn.cursor()
        
        cursor = conn.cursor(dictionary=True, buffered=True)

        if request.method == "POST":
            criteria = request.form

            sql = '''DELETE FROM Product
                    WHERE pct_id=%s'''
            val = (criteria['pct_id'],)
            cursor.execute(sql, val)
            conn.commit()
            status = {'message': "OK"}
                    
    except Exception as e:
        print(e)
        status = {'message': "ERROR"}
    finally:
        cursor.close()
        return {'status' : status}

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')