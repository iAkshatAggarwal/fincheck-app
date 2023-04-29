from datetime import datetime, date, timedelta
from sklearn.linear_model import LinearRegression
import pandas as pd
import uuid

def get_referral_code():
    return str(uuid.uuid4().hex)[:10]

def authenticate_user(users, username, password):
  for user in users:
    # users is a list of dictionary
    if user['uname'] == username and user['upass'] == password:
      return user['uid'], user['company'], user['uname'], user['email'],  user['referral_code']
  return None, None, None, None, None

def check_existing_user(users, username, email):
  for user in users:
    if user['uname'] == username or user['email'] == email:
      return False
  return True

def get_pass_from_uid(users, uid):
  for user in users:
    if user['uid'] == uid:
      return user["upass"]

def get_subs_end(users, uid):
  for user in users:
    if user['uid'] == uid:
      return user['subs_end']

def get_interval_dates(interval, datas):
  end_date =  date.today()
  start_date = date.today()
  if interval == 'thisweek':
    start_date = end_date - timedelta(days=7)
  elif interval == 'thismonth':
    start_date =  end_date.replace(day=1) - timedelta(days=1)
  elif interval == 'thisquarter':
    month = end_date.month - 3 if end_date.month > 3 else end_date.month + 9
    start_date = date(end_date.year, month, 1) - timedelta(days=1)
  elif interval == 'thisyear':
        start_date = date(end_date.year, 1, 1)
  elif interval == 'alltime':
    start_date = min(data['date'] for data in datas)
  return start_date, end_date

def extract_interval_data(data_list, start_date, end_date):
    extracted_data = []
    for data in data_list:
        if isinstance(data["date"], datetime):
          if start_date <= data["date"].date() <= end_date:
              extracted_data.append(data)
        else:
          if start_date <= data["date"] <= end_date:
              extracted_data.append(data)
    return extracted_data
  
def get_future_date(interval):
    end_date = date.today()
    if interval == 'thisweek':
        start_date = end_date + timedelta(days=1)
        end_date = end_date + timedelta(days=7)
    elif interval == 'thismonth':
        start_date = end_date.replace(day=1) + timedelta(days=1)
        end_date = end_date.replace(day=28) + timedelta(days=4)
    elif interval == 'thisquarter':
        month = end_date.month + 3 if end_date.month <= 9 else end_date.month - 9
        start_date = date(end_date.year, month, 1) + timedelta(days=1)
        end_date = start_date + timedelta(days=89)
    elif interval == 'thisyear':
        start_date = end_date.replace(month=1, day=1) + timedelta(days=1)
        end_date = end_date.replace(month=12, day=31)
    return end_date

def make_chart(table, x, y):
  labels=[]
  values=[]
  for row in table:
    labels.append(row[x])
    values.append(row[y])
  data = {'labels':labels, 'values':values}
  return data

def get_grevenue_gmargin(sales):
  gross_revenue = 0
  gross_profit = 0
  for sale in sales:
    gross_revenue += sale['sale_amt']
    gross_profit += sale['sale_profit']
  return gross_revenue, gross_profit   

def get_gexpenses(expenses):
  gross_expenses = 0
  for expense in expenses:
    gross_expenses += expense['eprice']
  return gross_expenses

def add_sales_by_dates(sales):
  date_sums = {}
  for sale in sales: #Sum up the prices for each date
    if sale['date'] in date_sums:
      date_sums[sale['date']] += sale['sale_amt']
    else:
      date_sums[sale['date']] = sale['sale_amt']
    #New list of dictionaries with the summed prices for each date
  output = [{'date': date.strftime("%d/%m/%Y"), 'sale_amt': sale_amt} for date, sale_amt in date_sums.items()]
  return output

def get_cogs(products, sales):
  cogs = 0
  for product in products:
    for sale in sales:
      if sale["product"] == product['pname']:
        cogs += sale["sale_qty"] * product["pcp"]
  return cogs

