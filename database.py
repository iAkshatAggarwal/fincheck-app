import os
import datetime
from sqlalchemy import create_engine, text
from utils import get_cp, get_pqty, calc_updated_sales

host = os.environ["HOST"]
username =os.environ["USERNAME"]
password = os.environ["PASSWORD"]
database = os.environ["DATABASE"]
  
conn_string = f"mysql+pymysql://{username}:{password}@{host}/{database}"

engine = create_engine(conn_string, connect_args = {
  "ssl":{
    "ssl_ca": "/etc/ssl/cert.pem"
  }
})

def add_user(uname, upass, company, email, referral_code):
  with engine.connect() as conn:
    query = text("INSERT INTO users(uname, upass, company, email, referral_code) VALUES (:uname, :upass, :company, :email, :referral_code)")
    conn.execute(query,
                 {
                  'uname': uname, 
                  'upass': upass, 
                  'company': company,
                  'email': email,
                  'onboarded': datetime.datetime.now(),
                  'referral_code': referral_code
                 }
    )
    return True

def change_password(uid, upass):
  with engine.connect() as conn:
    query = text("UPDATE users SET upass= :upass where uid= :uid")
    conn.execute(query,
                 { 
                  'uid': uid, 
                  'upass': upass
                 }
    )
    return True

def update_email_address(uid, email):
  with engine.connect() as conn:
    query = text("UPDATE users SET email= :email where uid= :uid")
    conn.execute(query,
                 { 
                  'uid': uid, 
                  'email': email
                 }
    )
    return True

def add_subscription_to_user(uid, amount, payment_id):
  with engine.connect() as conn:
    subs_start = datetime.datetime.utcnow()
    subs_end = datetime.datetime.utcnow()
    if amount == 699:
      subs_end = subs_start + datetime.timedelta(days=28)
      subscription = 'monthly'
    elif amount == 1999:
      subs_end = subs_start + datetime.timedelta(days=84)
      subscription = 'quarterly'
    elif amount == 7999:
      subs_end = subs_start + datetime.timedelta(days=365)
      subscription = 'yearly'
    query = text("UPDATE users SET subs_start =:subs_start, subs_end =:subs_end, subscription =:subscription WHERE uid = :uid")
    conn.execute(query,
                 {
                  'uid': uid, 
                  'subs_start': subs_start, 
                  'subs_end': subs_end,
                  'subscription': subscription,
                  'payment_id': payment_id
                 }
    )
    return True

def load_users():
  with engine.connect() as conn:
    result = conn.execute(text("SELECT * from users"))
    users = []
    for row in result.fetchall():
        row_dict = dict(zip(result.keys(), row))
        users.append(row_dict)
    return users
    
def load_inventory(uid):
  with engine.connect() as conn:
    query = text("SELECT * from product WHERE uid = :uid")
    result = conn.execute(query, {'uid': uid})
    products = []
    for row in result.fetchall():
        row_dict = dict(zip(result.keys(), row))
        products.append(row_dict)
    return products

def load_sales(uid):
  with engine.connect() as conn:
    query = text("SELECT * from sales WHERE uid = :uid ORDER BY date DESC")
    result = conn.execute(query, {'uid': uid})
    sales = []
    for row in result.fetchall():
        row_dic = dict(zip(result.keys(), row))
        sales.append(row_dic)
    return sales

def load_wholesalers(uid):
  with engine.connect() as conn:
    query = text("SELECT * from wholesalers WHERE uid = :uid")
    result = conn.execute(query, {'uid': uid})
    wholesalers = []
    for row in result.fetchall():
        row_dic = dict(zip(result.keys(), row))
        wholesalers.append(row_dic)
    return wholesalers

def load_ledgers(uid):
  with engine.connect() as conn:
    query = text("SELECT * from ledger WHERE uid = :uid ORDER BY date DESC")
    result = conn.execute(query, {'uid': uid})
    ledgers = []
    for row in result.fetchall():
        row_dic = dict(zip(result.keys(), row))
        ledgers.append(row_dic)
    return ledgers

def load_expenses(uid):
  with engine.connect() as conn:
    query = text("SELECT * from expenses WHERE uid = :uid ORDER BY date DESC")
    result = conn.execute(query, {'uid': uid})
    expenses = []
    for row in result.fetchall():
        row_dic = dict(zip(result.keys(), row))
        expenses.append(row_dic)
    return expenses

def load_replacements(uid):
  with engine.connect() as conn:
    query = text("SELECT * from replacements WHERE uid = :uid ORDER BY date DESC")
    result = conn.execute(query, {'uid': uid})
    replacements = []
    for row in result.fetchall():
        row_dic = dict(zip(result.keys(), row))
        replacements.append(row_dic)
    return replacements

