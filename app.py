import os
import random
import datetime
import razorpay
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_mail import Mail, Message
from utils import get_referral_code, authenticate_user, check_existing_user, get_pass_from_uid, get_subs_end, get_signup_otp_msg, get_payment_success_msg, get_update_email_msg, get_userid_from_email, check_email_in_users, get_forgot_pass_msg, get_interval_dates, make_chart, add_sales_by_dates , get_cogs, get_grevenue_gmargin, get_gexpenses, add_expenses_by_dates, add_expenses_by_category, group_sales_by_month, top_products, extract_interval_data, add_deleted_sale_qty_to_inventory, predict_sales, get_unpaid_customers, add_amt_unpaid_customers, get_latest_credits
from database import add_user, change_password, update_email_address, add_subscription_to_user, load_users, load_inventory, load_sales, load_wholesalers, load_ledgers, load_expenses, load_replacements, add_product, delete_product, update_product, add_wholesaler, delete_wholesaler, update_wholesaler, add_ledger, delete_ledger, update_ledger, add_sale, delete_sale, update_sale, add_expense, delete_expense, update_expense, add_replacement, delete_replacement, update_replacement

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['RAZORPAY_KEY_ID'] = os.environ.get('RAZORPAY_KEY_ID')
app.config['RAZORPAY_KEY_SECRET'] = os.environ.get('RAZORPAY_KEY_SECRET')

mail = Mail(app)

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST": 
        users = load_users()
        user_id, company, username, email, referral_code = authenticate_user(users, request.form["username"], request.form["password"])
        if user_id is None: 
            flash('Incorrect Password! Try again', 'danger')
            redirect(url_for('login'))
        else:
            session['user_id'] = user_id
            session['company'] = company
            session['username'] = username
            session['email'] = email
            session['referral_code'] = referral_code
            flash(f"Welcome to {company}\'s dashboard", 'success')
            return redirect('/dashboard/thismonth') 
    # If request.method = "GET"
    return render_template('login.html')

@app.route('/logout')
def logout():
    # clear session variables
    session.clear()
    # redirect to login page
    return redirect(url_for('login'))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST": 
      users = load_users()
      if check_existing_user(users, request.form["username"], request.form["email"]):
        session['username'] = request.form["username"]
        session['password'] = request.form["password"]
        session['company'] = request.form["company"]
        session['email'] = request.form['email']
        username = request.form["username"]
        otp = str(random.randint(1000, 9999))
        session['otp'] = otp
        msg = Message('FinCheck | OTP to Verify Email', sender= os.environ.get('MAIL_USERNAME'), recipients=[request.form['email']])
        msg.body = get_signup_otp_msg(username,otp)
        mail.send(msg)
        return render_template('login.html', showModal=True)

      else:
        flash('The username or email you entered already exists! Try again', 'danger')
        redirect(url_for('login'))
                       
    # If request.method = "GET"
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'email' not in session or 'otp' not in session:
        return redirect(url_for('login'))
      
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session['otp']:
            users = load_users()
            email = session.get('email')
            if check_email_in_users(users, email):
              return render_template('login.html', showNewPassModal=True)

            elif session.get('referral_code') is None: #New Sign up
              referral_code = get_referral_code()
              if add_user(session['username'], 
                      session['password'],
                      session['company'] ,
                      session['email'],
                      referral_code):
                session.clear()
                flash('Registration successful!', 'success')
                return redirect("/login")

            else:
              user_id = session.get('user_id')
              email = session.get('new-email')
              if update_email_address(user_id, email):
                session.clear()
                flash('Email Update Successful!', 'success')
                return redirect("/login")
              
        else:
            flash('Invalid OTP! Try again', 'danger')
            redirect(url_for('login'))

@app.route('/change-password', methods=["POST"])
def change_pass():
    if request.method == "POST": 
      users = load_users()
      if session.get('user_id') is None: # User forgot password
        email = session.get('email')
        user_id = get_userid_from_email(users,email)
        if  request.form["new-pass"] == request.form["re-new-pass"]:
          if change_password(user_id, request.form["new-pass"]):
            session.clear()
            flash('Password changed successfully', 'success')
            return redirect("/login")
      else:
        user_id = session.get('user_id')
        if request.form["old-pass"] == get_pass_from_uid(users, user_id) and request.form["new-pass"] == request.form["re-new-pass"]:
          if change_password(user_id, request.form["new-pass"]):
            flash('Password changed successfully', 'success')
            return redirect("/dashboard/thismonth")
        else:
            flash('Password change failed. Please try again', 'danger')
            return redirect("/dashboard/thismonth")