def add_expenses_by_dates(expenses):
  date_sums = {}
  for expense in expenses: #Sum up the prices for each date
    if expense['date'] in date_sums:
      date_sums[expense['date']] += expense['eprice']
    else:
      date_sums[expense['date']] = expense['eprice']
    #New list of dictionaries with the summed prices for each date
  output = [{'date': date.strftime("%d/%m/%Y"), 'eprice': eprice} for date, eprice in date_sums.items()]
  return output

def add_expenses_by_category(expenses):
  date_sums = {}
  for expense in expenses: #Sum up the prices for each category
    if expense['type'] in date_sums:
      date_sums[expense['type']] += expense['eprice']
    else:
      date_sums[expense['type']] = expense['eprice']
    #New list of dictionaries with the summed prices for each category
  output = [{'type': type, 'eprice': eprice} for type, eprice in date_sums.items()]
  return output

def group_sales_by_month(sales):
  sales_by_month = {}
  for sale in sales:
      date = sale['date']
      month = date.strftime('%Y-%m')
      if month in sales_by_month:
          sales_by_month[month]['price'] += sale['sale_amt']
      else:
          sales_by_month[month] = {
              'month': month,
              'price': sale['sale_amt']
          }
  return list(sales_by_month.values())

def get_cp(products, pname):
    for product in products:
        if product["pname"] == pname:
            return product["pcp"]
    return None

def get_pqty(products, pname):
    for product in products:
        if product["pname"] == pname:
            return product["pqty"]
    return None

def calc_updated_sales(id, sales, sale_price, sale_amt, sale_profit, products, product, sale_qty):
  cp = get_cp(products, product)
  for sale in sales: # To update new amount and profit
    if str(sale["id"]) == str(id):
      sale_amt = float(sale_price) * float(sale_qty)
      sale_profit = float(sale_amt) - (float(sale_qty) * float(cp))
      for prod in products: # To update qty in inventory
        if str(prod["pname"]) == str(product):
          pname = prod["pname"] 
          pqty = prod["pqty"]
          if int(sale_qty) > int(sale["sale_qty"]):
            pqty -= (int(sale_qty)- int(sale["sale_qty"]))
          elif int(sale_qty) < int(sale["sale_qty"]):
            pqty += (int(sale["sale_qty"]) - int(sale_qty))
  return sale_amt, sale_profit, pname, pqty

def top_products(sales):
    # Create a dictionary to store the quantity and profit for each product
    product_dict = {}

    # Loop through each sale and update the product dictionary
    for sale in sales:
        name = sale['product']
        qty = sale['sale_qty']
        profit = sale['sale_profit']

        # If the product is already in the dictionary, add the quantity and profit
        if name in product_dict:
            product_dict[name]['qty'] += qty
            product_dict[name]['profit'] += profit
        # If the product is not in the dictionary, add it with the quantity and profit
        else:
            product_dict[name] = {'name': name, 'qty': qty, 'profit': profit}

    # Sort the products by quantity and profit in descending order and take the top 10
    sorted_products_qty = sorted(list(product_dict.values()), key=lambda x: (-x['qty'], -x['profit']))[:10]
    sorted_products_profit = sorted(list(product_dict.values()), key=lambda x: (-x['profit'], -x['qty']))[:10]

    # Return separate lists of dictionaries for the top products by quantity and profit
    return (sorted_products_qty, sorted_products_profit)

def add_deleted_sale_qty_to_inventory(products, product, sale_qty):
    for prod in products: # To update qty in inventory
      if str(prod["pname"]) == str(product):
        pqty = int(prod["pqty"])
        pqty += int(sale_qty)
        break
    return pqty

def get_unpaid_customers(sales):
    unpaid_customers = []
    for sale in sales:
      if sale['status'] == 'Unpaid':
        unpaid_customers.append(
          {
            'customer': sale['customer'], 
            'date': sale['date'],
            'product': sale['product'],
            'sale_qty': sale['sale_qty'],
            'sale_amt': sale['sale_amt']
          }
        )   
    return unpaid_customers