#------------------------------- Products -------------------------------
def add_product(pname, pcp, psp, pqty, uid):
  with engine.connect() as conn:
    query = text("INSERT INTO product(pname, pcp, psp, pqty, uid) VALUES (:pname, :pcp, :psp, :pqty, :uid)")
    conn.execute(query,
                 {'pname': pname,
                  'pcp': pcp,
                  'psp': psp,
                  'pqty': pqty,
                  'uid': uid
                 }
    )
    return True

def delete_product(id):
  with engine.connect() as conn:
    conn.execute(text("DELETE FROM product WHERE pid = :val"), {'val': id})
    return True

def update_product(pid, pname, pcp, psp, pqty):
  with engine.connect() as conn:
    query = (text("UPDATE product SET pname =:pname, pcp =:pcp, psp =:psp, pqty =:pqty WHERE pid = :pid"))
    conn.execute(query,
                 {
                  'pid': pid,
                  'pname': pname, 
                  'pcp': pcp, 
                  'psp': psp, 
                  'pqty': pqty
                 }
    )
    return True
    
#------------------------------- Sales -------------------------------

def add_sale(pname, qty, price, customer, status, uid):
  with engine.connect() as conn:
    #to get cp
    products = load_inventory(uid)
    amount = int(qty) * int(price)
    cp = get_cp(products, pname)
    new_qty = get_pqty(products, pname) - int(qty) #updated qty of inventory
    profit = amount - (int(qty) * int(cp))
    if customer == "" and status == "Paid":
      customer = "CASH"
    query= text("INSERT INTO sales(product, date, sale_qty, sale_price, sale_amt, sale_profit,  customer, status, uid) VALUES (:product, :date, :sale_qty, :sale_price, :sale_amt, :sale_profit, :customer, :status, :uid)")
    conn.execute(query,
                 {
                  'product': pname, 
                  'date': datetime.datetime.now(), 
                  'sale_qty': qty, 
                  'sale_price': price,
                  'sale_amt': amount,
                  'sale_profit': profit,
                  'customer': customer,
                  'status': status,
                  'uid': uid
                 }
    )
    query2 = text("UPDATE product SET pqty = :pqty  WHERE pname = :pname")
    conn.execute(query2,
                {
                  'pqty': new_qty,
                  'pname': pname
                }
    )
    return True

def delete_sale(id, pname, pqty):
  with engine.connect() as conn:
    # To update qty in inventory or product table
    conn.execute(text("UPDATE product SET pqty = :pqty  WHERE pname = :pname"), {'pqty': pqty, 'pname': pname})
    # To delete sale from sales table
    conn.execute(text("DELETE FROM sales WHERE id = :val"), {'val': id})
    return True

def update_sale(id, date, product, sale_qty, 
                sale_price, sale_amt, sale_profit, customer, status, uid):
  with engine.connect() as conn:
    sales = load_sales(uid)
    products = load_inventory(uid)
    sale_amt, sale_profit, pname, pqty = calc_updated_sales(id, sales, sale_price, sale_amt, sale_profit, products, product, sale_qty)
    # To update qty in inventory or product table
    query1 = text("UPDATE product SET pqty = :pqty  WHERE pname=:pname AND uid=:uid")
    conn.execute(query1,
                  {
                    'pqty': pqty,
                    'pname': pname,
                    'uid':uid
                  }
    )
    # Updating Sales 
    query2 = (text("UPDATE sales SET id = :id, date = :date, product = :product, sale_qty = :sale_qty, sale_price = :sale_price, sale_amt = :sale_amt, sale_profit = :sale_profit, customer =:customer, status = :status WHERE id = :id AND uid = :uid"))
    conn.execute(query2,
                 {
                  'id': id,
                  'date': date, 
                  'product': product, 
                  'sale_qty': sale_qty, 
                  'sale_price': sale_price,
                  'sale_amt': sale_amt,
                  'sale_profit': sale_profit,
                  'customer': customer,
                  'status': status,
                  'uid': uid
                 }
    )
    return True

#------------------------------- Wholesalers -------------------------------

def add_wholesaler(wname, wcontact, waddress, uid):
  with engine.connect() as conn:
    query = text("INSERT INTO wholesalers(wname, wcontact, waddress, onboarded, uid) VALUES (:wname, :wcontact, :waddress, :onboarded, :uid)")
    conn.execute(query,
                 {'wname': wname,
                  'wcontact': wcontact,
                  'waddress': waddress,
                  'onboarded': datetime.datetime.now(),
                  'uid': uid
                 }
    )
    return True