@app.route('/forgot-password', methods=["POST"])
def forgot_pass():
    if request.method == "POST": 
      users = load_users()
      session['email'] = request.form['email']
      if check_email_in_users(users, request.form["email"]):
          otp = str(random.randint(1000, 9999))
          session['otp'] = otp
          msg = Message('FinCheck | Forgot Password', sender= os.environ.get('MAIL_USERNAME'), recipients=[request.form['email']])
          msg.body = get_forgot_pass_msg(otp)
          mail.send(msg)
          return render_template('login.html', showModal=True)
      else:
          flash('Entered email id does not exists!', 'danger')
          return redirect("/login")

@app.route('/update-email', methods=["POST"])
def update_email():
    if request.method == "POST": 
        otp = str(random.randint(1000, 9999))
        session['otp'] = otp
        session['new-email'] = request.form['new-email']
        username = session.get('username')
        referral_code = session.get('referral_code')
        msg = Message('FinCheck | Update Email Address', sender= os.environ.get('MAIL_USERNAME'), recipients=[request.form['new-email']])
        msg.body = get_update_email_msg(username,otp)
        mail.send(msg)
        return render_template('login.html', showModal=True)

@app.route('/plans')
def plans():
    return render_template("subscription.html")

@app.route('/checkout/<int:amount>')
def checkout(amount):
    username = session.get('username')
    company = session.get('company')
    email = session.get('email')
    referral_code = session.get('referral_code')
    client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
    payment = client.order.create({'amount': int(amount*100), 'currency': 'INR', 'payment_capture': '1'})
    return render_template("altdash.html",
                           key=app.config['RAZORPAY_KEY_ID'],
                           payment=payment,
                           username=username,
                           company=company,
                           email=email,
                           referral_code = referral_code,
                           showPayModal=True)

@app.route('/payment', methods=['POST'])
def payment():
    payment_id = request.form['razorpay_payment_id']
    client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
    payment = client.payment.fetch(payment_id)
    # The payment was successful
    if payment.get('status') == 'captured':
        amount = int(payment['amount'])/100
        user_id = session.get('user_id')
        username = session.get('username')
        email = session.get('email')
        #Update your application database
        if add_subscription_to_user(user_id, amount,payment): 
          #send an email notification to the user
          msg = Message('FinCheck | Payment Successful', sender= os.environ.get('MAIL_USERNAME'), recipients=[email])
          msg.body = get_payment_success_msg(username,amount)
          mail.send(msg)
          flash('Payment Successful', 'success')
          return redirect("/dashboard/thismonth")
    else:
        # The payment failed or was cancelled
        flash('Payment Failed', 'danger')
        return redirect("/dashboard/thismonth")

          
#------------------------------- Dashboard -------------------------------

