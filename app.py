import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from utils import authenticate_user, check_existing_user, get_pass_from_uid, get_interval_dates, make_chart, add_sales_by_dates , get_cogs, get_grevenue_gmargin, get_gexpenses, add_expenses_by_dates, add_expenses_by_category, group_sales_by_month, top_products, extract_interval_data, add_deleted_sale_qty_to_inventory, predict_sales, get_unpaid_customers, add_amt_unpaid_customers, get_latest_credits
from database import add_user, change_password, load_users, load_inventory, load_sales, load_wholesalers, load_ledgers, load_expenses, load_replacements, add_product, delete_product, update_product, add_wholesaler, add_ledger, delete_ledger, update_ledger, add_sale, delete_sale, update_sale, add_expense, delete_expense, update_expense, add_replacement, delete_replacement, update_replacement

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST": 
        users = load_users()
        user_id, company, username = authenticate_user(users, 
                                      request.form["username"], 
                                      request.form["password"])
        if user_id is None: 
            return render_template('login.html', login_error = True)
        else:
            session['user_id'] = user_id
            session['company'] = company
            session['username'] = username
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
      if check_existing_user(users, request.form["username"], request.form["company"]):
        if add_user(request.form["username"], 
                    request.form["password"],
                    request.form["company"],
                    request.form["email"]):
            return redirect("/login")

      else:
        flash('The username you entered already exists! Try again', 'danger')
        redirect(url_for('register'))
                       
    # If request.method = "GET"
    return render_template('register.html')

@app.route('/change-password', methods=["POST"])
def change_pass():
    if request.method == "POST": 
      users = load_users()
      user_id = session.get('user_id')
      if request.form["old-pass"] == get_pass_from_uid(users, user_id) and request.form["new-pass"] == request.form["re-new-pass"]:
        if change_password(user_id, request.form["new-pass"]):
          flash('Password changed successfully', 'success')
          return redirect("/dashboard/thismonth")
      else:
          flash('Password change failed. Please try again', 'danger')
          return redirect("/dashboard/thismonth")

@app.route('/plans')
def plans():
    return render_template("subscription.html")
          
#------------------------------- Dashboard -------------------------------

@app.route('/dashboard/<interval>')
def dashboard(interval="today"):
    # check if user is authenticated
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      # user is authenticated, render dashboard page
      sales = load_sales(user_id)
      expenses = load_expenses(user_id)
      products = load_inventory(user_id)
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
      #Top Products
      top_products_qty, top_products_profit = top_products(sales)
      
      return render_template('dashboard.html',
                             company=company,
                             username=username,
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
                             top_products_qty=top_products_qty,
                             top_products_profit=top_products_profit)

#------------------------------- Products -------------------------------
@app.route('/products')
def show_products():
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
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

#------------------------------- Ledgers -------------------------------

@app.route('/ledgers/<interval>')
def show_ledgers(interval="today"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
    if user_id is None:
        # user is not authenticated, redirect to login page
        return redirect(url_for('login'))
    else:
      ledgers = load_ledgers(user_id)
      wholesalers = load_wholesalers(user_id)
      result = get_latest_credits(ledgers)
      # Assigning interval dates
      start_date, end_date = get_interval_dates(interval, ledgers)
      #Extract expenses data for given interval
      interval_ledgers = extract_interval_data(ledgers, start_date, end_date)
      #For chart
      data = make_chart(result, 'wname', 'credit')
      return render_template('ledger.html',
                             company=company,
                             username=username,
                             ledgers=interval_ledgers,
                             wholesalers=wholesalers,
                             data=data)

@app.route("/add_wholesaler", methods=["GET", "POST"])
def add_wsaler():
    user_id = session.get('user_id')
    if add_wholesaler(request.form["wname"],
                  request.form["wcontact"],
                  request.form["waddress"],
                  user_id):
      return redirect("/ledgers/thisweek")

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

#------------------------------- Sales -------------------------------

@app.route('/sales/<interval>')
def show_sales(interval = "thisweek"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
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
      return render_template('sales.html',
                             company=company,
                             username=username,
                             products = products,
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

#------------------------------- Expenses -------------------------------
@app.route('/expenses/<interval>')
def show_expenses(interval = "thisweek"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
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
                             unpaid_customers=unpaid_customers,
                             data=data)

#------------------------------- Replacements -------------------------------
@app.route('/replacements/<interval>')
def show_replacements(interval="today"):
    user_id = session.get('user_id')
    company = session.get('company')
    username = session.get('username')
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
      return render_template('replacements.html',
                             company=company,
                             username=username,
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
      

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