def delete_wholesaler(id):
  with engine.connect() as conn:
    conn.execute(text("DELETE FROM wholesalers WHERE wid = :val"), {'val': id})
    return True

def update_wholesaler(wid, wname, wcontact, waddress, onboarded):
  with engine.connect() as conn:
    query = (text("UPDATE wholesalers SET wname =:wname, wcontact =:wcontact, waddress =:waddress, onboarded =:onboarded WHERE wid = :wid"))
    conn.execute(query,
                 {
                  'wid': wid, 
                  'wname': wname, 
                  'wcontact': wcontact, 
                  'waddress': waddress, 
                  'onboarded': onboarded
                 }
    )
    return True
    
#------------------------------- Ledgers -------------------------------

def add_ledger(wname, credit, debit, uid):
  with engine.connect() as conn:
    ledgers = load_ledgers(uid)
    ledger_subset = [ledger for ledger in ledgers if ledger['wname'] == wname]
    if len(ledger_subset) > 0:
        latest_ledger = sorted(ledger_subset, key=lambda x: x['date'])[-1]
        credit = latest_ledger['credit']
        credit -= int(debit)
    for ledger in ledgers:
      if ledger['wname'] != wname and credit == "":
        credit = 0
    if debit == "":
      debit = 0
    
    query = text("INSERT INTO ledger(wname, date, credit, debit, uid) VALUES (:wname, :date, :credit, :debit, :uid)")
    conn.execute(query,
                 {
                  'wname': wname, 
                  'date': datetime.datetime.now(), 
                  'credit': credit, 
                  'debit': debit,
                  'uid': uid
                 }
    )
    return True

def delete_ledger(id):
  with engine.connect() as conn:
    conn.execute(text("DELETE FROM ledger WHERE wid = :val"), {'val': id})
    return True

def update_ledger(wid, wname, date, credit, debit):
  with engine.connect() as conn:
    if credit == "":
      credit = 0
    elif debit == "":
      debit = 0
    query = (text("UPDATE ledger SET wname =:wname, date =:date, credit =:credit, debit =:debit WHERE wid = :wid"))
    conn.execute(query,
                 {
                  'wid': wid, 
                  'wname': wname, 
                  'date': date, 
                  'credit': credit, 
                  'debit': debit
                 }
    )
    return True

#------------------------------- Expenses -------------------------------

def add_expense(type, eprice, uid):
  with engine.connect() as conn:
    query = text("INSERT INTO expenses(type, eprice, date, uid) VALUES (:type, :eprice, :date, :uid)")
    conn.execute(query,
                 {
                  'type': type, 
                  'eprice': eprice, 
                  'date': datetime.datetime.now(),
                  'uid': uid
                 }
    )
    return True

def delete_expense(id):
  with engine.connect() as conn:
    conn.execute(text("DELETE FROM expenses WHERE id = :val"), {'val': id})
    return True

def update_expense(id, date, type, eprice):
  with engine.connect() as conn:
    query = (text("UPDATE expenses SET date =:date, type =:type, eprice =:eprice WHERE id = :id"))
    conn.execute(query,
                 {
                  'id': id, 
                  'date': date, 
                  'type': type, 
                  'eprice': eprice
                 }
    )
    return True

#------------------------------- Replacements -------------------------------

def add_replacement(pname, qty, uid):
  with engine.connect() as conn:
    #to get cp
    products = load_inventory(uid)
    cp = get_cp(products, pname)
    amt = int(qty) * int(cp)
    query = text("INSERT INTO replacements(date, pname, qty, amt, uid) VALUES (:date, :pname, :qty, :amt, :uid)")
    conn.execute(query,
                 {
                  'date': datetime.datetime.now(),
                  'pname': pname,
                  'qty': qty,
                  'amt': amt,
                  'uid': uid
                 }
    )
    return True

def delete_replacement(id):
  with engine.connect() as conn:
    conn.execute(text("DELETE FROM replacements WHERE rid = :val"), {'val': id})
    return True

def update_replacement(pname, qty, uid):
  with engine.connect() as conn:
    #To update amount
    products = load_inventory(uid)
    cp = get_cp(products, pname)
    amt = int(qty) * int(cp)
    query = (text("UPDATE replacements SET qty =:qty, amt=:amt WHERE pname = :pname"))
    conn.execute(query,
                 {
                  'pname': pname,
                  'qty': qty,
                  'amt': amt
                 }
    )
    return True