@app.route('/dashboard/<interval>')
def dashboard(interval="today"):
    # check if user is authenticated
    users = load_users()
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    referral_code = session.get('referral_code')
    subs_end = get_subs_end(users, user_id)
    session['subs_end'] = subs_end
    utc_now = datetime.datetime.now()
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    elif subs_end is None or subs_end < utc_now: #If user has not subscribed
        return render_template('altdash.html',
                               company=company,
                               username=username,
                               email=email,
                               subs_end=subs_end,
                               referral_code=referral_code, 
                               showModal=True)
    else:
      # user is authenticated, render dashboard page
      sales = load_sales(user_id)
      expenses = load_expenses(user_id)
      products = load_inventory(user_id)
      ledgers = load_ledgers(user_id)
      # Assigning interval dates
      start_date, end_date = get_interval_dates(interval, sales)
      #Extract Sales data for given interval
      interval_sales = extract_interval_data(sales, start_date, end_date)
      interval_expenses = extract_interval_data(expenses, start_date, end_date)
      #Gross Revenue and Gross Margin
      g_revenue , g_margin = get_grevenue_gmargin(interval_sales)
      if g_revenue != 0:
        perc_gmargin = "{:.2%}".format((g_margin/g_revenue))
      else:
        perc_gmargin = "{:.2%}".format(0)
      g_expenses = get_gexpenses(interval_expenses)
      #Net Revenue
      n_revenue = g_margin - g_expenses
      #Cost of Goods Sold
      cogs = get_cogs(products, interval_sales)
      #Inventory Cost
      inventory_cost = sum(product['pqty'] * product['pcp'] for product in products)
      #EBITDA i.e Earning before Interest, Taxes, Depreciation and Amortization
      if n_revenue != 0:
        ebitda = "{:.2%}".format((n_revenue/g_revenue))
      else:
        ebitda = 0
      #Revenue Projection and Profit Projection
      p_revenue, p_profit = predict_sales(sales, interval)
      #Monthly Sales Chart
      monthly_sales = group_sales_by_month(sales)
      monthly_sales_data = make_chart(monthly_sales, 'month', 'price')
      # For Daily Sales Chart
      daily_sales = add_sales_by_dates(interval_sales) #adding amount for same dates 
      daily_sales_data = make_chart(daily_sales, 'date', 'sale_amt')
      #For Expenses by Category Chart
      category_expenses = add_expenses_by_category(interval_expenses)
      category_expenses_data = make_chart(category_expenses, 'type', 'eprice')
      # For Daily Expenses Chart
      daily_expenses = add_expenses_by_dates(interval_expenses)
      daily_expenses_data = make_chart(daily_expenses, 'date', 'eprice')
      #For Unpaid Customers Chart
      unpaid_customers = get_unpaid_customers(sales)
      unpaid_customers_output = add_amt_unpaid_customers(unpaid_customers) 
      unpaid_customers_data = make_chart(unpaid_customers_output, 'customer', 'sale_amt')
      #For Wholesalers chart
      wholesaler_credits = get_latest_credits(ledgers)
      wholesalers_data = make_chart(wholesaler_credits, 'wname', 'credit')
      #Top Products
      top_products_qty, top_products_profit = top_products(sales)
      
      return render_template('dashboard.html',
                             company=company,
                             username=username,
                             email=email,
                             subs_end=subs_end,
                             referral_code=referral_code,
                             g_revenue=g_revenue,
                             g_margin=g_margin,
                             perc_gmargin=perc_gmargin,
                             g_expenses=g_expenses,
                             n_revenue=n_revenue,
                             cogs=cogs,
                             ebitda=ebitda,
                             p_revenue=p_revenue,
                             p_profit=p_profit,
                             inventory_cost=inventory_cost,
                             monthly_sales_data=monthly_sales_data,
                             daily_sales_data=daily_sales_data,
                             category_expenses_data=category_expenses_data,
                             daily_expenses_data=daily_expenses_data,
                             unpaid_customers_data=unpaid_customers_data,
                             wholesalers_data=wholesalers_data,
                             top_products_qty=top_products_qty,
                             top_products_profit=top_products_profit)

#------------------------------- Products -------------------------------
@app.route('/products')
def show_products():
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    subs_end = session.get('subs_end')
    referral_code = session.get('referral_code')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      products = load_inventory(user_id)
      #For chart
      data = make_chart(products, 'pname', 'pqty')
      return render_template('products.html',
                             company=company,
                             username=username,
                             subs_end=subs_end,
                             email=email,
                             referral_code=referral_code,
                             products=products,
                             data=data)

@app.route("/add_product", methods=["GET", "POST"])
def add_prod():
    user_id = session.get('user_id')
    if add_product(request.form["pname"],
                  request.form["pcp"],
                  request.form["psp"],
                  request.form["pqty"],
                  user_id):
      return redirect("/products")

@app.route("/products/<pid>/delete")
def del_prod(pid):
    if delete_product(pid):
      return redirect("/products")

@app.route("/products/update", methods=["GET", "POST"])
def mod_prod():
    if update_product(request.form.get('pname'),
                      request.form.get('pcp'),
                      request.form.get('psp'),
                      request.form.get('pqty')):
      return redirect('/products')

#------------------------------- Sales -------------------------------