def add_amt_unpaid_customers(sales):
  date_sums = {}
  for sale in sales: #Sum up the amount for each customer
    if sale['customer'] in date_sums:
      date_sums[sale['customer']] += sale['sale_amt']
    else:
      date_sums[sale['customer']] = sale['sale_amt']
    #New list of dictionaries with the summed prices for each date
  output = [{'customer': customer, 'sale_amt': sale_amt} for customer, sale_amt in date_sums.items()]
  return output

def get_latest_credits(ledgers):
    result = {}
    for ledger in sorted(ledgers, key=lambda x: x['date'], reverse=True):
        wname, credit = ledger['wname'], ledger['credit']
        if wname not in result:
            result[wname] = credit
    return [{'wname': k, 'credit': v} for k, v in result.items()]
        
# ------------------------------ Revenue Prediction ------------------------------

def predict_sales(previous_sales_data, interval):
    if len(previous_sales_data) == 0:
      return 0,0

    # Convert the previous sales data to a Pandas dataframe
    sales_df = pd.DataFrame(previous_sales_data)
    predict_date = get_future_date(interval)

    # Convert the sale_date column to datetime object
    sales_df['date'] = pd.to_datetime(sales_df['date'])

    # Group the sales data by date and calculate the total sale amount for each day
    sale_amt_df = sales_df.groupby('date')['sale_amt'].sum().reset_index()

    # Split the date into year, month and day for easier analysis
    sale_amt_df['year'] = sale_amt_df['date'].dt.year
    sale_amt_df['month'] = sale_amt_df['date'].dt.month
    sale_amt_df['day'] = sale_amt_df['date'].dt.day

    # Create a linear regression model to predict future sales
    X = sale_amt_df[['year', 'month', 'day']]
    y = sale_amt_df['sale_amt']
    model = LinearRegression()
    model.fit(X, y)

    # Create a dataframe with dates up to the predict_date
    date_range = pd.date_range(start=sale_amt_df['date'].min(), end=predict_date, freq='D')
    future_sales_df = pd.DataFrame({'date': date_range})
    future_sales_df['year'] = future_sales_df['date'].dt.year
    future_sales_df['month'] = future_sales_df['date'].dt.month
    future_sales_df['day'] = future_sales_df['date'].dt.day

    # Predict sales for each date up to the predict_date
    future_sales_df['predicted_sales'] = model.predict(future_sales_df[['year', 'month', 'day']])

    # Calculate the predicted revenue and profit for each date up to the predict_date
    avg_profit_margin = sales_df['sale_profit'].mean() / sales_df['sale_amt'].mean()
    future_sales_df['predicted_revenue'] = future_sales_df['predicted_sales'].cumsum()
    future_sales_df['predicted_profit'] = future_sales_df['predicted_revenue'] * avg_profit_margin

    # Calculate the total predicted revenue and profit up to the predict_date
    predict_date = pd.to_datetime(predict_date) # Convert predict_date to a Pandas datetime object
    filtered_sales_df = future_sales_df[future_sales_df['date'] <= predict_date]
    total_predicted_revenue = round(filtered_sales_df.iloc[-1]['predicted_revenue'],2)
    total_predicted_profit = round(filtered_sales_df.iloc[-1]['predicted_profit'],2)

    # Calculate the stock maintenance for each product based on the predicted sales
    products = sales_df['product'].unique()
    stock_maintenance = {}
    for product in products:
        product_sales = sales_df[sales_df['product'] == product]
        avg_sale_qty = product_sales['sale_qty'].mean()
        avg_sale_profit = product_sales['sale_profit'].mean()
        avg_sale_amt = product_sales['sale_amt'].mean()
        predicted_sale_qty = filtered_sales_df['predicted_sales'].mean() / avg_sale_amt * avg_sale_qty
        predicted_sale_profit = predicted_sale_qty * avg_sale_profit
        stock_maintenance[product] = {
            'predicted_sale_qty': predicted_sale_qty,
            'predicted_sale_profit': predicted_sale_profit
        }
  
    return total_predicted_revenue, total_predicted_profit