@app.route('/sales/<interval>')
def show_sales(interval = "thisweek"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    subs_end = session.get('subs_end')
    referral_code = session.get('referral_code')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      sales = load_sales(user_id)
      products = load_inventory(user_id)
      # Assigning interval dates
      start_date, end_date = get_interval_dates(interval, sales)
      #Extract Sales data for given interval
      interval_sales = extract_interval_data(sales, start_date, end_date)
      #For chart
      output = add_sales_by_dates(interval_sales) #adding amount for same dates 
      data = make_chart(output, 'date', 'sale_amt')
      if len(products) == 0:
        return render_template('sales.html',
                               company=company,
                               username=username,
                               email=email,
                               subs_end=subs_end,
                               referral_code=referral_code,
                               products=products,
                               sales=sales,
                               data=data,
                               showModal=True)
      else:
        return render_template('sales.html',
                               company=company,
                               username=username,
                               email=email,
                               subs_end=subs_end,
                               referral_code=referral_code,
                               products=products,
                               sales=interval_sales,
                               data=data)

@app.route("/add_sale", methods=["GET", "POST"])
def add_sales():
    user_id = session.get('user_id')
    if add_sale(request.form["pname"],
                  request.form["qty"],
                  request.form["price"],
                  request.form["customer"],
                  request.form['status'],
                  user_id):
      return redirect("/sales/thisweek")

@app.route("/sales/<id>/delete")
def del_sales(id):
    user_id = session.get('user_id')
    products = load_inventory(user_id)
    product = request.args.get('product')
    sale_qty = request.args.get('sale_qty')
    print(product)
    new_qty = add_deleted_sale_qty_to_inventory(products, product, sale_qty)
    if delete_sale(id, product, new_qty):
      return redirect("/sales/thisweek")

@app.route("/sales/update", methods=["GET", "POST"])
def mod_sale():
    user_id = session.get('user_id')
    if update_sale(request.form.get('id'),
                request.form.get('date'),
                request.form.get('product'),
                request.form.get('sale_qty'),
                request.form.get('sale_price'),
                request.form.get('sale_amt'),
                request.form.get('sale_profit'),
                request.form.get('customer'),
                request.form.get('status'),
                user_id):
      return redirect("/sales/thisweek")

#------------------------------- Ledgers -------------------------------

@app.route('/ledgers/<interval>')
def show_ledgers(interval="today"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    subs_end = session.get('subs_end')
    referral_code = session.get('referral_code')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      ledgers = load_ledgers(user_id)
      wholesalers = load_wholesalers(user_id)
      result = get_latest_credits(ledgers)
      # Assigning interval dates
      start_date, end_date = get_interval_dates(interval, ledgers)
      #Extract ledger data for given interval
      interval_ledgers = extract_interval_data(ledgers, start_date, end_date)
      #For chart
      data = make_chart(result, 'wname', 'credit')
      if wholesalers==[]:
        return render_template('ledger.html',
                             company=company,
                             username=username,
                             email=email,
                             subs_end=subs_end,
                             referral_code=referral_code,
                             ledgers=interval_ledgers,
                             wholesalers=wholesalers,
                             data=data,
                             showModal=True)
      return render_template('ledger.html',
                             company=company,
                             username=username,
                             email=email,
                             subs_end=subs_end,
                             referral_code=referral_code,
                             ledgers=interval_ledgers,
                             wholesalers=wholesalers,
                             data=data)

@app.route("/add_ledger", methods=["GET", "POST"])
def add_led():
    user_id = session.get('user_id')
    if add_ledger(request.form["wname"],
                  request.form["credit"],
                  request.form["debit"],
                  user_id):
      return redirect("/ledgers/thisweek")

@app.route("/ledgers/<wid>/delete")
def del_led(wid):
    if delete_ledger(wid):
      return redirect("/ledgers/thisweek")  

@app.route("/ledgers/update", methods=["GET", "POST"])
def mod_led():
    if update_ledger(request.form.get('wid'),
                      request.form.get('wname'),
                      request.form.get('date'),
                      request.form.get('credit'),
                      request.form.get('debit')):
      return redirect('/ledgers/thisweek')

#------------------------------- Wholesalers -------------------------------

@app.route('/wholesalers')
def show_wholesalers():
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    subs_end = session.get('subs_end')
    referral_code = session.get('referral_code')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      ledgers = load_ledgers(user_id)
      wholesalers = load_wholesalers(user_id)
      result = get_latest_credits(ledgers)
      #For chart
      data = make_chart(result, 'wname', 'credit')
      return render_template('wholesalers.html',
                             company=company,
                             username=username,
                             email=email,
                             subs_end=subs_end,
                             referral_code=referral_code,
                             ledgers=ledgers,
                             wholesalers=wholesalers,
                             data=data)

@app.route("/add_wholesaler", methods=["GET", "POST"])
def add_wsaler():
    user_id = session.get('user_id')
    if add_wholesaler(request.form["wname"],
                  request.form["wcontact"],
                  request.form["waddress"],
                  user_id):
      return redirect("/wholesalers")

@app.route("/wholesalers/<wid>/delete")
def del_ws(wid):
    if delete_wholesaler(wid):
      return redirect("/wholesalers")  

@app.route("/wholesalers/update", methods=["GET", "POST"])
def mod_ws():
    if update_wholesaler(request.form.get('wid'),
                      request.form.get('wname'),
                      request.form.get('wcontact'),
                      request.form.get('waddress'),
                      request.form.get('onboarded')):
      return redirect('/wholesalers')

#------------------------------- Expenses -------------------------------

@app.route('/expenses/<interval>')
def show_expenses(interval = "thisweek"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    subs_end = session.get('subs_end')
    referral_code = session.get('referral_code')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      expenses = load_expenses(user_id)
      # Assigning interval dates
      start_date, end_date = get_interval_dates(interval, expenses)
      #Extract expenses data for given interval
      interval_expenses = extract_interval_data(expenses, start_date, end_date)
      output = add_expenses_by_dates(interval_expenses)
      data = make_chart(output, 'date', 'eprice')
      return render_template('expenses.html',
                              company=company,
                              username=username,
                              email=email,
                              subs_end=subs_end,
                              referral_code=referral_code,
                              expenses=interval_expenses,
                              data=data)

@app.route("/add_expense", methods=["GET", "POST"])
def add_ex():
    user_id = session.get('user_id')
    if add_expense(request.form["type"],
                  request.form["eprice"],
                  user_id):
      return redirect("/expenses/thisweek")

@app.route("/expenses/<id>/delete")
def del_ex(id):
    if delete_expense(id):
      return redirect("/expenses/thisweek") 

@app.route("/expenses/update", methods=["GET", "POST"])
def mod_expense():
    if update_expense(request.form.get('id'),
                      request.form.get('date'),
                      request.form.get('type'),
                      request.form.get('eprice')):
      return redirect('/expenses/thisweek')

#------------------------------- Customers -------------------------------
@app.route('/customers')
def show_customers():
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    subs_end = session.get('subs_end')
    referral_code = session.get('referral_code')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      sales = load_sales(user_id)
      unpaid_customers = get_unpaid_customers(sales)
      #For chart
      output = add_amt_unpaid_customers(unpaid_customers) #adding amount for same dates 
      data = make_chart(output, 'customer', 'sale_amt')
      return render_template('customers.html',
                             company=company,
                             username=username,
                             email=email,
                             subs_end=subs_end,
                             referral_code=referral_code,
                             unpaid_customers=unpaid_customers,
                             data=data)

#------------------------------- Replacements -------------------------------
@app.route('/replacements/<interval>')
def show_replacements(interval="today"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    email = session.get('email')
    subs_end = session.get('subs_end')
    referral_code = session.get('referral_code')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      replacements = load_replacements(user_id)
      products = load_inventory(user_id)
      # Assigning interval dates
      start_date, end_date = get_interval_dates(interval, replacements)
      #Extract expenses data for given interval
      interval_replacements = extract_interval_data(replacements, start_date, end_date)
      #For chart
      data = make_chart(replacements, 'pname', 'qty')
      if products==[]:
        return render_template('replacements.html',
                             company=company,
                             username=username,
                             email=email,
                             subs_end=subs_end,
                             referral_code=referral_code,
                             products=products,
                             replacements=interval_replacements,
                             data=data,
                             showModal=True)
      return render_template('replacements.html',
                             company=company,
                             username=username,
                             email=email,
                             subs_end=subs_end,
                             referral_code=referral_code,
                             products=products,
                             replacements=interval_replacements,
                             data=data)

@app.route("/add_replacement", methods=["GET", "POST"])
def add_repl():
    user_id = session.get('user_id')
    if add_replacement(request.form["pname"],
                  request.form["qty"],
                  user_id):
      return redirect("/replacements/thisweek")

@app.route("/replacements/<rid>/delete")
def del_repl(rid):
    if delete_replacement(rid):
      return redirect("/replacements/thisweek")

@app.route("/replacements/update", methods=["GET", "POST"])
def mod_repl():
    user_id = session.get('user_id')
    if update_replacement(request.form.get('pname'), 
                          request.form.get('qty'), 
                          user_id):
      return redirect('/replacements/thisweek')
      
@app.route("/terms")
def terms():
    return render_template("tnc.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")
  
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
