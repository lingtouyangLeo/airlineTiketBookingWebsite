import datetime
import re
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '114514'

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='DB_Project',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


@app.route('/')
def hello():
    error = request.args.get('error')
    return render_template('index.html', error=error)


@app.route('/view_flights/flight', methods=['POST'])
def view_flights_flight():
    depart_city = request.form['depart_city']
    arrival_city = request.form['arrival_city']
    depart_date = request.form['depart_date']
    print(depart_city)
    print(arrival_city)
    print(depart_date)
    cursor = conn.cursor()
    q = '''SELECT airline_name, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price, status, airplane_id \
                FROM flight, airport AS a1, airport AS a2\
                WHERE status = 'Upcoming' \
                AND a1.airport_name = departure_airport AND a2.airport_name = arrival_airport \
                AND (departure_airport = "{}" OR a1.airport_city = "{}") \
                AND (arrival_airport = "{}" OR a2.airport_city = "{}") AND DATE(departure_time) = "{}"'''.format(depart_city, depart_city, arrival_city, arrival_city, depart_date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)
    error = None
    if (data):
        return render_template('view_flights_flight.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('hello', error=error))


@app.route('/view_flights/status', methods=['POST'])
def view_flights_status():
    flight_num = request.form['flight_num']
    date = request.form['date']
    print(flight_num)
    print(date)
    cursor = conn.cursor()
    q = 'SELECT airline_name, flight_num, status, departure_time, arrival_time FROM flight\
        WHERE flight_num = {} \
        AND (DATE(departure_time) = "{}" OR DATE(arrival_time) = "{}" )'.format(flight_num, date, date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)

    error = None
    if (data):
        return render_template('view_flights_status.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('hello', error=error))


@app.route('/login')
def login():
    return render_template('login.html')


def check_permission(username):
    cursor = conn.cursor()
    q = "SELECT * FROM `permission` WHERE username = '%s' and permission_type = 'admin'"
    cursor.execute(q % username)
    data = cursor.fetchone()
    cursor.close()
    print(data)
    return bool(data)


def check_operator(username):
    cursor = conn.cursor()
    q = "SELECT * FROM `permission` WHERE username = '%s' and permission_type = 'Operator'"
    cursor.execute(q % username)
    data = cursor.fetchone()
    cursor.close()
    print(data)
    return bool(data)


@app.route('/login_authenticate', methods=['GET', 'POST'])
def login_authenticate():
    username = request.form['username']
    password = request.form['password']
    usertype = request.form['usertype']
    print(usertype)
    cursor = conn.cursor()
    if usertype == 'customer':
        q = 'SELECT * FROM customer WHERE email = %s and password = md5(%s)'
        # q = 'SELECT * FROM customer WHERE email = %s and password = %s'

    elif usertype == 'staff':
        q = 'SELECT * FROM airline_staff WHERE username = %s and password = md5(%s)'
    elif usertype == 'agent':
        q = 'SELECT * FROM booking_agent WHERE email = %s and password = md5(%s)'
    cursor.execute(q, (username, password))
    data = cursor.fetchone()
    cursor.close()
    error = None
    print(data)
    if (data):
        session['username'] = username
        session['usertype'] = usertype
        if usertype == 'staff':
            session['admin'] = check_permission(username)
            session['Operator'] = check_operator(username)
            print(check_permission(username))
            return redirect(url_for('staff_home'))
        elif usertype == 'customer':
            return redirect(url_for('customer_home'))
        else:
            return redirect(url_for('agent_home'))
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)


@app.route('/register')
def register():
    return render_template('register_category.html')


@app.route('/register_category', methods=['GET', 'POST'])
def register_category():
    usertype = request.form['usertype']
    if usertype == 'customer':
        return render_template('customer_register.html')
    elif usertype == 'staff':
        return render_template('staff_register.html')
    else:
        return render_template('agent_register.html')


@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    username = request.form['username']
    name = request.form['name']
    password = request.form['password']
    street = request.form['street']
    city = request.form['city']
    state = request.form['state']
    phone_number = request.form['phone_number']
    passport_number = request.form['passport_number']
    passport_expiration = request.form['passport_expiration']
    passport_country = request.form['passport_country']
    date_of_birth = request.form['date_of_birth']
    building_number = request.form['building_number']

    cursor = conn.cursor()
    q = 'SELECT * FROM customer WHERE email = %s'
    cursor.execute(q, (username))
    data = cursor.fetchone()
    error = None

    if (data):
        error = 'This user has already existed.'
        return render_template('customer_register.html', error=error)
    else:
        ins = "INSERT INTO customer VALUES(\'{}\', \'{}\', md5(\'{}\'), \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')"
        cursor.execute(
            ins.format(username, name, password, building_number, street, city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/staff_register', methods=['GET', 'POST'])
def staff_register():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    date_of_birth = request.form['date_of_birth']
    airline_name = request.form['airline_name']

    cursor = conn.cursor()
    q = 'SELECT * FROM airline_staff WHERE username = %s'
    cursor.execute(q, (username))
    data = cursor.fetchone()
    error = None

    if(data):
        error = "This user has already existed."
        return render_template('staff_register.html', error=error)
    else:
        ins = "INSERT INTO airline_staff VALUES(\'{}\', md5(\'{}\'), \'{}\', \'{}\', \'{}\', \'{}\')"
        cursor.execute(ins.format(username, password, first_name,
                       last_name, date_of_birth, airline_name))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/agent_register', methods=['GET', 'POST'])
def agent_register():
    email = request.form['username']
    password = request.form['password']
    booking_agent_id = request.form['booking_agent_id']

    cursor = conn.cursor()
    q = 'SELECT * FROM booking_agent WHERE email = %s'
    cursor.execute(q, (email))
    data = cursor.fetchone()
    error = None

    if (data):
        error = "This user has already existed."
        return render_template('agent_register.html', error=error)
    else:
        ins = "INSERT INTO booking_agent VALUES(\'{}\', md5(\'{}\'), \'{}\')"
        cursor.execute(ins.format(email, password, booking_agent_id))
        conn.commit()
        cursor.close()
        return render_template('index.html')

# ------------------------------------------------------------------------------------------------------------


@app.route('/customer_home')
def customer_home():
    username = session['username']

    cursor = conn.cursor()
    q = 'SELECT purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
				FROM purchases, ticket, flight \
				WHERE purchases.ticket_id = ticket.ticket_id \
				AND ticket.airline_name = flight.airline_name \
				AND ticket.flight_num = flight.flight_num \
				AND customer_email = \'{}\''
    cursor.execute(q.format(username))
    data = cursor.fetchall()
    cursor.close()
    message = request.args.get('message')
    return render_template('customer_home.html', username=username, posts=data, message=message)


@app.route('/customer_home/customer_viewflights', methods=['POST'])
def customer_viewflights():
    username = session['username']
    depart_date = request.form['depart_date']
    depart_city = request.form['depart_city']
    depart_airport = request.form['depart_airport']
    arrival_date = request.form['arrival_date']
    arrival_city = request.form['arrival_city']
    arrival_airport = request.form['arrival_airport']

    cursor = conn.cursor()
    q = 'SELECT purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
				FROM purchases, ticket, flight, airport \
				WHERE purchases.ticket_id = ticket.ticket_id \
				AND ticket.airline_name = flight.airline_name \
				AND ticket.flight_num = flight.flight_num \
                AND flight.departure_airport = airport.airport_name \
				AND purchases.customer_email = %s \
                AND flight.departure_time BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE) \
                AND flight.departure_airport = %s AND flight.arrival_airport = %s'
    cursor.execute(q, (username, depart_date, arrival_date,
                       depart_airport, arrival_airport))
    data = cursor.fetchall()
    cursor.close()
    error = None

    if (data):
        return render_template('customer_viewflights.html', username=username, depart_date=depart_date,
                               arrival_date=arrival_date, posts=data)
    else:
        error = 'No results have been found.'
        return render_template('customer_viewflights.html', username=username, depart_date=depart_date,
                               arrival_date=arrival_date, error=error)


@app.route('/customer_home/customer_purchase_page')
def customer_purchase_page():
    return render_template('customer_purchase.html')


@app.route('/customer_home/customer_purchase_search', methods=['POST'])
def customer_purchase_search():
    depart_date = request.form['depart_date']
    depart_city = request.form['depart_city']
    depart_airport = request.form['depart_airport']
    arrival_date = request.form['arrival_date']
    arrival_city = request.form['arrival_city']
    arrival_airport = request.form['arrival_airport']

    cursor = conn.cursor()
    q = 'SELECT * FROM flight, airport \
            WHERE airport.airport_name = flight.departure_airport \
            AND airport.airport_city = %s \
            AND airport.airport_name = %s \
            AND flight.status = "Upcoming"\
            AND %s BETWEEN DATE_SUB(flight.departure_time, INTERVAL 2 DAY) AND DATE_ADD(flight.departure_time, INTERVAL 2 DAY) \
            AND %s BETWEEN DATE_SUB(flight.arrival_time, INTERVAL 2 DAY) AND DATE_ADD(flight.arrival_time, INTERVAL 2 DAY) \
            AND (flight.airline_name, flight.flight_num) in \
                (SELECT flight.airline_name, flight.flight_num FROM flight, airport \
                WHERE airport.airport_name=flight.arrival_airport \
                AND airport.airport_city = %s \
                AND airport.airport_name = %s)'
    cursor.execute(q, (depart_city, depart_airport, depart_date,
                   arrival_date, arrival_city, arrival_airport))
    data = cursor.fetchall()
    cursor.close()
    error = None

    if (data):
        return render_template('customer_purchase.html', results=data)
    else:
        error = 'No results have been found.'
        return render_template('customer_purchase.html', searchError=error)


@app.route('/customer_home/customer_purchase', methods=['POST'])
def customer_purchase():
    username = session['username']
    airline_name = request.form['airline_name']
    flight_num = request.form['flight_num']

    cursor = conn.cursor()

    queryCount = 'SELECT COUNT(*) as count FROM ticket WHERE flight_num = %s AND airline_name = %s'
    q = 'SELECT COUNT(*) as count FROM ticket'
    cursor.execute(queryCount, (flight_num, airline_name))
    ticketCount = cursor.fetchone()
    cursor.execute(q)
    ticket_id = cursor.fetchone()
    print(ticketCount)
    ticket_count = ticketCount['count'] + 1
    ticket_id = ticket_id['count'] + 1

    q = "SELECT * FROM flight, airplane WHERE flight.airline_name = %s AND flight_num = %s AND flight.airplane_id = airplane.airplane_id AND flight.airline_name = airplane.airline_name AND airplane.seats >= %s "
    cursor.execute(q, (airline_name, flight_num, ticket_count))
    data = cursor.fetchall()
    if not (data):
        message = 'There is no available seat.'
        return redirect(url_for('customer_home', message=message))

    q = 'INSERT INTO ticket VALUES(%s, %s, %s)'
    cursor.execute(q, (ticket_id, airline_name, flight_num))
    q = 'INSERT INTO purchases VALUES(%s, %s, %s, CURDATE())'
    cursor.execute(q, (ticket_id, username, None))
    conn.commit()
    cursor.close()
    message = 'Successful Purchase.'

    return redirect(url_for('customer_home', message=message))


@app.route('/customer_home/customer_search_init')
def customer_search_init():
    return render_template('customer_search.html')


@app.route('/customer_home/customer_search', methods=['POST'])
def customer_search():
    #username = request.form['username']
    depart_date = request.form['depart_date']
    depart_city = request.form['depart_city']
    depart_airport = request.form['depart_airport']
    arrival_date = request.form['arrival_date']
    arrival_city = request.form['arrival_city']
    arrival_airport = request.form['arrival_airport']

    cursor = conn.cursor()
    q = 'SELECT * FROM flight, airport \
            WHERE airport.airport_name = flight.departure_airport \
            AND airport.airport_city = %s \
            AND airport.airport_name = %s \
            AND flight.status = "Upcoming"\
            AND %s BETWEEN DATE_SUB(flight.departure_time, INTERVAL 2 DAY) AND DATE_ADD(flight.departure_time, INTERVAL 2 DAY) \
            AND %s BETWEEN DATE_SUB(flight.arrival_time, INTERVAL 2 DAY) AND DATE_ADD(flight.arrival_time, INTERVAL 2 DAY) \
            AND (flight.airline_name, flight.flight_num) in \
                (SELECT flight.airline_name, flight.flight_num FROM flight, airport \
                WHERE airport.airport_name=flight.arrival_airport \
                AND airport.airport_city = %s \
                AND airport.airport_name = %s)'
    cursor.execute(q, (depart_city, depart_airport, depart_date,
                   arrival_date, arrival_city, arrival_airport))
    data = cursor.fetchall()
    cursor.close()
    error = None

    if (data):
        return render_template('customer_search.html', results=data)
    else:
        error = 'No results have been found.'
        return render_template('customer_search.html', error=error)


@app.route('/customer_home/customer_spendingtrack')
def customer_spendingtrack():
    username = session['username']

    cursor = conn.cursor()
    q = 'SELECT sum(price) as total \
        FROM purchases, ticket, flight \
        WHERE purchases.ticket_id = ticket.ticket_id \
        AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
        AND purchases.purchase_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE() \
        AND purchases.customer_email = %s'
    cursor.execute(q, (username))
    data = cursor.fetchone()
    cur_month = datetime.datetime.now().month
    spending = ''
    for i in range(6):
        q = f'SELECT sum(price) as spending \
            FROM purchases, ticket, flight \
            WHERE purchases.ticket_id = ticket.ticket_id \
            AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
            AND year(purchases.purchase_date) = year(CURDATE() - interval {i} month)\
            AND month(purchases.purchase_date) = month(CURDATE() - interval {i} month) \
            AND purchases.customer_email = "{username}"'
        cursor.execute(q)
        data1 = cursor.fetchall()
        month = ((cur_month - (i + 1)) % 12) + 1
        print(month)
        print(data1[0]['spending'], i)
        spending += str(data1[0]['spending']) + ' ' + str(month) + ','
    cursor.close()
    print(spending)
    return render_template('customer_spendingtrack.html', totalamount=data['total'], results=spending)


@app.route('/customer_home/customer_spendingtrack_specific', methods=['POST'])
def customer_spendingtrack_specific():
    username = session['username']
    depart_date = request.form['depart_date']
    arrival_date = request.form['arrival_date']

    cursor = conn.cursor()
    q = 'SELECT sum(price) as total \
        FROM purchases, ticket, flight \
        WHERE purchases.ticket_id = ticket.ticket_id \
        AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
        AND purchases.purchase_date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE) \
        AND purchases.customer_email = %s'
    cursor.execute(q, (depart_date, arrival_date, username))
    total = cursor.fetchone()
    print(total)
    spending = ''
    month_range = (int(arrival_date[:4]) - int(depart_date[:4])) * \
        12 + int(arrival_date[5:7]) - int(depart_date[5:7])
    for i in range(month_range + 1):
        q = 'SELECT sum(price) as spending \
            FROM purchases, ticket, flight \
            WHERE purchases.ticket_id = ticket.ticket_id \
            AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
            AND year(purchases.purchase_date) = year(%s - interval ' + str(i) + ' month)\
            AND month(purchases.purchase_date) = month(%s - interval ' + str(i) + ' month) \
            AND purchases.customer_email = %s'
        cursor.execute(q, (arrival_date, arrival_date, username))
        data = cursor.fetchall()
        month = ((int(arrival_date[5:7]) - (i + 1)) % 12) + 1
        spending += str(data[0]['spending']) + ' ' + str(month) + ','
    cursor.close()
    print(spending)
    return render_template('customer_spendingtrack_specific.html', depart_date=depart_date, arrival_date=arrival_date,
                           total=total['total'], results=spending)

# ---------------ADDITIONAL FUNCTION-----------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/customer_home/customer_view_topdestination', methods=['POST'])
def customer_view_topdestination():
    airline = request.form['airline_name']
    print(airline)
    cursor = conn.cursor()
    q = 'SELECT airport_city \
        FROM (ticket NATURAL JOIN flight NATURAL JOIN purchases) JOIN airport \
        WHERE flight.arrival_airport = airport_name \
        AND flight.airline_name = %s AND purchase_date BETWEEN CURRENT_DATE - INTERVAL 3 MONTH \
        AND CURRENT_DATE \
        GROUP BY airport_city ORDER BY COUNT(airport_city) DESC LIMIT 3'
    cursor.execute(q, (airline))
    data1 = cursor.fetchall()

    q = 'SELECT airport_city \
        FROM (ticket NATURAL JOIN flight NATURAL JOIN purchases) JOIN airport \
        WHERE flight.arrival_airport = airport_name \
        AND flight.airline_name = %s AND purchase_date BETWEEN CURRENT_DATE - INTERVAL 1 YEAR \
        AND CURRENT_DATE \
        GROUP BY airport_city ORDER BY COUNT(airport_city) DESC LIMIT 3'
    cursor.execute(q, (airline))
    data2 = cursor.fetchall()
    print(data1)
    return render_template('customer_view_topdestination.html', data1=data1, data2=data2, li='a')

# ------------------------------------------------------------------------------------------------------------


@app.route('/agent_home')
def agent_home():
    username = session['username']

    cursor = conn.cursor()
    q = 'SELECT purchases.customer_email, purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
		FROM purchases, ticket, flight, booking_agent \
		WHERE purchases.ticket_id = ticket.ticket_id \
		AND ticket.airline_name = flight.airline_name \
		AND ticket.flight_num = flight.flight_num \
        AND booking_agent.booking_agent_id = purchases.booking_agent_id \
		AND booking_agent.email = %s\
		AND departure_time > curdate() \
		ORDER BY customer_email'
    cursor.execute(q, (username))
    data = cursor.fetchall()
    cursor.close()

    message = request.args.get('message')
    return render_template('agent_home.html', username=username, posts=data, message=message)


@app.route('/agent_home/agent_view_flights', methods=['POST'])
def agent_view_flights():
    username = session['username']
    depart_date = request.form['depart_date']
    depart_city = request.form['depart_city']
    depart_airport = request.form['depart_airport']
    arrival_date = request.form['arrival_date']
    arrival_city = request.form['arrival_city']
    arrival_airport = request.form['arrival_airport']

    cursor = conn.cursor()
    q = 'SELECT purchases.customer_email, purchases.ticket_id, ticket.airline_name, ticket.flight_num, departure_airport, departure_time, arrival_airport, arrival_time \
			FROM purchases, ticket, flight, airport, booking_agent \
			WHERE purchases.ticket_id = ticket.ticket_id \
			AND ticket.airline_name = flight.airline_name \
			AND ticket.flight_num = flight.flight_num \
            AND flight.departure_airport = airport.airport_name \
            AND booking_agent.booking_agent_id = purchases.booking_agent_id \
			AND booking_agent.email = %s\
            AND flight.departure_time BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE) \
            AND airport.airport_city = %s AND airport.airport_name = %s \
            AND (flight.airline_name, flight.flight_num) in \
                (SELECT flight.airline_name, flight.flight_num FROM flight, airport \
                WHERE airport.airport_name=flight.arrival_airport \
                AND airport.airport_city = %s \
                AND airport.airport_name = %s\
                AND flight.status = "Upcoming")'
    cursor.execute(q, (username, depart_date, arrival_date,
                   depart_city, depart_airport, arrival_city, arrival_airport))
    data = cursor.fetchall()
    cursor.close()

    print(depart_date, arrival_date)

    if (data):
        return render_template('agent_view_flights.html', username=username, depart_date=depart_date, arrival_date=arrival_date, posts=data)
    else:
        error = 'No results have been found.'
        return render_template('agent_view_flights.html', username=username, depart_date=depart_date, arrival_date=arrival_date, error=error)


@app.route('/agent_home/agent_purchase_init')
def agent_purchase_init():
    return render_template('agent_purchase.html')


@app.route('/agent_home/agent_purchase_search', methods=['POST'])
def agent_purchase_search():
    depart_city = request.form['depart_city']
    depart_airport = request.form['depart_airport']
    depart_date = request.form['depart_date']
    arrival_city = request.form['arrival_city']
    arrival_airport = request.form['arrival_airport']
    arrival_date = request.form['arrival_date']

    cursor = conn.cursor()
    q = 'SELECT * FROM flight, airport \
            WHERE airport.airport_name = flight.departure_airport \
            AND airport.airport_city = %s \
            AND airport.airport_name = %s \
            AND flight.status = "Upcoming"\
            AND %s BETWEEN DATE_SUB(flight.departure_time, INTERVAL 2 DAY) AND DATE_ADD(flight.departure_time, INTERVAL 2 DAY) \
            AND %s BETWEEN DATE_SUB(flight.arrival_time, INTERVAL 2 DAY) AND DATE_ADD(flight.arrival_time, INTERVAL 2 DAY) \
            AND (flight.airline_name, flight.flight_num) in \
                (SELECT flight.airline_name, flight.flight_num FROM flight, airport \
                WHERE airport.airport_name=flight.arrival_airport \
                AND airport.airport_city = %s \
                AND airport.airport_name = %s)'
    cursor.execute(q, (depart_city, depart_airport, depart_date,
                   arrival_date, arrival_city, arrival_airport))
    data = cursor.fetchall()
    cursor.close()

    error = None
    if (data):
        return render_template('agent_purchase.html', results=data)
    else:
        error = 'There are no flights temporarily.'
        return render_template('agent_purchase.html', error=error)


@app.route('/agent_home/agent_purchase', methods=['POST'])
def agent_purchase():
    username = session['username']
    email = request.form['customer_email']
    airline = request.form['airline']
    flight_num = request.form['flight_num']

    cursor = conn.cursor()
    q = 'SELECT * FROM booking_agent_work_for WHERE email = %s AND airline_name = %s'
    cursor.execute(q, (username, airline))
    data = cursor.fetchall()
    cursor.close()
    print(data)
    error = None
    if not (data):
        error = 'Access denied.'
        return render_template('agent_purchase.html', searchError=error)

    cursor = conn.cursor()

    queryCount = 'SELECT COUNT(*) as count FROM ticket WHERE flight_num = %s AND airline_name = %s'
    q = 'SELECT COUNT(*) as count FROM ticket'
    cursor.execute(queryCount, (flight_num, airline))
    ticketCount = cursor.fetchone()
    cursor.execute(q)
    ticket_id = cursor.fetchone()
    print(ticketCount)
    ticket_count = ticketCount['count'] + 1
    ticket_id = ticket_id['count'] + 1

    q = "SELECT * FROM flight, airplane WHERE flight.airline_name = %s AND flight_num = %s AND flight.airplane_id = airplane.airplane_id AND flight.airline_name = airplane.airline_name AND airplane.seats >= %s "
    cursor.execute(q, (airline, flight_num, ticket_count))
    data = cursor.fetchall()

    if not (data):
        message = 'There is no available seat.'
        return redirect(url_for('agent_home', message=message))

    q = 'INSERT INTO ticket VALUES(%s, %s, %s)'
    cursor.execute(q, (ticket_id, airline, flight_num))
    q = 'SELECT booking_agent_id FROM booking_agent WHERE email = %s'
    cursor.execute(q, (username))
    agent_id = cursor.fetchone()
    q = 'INSERT INTO purchases VALUES (%s, %s, %s, CURDATE())'
    cursor.execute(q, (ticket_id, email, agent_id['booking_agent_id']))
    conn.commit()
    cursor.close()
    message = 'Purchased successfully.'
    return redirect(url_for('agent_home', message=message))


@app.route('/agent_home/agent_search_init')
def agent_search_init():
    return render_template('agent_search.html')


@app.route('/agent_home/agent_search', methods=['POST'])
def agent_search():
    username = session['username']
    depart_city = request.form['depart_city']
    depart_airport = request.form['depart_airport']
    depart_date = request.form['depart_date']
    arrival_city = request.form['arrival_city']
    arrival_airport = request.form['arrival_airport']
    arrival_date = request.form['arrival_date']

    cursor = conn.cursor()
    query = 'SELECT * FROM flight, airport \
            WHERE airport.airport_name = flight.departure_airport \
            AND airport.airport_city = %s \
            AND airport.airport_name = %s \
            AND flight.status = "Upcoming"\
            AND %s BETWEEN DATE_SUB(flight.departure_time, INTERVAL 2 DAY) AND DATE_ADD(flight.departure_time, INTERVAL 2 DAY) \
            AND %s BETWEEN DATE_SUB(flight.arrival_time, INTERVAL 2 DAY) AND DATE_ADD(flight.arrival_time, INTERVAL 2 DAY) \
            AND (flight.airline_name, flight.flight_num) in \
                (SELECT flight.airline_name, flight.flight_num FROM flight, airport \
                WHERE airport.airport_name=flight.arrival_airport \
                AND airport.airport_city = %s \
                AND airport.airport_name = %s)'

    cursor.execute(query, (depart_city, depart_airport, depart_date,
                   arrival_date, arrival_city, arrival_airport))
    data = cursor.fetchall()
    cursor.close()

    error = None
    if (data):
        return render_template('agent_search.html', results=data)
    else:
        error = 'No results have been found.'
        return render_template('agent_search.html', error=error)


@app.route('/agent_home/agent_view_commission')
def agent_view_commission():
    username = session['username']

    cursor = conn.cursor()
    q = 'SELECT booking_agent_id FROM booking_agent WHERE email=%s'
    cursor.execute(q, (username))
    agent_id = cursor.fetchone()

    q = 'SELECT sum(price)*.10 as totalComm FROM purchases, ticket, flight \
        WHERE purchases.ticket_id = ticket.ticket_id \
        AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
        AND purchases.purchase_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE() \
        AND purchases.booking_agent_id = %s'
    cursor.execute(q, (agent_id['booking_agent_id']))
    total_commission = cursor.fetchone()

    if (total_commission):
        total_commission = total_commission['totalComm']
    else:
        total_commission = 0

    q = 'SELECT count(*) as ticketCount FROM purchases, ticket, flight \
        WHERE purchases.ticket_id = ticket.ticket_id \
        AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
        AND purchases.purchase_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE() \
        AND purchases.booking_agent_id = %s'
    cursor.execute(q, (agent_id['booking_agent_id']))
    ticket_amount = cursor.fetchone()
    cursor.close()

    ticket_amount = ticket_amount['ticketCount']
    avg_commission = 0
    if ticket_amount != 0:
        avg_commission = total_commission / ticket_amount

    return render_template('agent_view_commission.html', username=username, total_commission=total_commission, avg_commission=avg_commission, ticket_amount=ticket_amount)


@app.route('/agent_home/agent_commission_date', methods=['POST'])
def agent_commission_date():
    username = session['username']
    depart_date = request.form['depart_date']
    arrival_date = request.form['arrival_date']

    cursor = conn.cursor()
    q = 'SELECT booking_agent_id FROM booking_agent WHERE email=%s'
    cursor.execute(q, (username))
    agent_id = cursor.fetchone()
    q = 'SELECT sum(price)*.10 as totalComm FROM purchases, ticket, flight \
        WHERE purchases.ticket_id = ticket.ticket_id \
        AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
        AND purchases.purchase_date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE) \
        AND purchases.booking_agent_id = %s'
    cursor.execute(q, (depart_date, arrival_date,
                   agent_id['booking_agent_id']))
    total_commission = cursor.fetchone()

    if (total_commission):
        total_commission = total_commission['totalComm']
    else:
        total_commission = 0

    q = 'SELECT count(*) as ticketCount FROM purchases, ticket, flight \
        WHERE purchases.ticket_id = ticket.ticket_id \
        AND ticket.airline_name = flight.airline_name AND ticket.flight_num = flight.flight_num \
        AND purchases.purchase_date BETWEEN CAST( %s AS DATE) AND CAST( %s AS DATE) \
        AND purchases.booking_agent_id = %s'
    cursor.execute(q, (depart_date, arrival_date,
                   agent_id['booking_agent_id']))
    ticket_amount = cursor.fetchone()
    cursor.close()

    ticket_amount = ticket_amount['ticketCount']
    return render_template('agent_commission_date.html', depart_date=depart_date, arrival_date=arrival_date, total_commission=total_commission, ticket_amount=ticket_amount)


@app.route('/agent_home/agent_view_topcustomer')
def agent_view_topcustomer():
    username = session['username']

    cursor = conn.cursor()
    q = 'SELECT customer_email, count(ticket_id) AS ticket_sales FROM booking_agent NATURAL JOIN purchases\
        WHERE (purchase_date between date_sub(curdate(), interval 6 month) and curdate()) \
        AND email = %s \
        GROUP BY customer_email ORDER BY ticket_sales DESC LIMIT 5'
    cursor.execute(q, (username))
    data = cursor.fetchall()
    results1 = ''
    for index in data:
        results1 += str(index['ticket_sales']) + ' ' + \
            str(index['customer_email']) + ','

    q = 'SELECT customer_email, sum(flight.price) AS commission FROM booking_agent, purchases, ticket, flight \
        WHERE (purchase_date between date_sub(curdate(), interval 1 year) and curdate())\
        AND booking_agent.booking_agent_id = purchases.booking_agent_id \
        AND purchases.ticket_id = ticket.ticket_id \
        AND ticket.airline_name = flight.airline_name \
        AND ticket.flight_num = flight.flight_num \
        AND booking_agent.email = %s \
        GROUP BY purchases.customer_email\
        ORDER BY commission DESC\
        LIMIT 5'
    cursor.execute(q, (username))
    data = cursor.fetchall()
    results2 = ''
    for index in data:
        results2 += str(index['commission']) + ' ' + \
            str(index['customer_email']) + ','

    return render_template('agent_view_topcustomer.html', results1=results1, results2=results2)

# ------------------------------------------------------------------------------------------------------------


def valid_staff():
    username = session.get('username')
    if not username:
        return False

    cursor = conn.cursor()
    q = 'SELECT * FROM airline_staff WHERE username = %s'
    cursor.execute(q, (username))
    data = cursor.fetchall()
    cursor.close()

    if (data):
        return True
    else:
        session.pop('username')
        return False


def get_airline():
    username = session['username']

    cursor = conn.cursor()
    q = 'SELECT airline_name FROM airline_staff WHERE username = %s'
    cursor.execute(q, (username))
    airline = cursor.fetchone()['airline_name']
    cursor.close()

    return airline


@app.route('/staff_home')
def staff_home():
    if valid_staff():
        username = session['username']

        cursor = conn.cursor()
        airline = get_airline()
        q = 'SELECT * FROM flight WHERE airline_name = %s AND departure_time BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL 30 DAY'
        cursor.execute(q, (airline))
        data = cursor.fetchall()
        cursor.close()
        error = request.args.get('error')
        results2 = None
        if not (data):
            results2 = "No flights in next 30 days."
        message2 = request.args.get('message2')
        return render_template('staff_searchflight.html', username=username, error=error,
                               results=data, results2=results2, message2=message2, message='Upcoming flights in the next 30 days:')
    else:
        error = 'Operation has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_searchflight/filter', methods=['POST'])
def staff_searchflight_filter():
    if valid_staff():
        username = session['username']
        airline = get_airline()
        depart_city = request.form['depart_city']
        arrival_city = request.form['arrival_city']
        depart_date = request.form['depart_date']
        arrival_date = request.form['arrival_date']

        cursor = conn.cursor()
        if depart_date > arrival_date:
            error = 'Invalid time.'
            return redirect(url_for('staff_home', error=error))
        if depart_city == 'None' and arrival_city == 'None':
            q = 'SELECT * FROM flight WHERE airline_name = "%s"\
                AND ((convert(departure_time,date) BETWEEN "%s" AND "%s")\
                OR (convert(arrival_time,date) BETWEEN "%s" AND "%s"))'
            cursor.execute(q % (airline, depart_date,
                           arrival_date, depart_date, arrival_date))
            data = cursor.fetchall()
            cursor.close()
        elif depart_city == 'None' and arrival_city != 'None':
            q = 'SELECT * FROM flight WHERE airline_name = %s\
                AND (arrival_airport = %s \
                    OR arrival_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s))\
                AND ((convert(departure_time,date) BETWEEN %s AND %s)\
                    OR (convert(arrival_time,date) BETWEEN %s AND %s))'
            cursor.execute(q, (airline, arrival_city, arrival_city,
                           depart_date, arrival_date, depart_date, arrival_date))
            data = cursor.fetchall()
            cursor.close()
        elif depart_city != 'None' and arrival_city == 'None':
            q = 'SELECT * FROM flight WHERE airline_name = %s\
                AND (departure_airport = %s \
                    OR departure_airport IN (SELECT airport_name FROM airport WHERE airport_city = %s))\
                AND ((convert(departure_time,date) BETWEEN %s AND %s)\
                    OR (convert(arrival_time,date) BETWEEN %s AND %s))'
            cursor.execute(q, (airline, depart_city, depart_city,
                           depart_date, arrival_date, depart_date, arrival_date))
            data = cursor.fetchall()
            cursor.close()
        else:
            q = 'SELECT * FROM flight WHERE airline_name = "%s"\
                AND (departure_airport = "%s" \
                    OR departure_airport IN (SELECT airport_name FROM airport WHERE airport_city = "%s"))\
                AND (arrival_airport = "%s" \
                    OR arrival_airport IN (select airport_name FROM airport WHERE airport_city = "%s"))\
                AND ((convert(departure_time,date) BETWEEN "%s" AND "%s")\
                    OR (convert(arrival_time,date) BETWEEN "%s" AND "%s"))'
            cursor.execute(q % (airline, depart_city, depart_city, arrival_city,
                           arrival_city, depart_date, arrival_date, depart_date, arrival_date))
            data = cursor.fetchall()
            cursor.close()
        error = None

        if (data):
            return render_template('staff_searchflight.html', username=username, results=data, message='Results:')
        else:
            error = 'No results have been found.'
            return redirect(url_for('staff_home', error=error))
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_searchflight/customer_on_flight', methods=['POST'])
def staff_search_customer_on_flight():
    if valid_staff():
        username = session['username']
        airline = get_airline()
        flight_num = request.form['flight_num']

        cursor = conn.cursor()
        q = 'SELECT customer_email FROM purchases NATURAL JOIN ticket WHERE flight_num = %s \
            AND airline_name = %s'
        cursor.execute(q, (flight_num, airline))
        data = cursor.fetchall()
        cursor.close()

        if (data):
            return render_template('staff_searchflight.html', username=username, customerresults=data, message='Customers on the Flight ' + flight_num)
        else:
            error = 'No results have been found.'
            return redirect(url_for('staff_home', error=error))
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


def permission_check():
    username = session.get('username')
    q = "SELECT * FROM permission WHERE permission_type = 'operator' AND username = %s "
    cursor = conn.cursor()
    cursor.execute(q, (username))
    data = cursor.fetshall()
    if (data):
        return True
    else:
        return False


@app.route('/staff_home/staff_searchflight/update_check')
def staff_creatflight_init():
    if valid_staff():
        error = request.args.get('error')
        return render_template('staff_creatflight_init.html', error=error)
    elif not permission_check():
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_searchflight/updating', methods=['POST'])
def staff_updatingflight():
    if valid_staff():
        flight_num = request.form['flight_num']
        depart_date = request.form['depart_date']
        depart_airport = request.form['depart_airport']
        arrival_date = request.form['arrival_date']
        arrival_airport = request.form['arrival_airport']
        status = "Upcoming"
        price = request.form['price']
        airplane_id = request.form['airplane_id']
        airline = get_airline()

        if depart_date > arrival_date:
            error = 'Invalid time.'
            return redirect(url_for('staff_creatflight_init', error=error))

        cursor = conn.cursor()
        q = 'SELECT * FROM airplane WHERE airplane_id = %s AND airline_name = %s'
        cursor.execute(q, (airplane_id, airline))
        data = cursor.fetchall()

        if not (data):
            error = 'Invalid Airplane ID.'
            return redirect(url_for('staff_creatflight_init', error=error))
        q = 'SELECT * FROM airport WHERE airport_name = %s'
        cursor.execute(q, (depart_airport))
        data = cursor.fetchall()
        if not (data):
            error = 'Invalid Depart Airport.'
            return redirect(url_for('staff_creatflight_init', error=error))
        q = 'SELECT * FROM airport WHERE airport_name = %s'
        cursor.execute(q, (arrival_airport))
        data = cursor.fetchall()
        if not (data):
            error = 'Invalid Arrival Airport.'
            return redirect(url_for('staff_creatflight_init', error=error))

        q = 'INSERT INTO flight VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(q, (airline, flight_num, depart_airport, depart_date,
                       arrival_airport, arrival_date, price, status, airplane_id))
        conn.commit()
        cursor.close()

        error = request.args.get('error')
        return redirect(url_for('staff_home', error=error))
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_searchflight/modify_status', methods=['POST'])
def staff_modify_status():
    if valid_staff():
        flight_num = request.form['flight_num']
        status = request.form['status']
        airline = get_airline()

        cursor = conn.cursor()
        q = 'SELECT * FROM flight WHERE flight_num = %s AND airline_name = %s'
        cursor.execute(q, (flight_num, airline))
        data = cursor.fetchall()

        if not (data):
            error = 'Cannot find your flight.'
            return redirect(url_for('staff_createflight_init', error=error))

        q = 'UPDATE flight SET status = %s WHERE flight_num = %s AND airline_name = %s'
        cursor.execute(q, (status, flight_num, airline))
        conn.commit()
        cursor.close()

        error = request.args.get('error')
        return redirect(url_for('staff_home', error=error))
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_add_airplane')
def staff_add_airplane_init():
    if valid_staff():
        error = request.args.get('error')
        return render_template('staff_add_airplane.html', error=error)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_add_airplane/adding', methods=['POST'])
def staff_adding_airplane():
    if valid_staff():
        airplane_id = request.form['airplane_id']
        seats = request.form['seats']
        airline = get_airline()

        cursor = conn.cursor()
        q = 'SELECT * FROM airplane WHERE airplane_id = %s'
        cursor.execute(q, (airplane_id))
        data = cursor.fetchall()

        if (data):
            error = 'This airplane has already existed.'
            return redirect(url_for('staff_add_airplane_init', error=error))

        q = 'INSERT INTO airplane VALUES (%s, %s, %s)'
        cursor.execute(q, (airline, airplane_id, seats))
        conn.commit()

        q = 'SELECT * FROM airplane WHERE airline_name = %s'
        cursor.execute(q, (airline))
        data = cursor.fetchall()
        cursor.close()

        return render_template('staff_added_airplane.html', results=data)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_add_airport')
def staff_add_airport():
    if valid_staff():
        error = request.args.get('error')
        return render_template('staff_add_airport.html', error=error)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))

# Additional requirement!!!
# Airline Staff with "Admin" permission will
# be able to add new airports into the system
# for the airline they work for.


@app.route('/staff_home/staff_add_airport/adding', methods=['POST'])
def staff_adding_airport():
    if valid_staff():
        city = request.form['city']
        airport = request.form['airport']

        cursor = conn.cursor()
        q = 'SELECT * FROM airport WHERE airport_name = %s'
        cursor.execute(q, (airport))
        data = cursor.fetchone()

        if (data):
            error = 'This airport has already existed.'
            return redirect(url_for('staff_add_airport', error=error))
        else:
            q = 'INSERT INTO airport VALUES (%s, %s)'
            cursor.execute(q, (airport, city))
            conn.commit()
            cursor.close()

            message = 'You have successed added an airport.'
            return redirect(url_for('staff_home', message2=message))
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_agent')
def staff_agent():
    if valid_staff():
        airline = get_airline()

        cursor = conn.cursor()
        q = 'SELECT email, COUNT(ticket_id) AS ticket_sales\
            FROM booking_agent NATURAL JOIN purchases NATURAL JOIN ticket\
            WHERE (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 month) AND curdate())\
                    AND airline_name = %s\
            GROUP BY email\
            ORDER BY ticket_sales DESC\
            LIMIT 5'
        cursor.execute(q, (airline))
        data1 = cursor.fetchall()

        q = 'SELECT email, COUNT(ticket_id) AS ticket_sales\
            FROM booking_agent NATURAL JOIN purchases NATURAL JOIN ticket\
            WHERE (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate())\
                    AND airline_name = %s\
            GROUP BY email\
            ORDER BY ticket_sales DESC\
            LIMIT 5'
        cursor.execute(q, (airline))
        data2 = cursor.fetchall()

        q = 'SELECT email, SUM(price)*0.1 AS totalcommission\
            FROM booking_agent NATURAL JOIN purchases NATURAL JOIN ticket NATURAL JOIN flight\
            WHERE (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate())\
                    AND airline_name = %s\
            GROUP BY email\
            ORDER BY totalcommission DESC\
            LIMIT 5'
        cursor.execute(q, (airline))
        data3 = cursor.fetchall()
        cursor.close()

        error = request.args.get('error')
        return render_template('staff_agent.html', error=error, data1=data1, data2=data2, data3=data3)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_customer')
def staff_customer():
    if valid_staff():
        airline = get_airline()

        cursor = conn.cursor()
        q = 'SELECT customer.name, purchases.customer_email, COUNT(ticket.ticket_id) AS ticket_purchased\
            FROM (purchases NATURAL JOIN ticket), customer\
            WHERE customer.email = purchases.customer_email\
            AND ticket.airline_name = %s\
            AND (purchases.purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate())\
            GROUP BY purchases.customer_email\
            ORDER BY ticket_purchased DESC\
            LIMIT 1'
        cursor.execute(q, (airline))
        data = cursor.fetchall()
        cursor.close()

        error = request.args.get('error')
        return render_template('staff_customer.html', error=error, results=data)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_customer/specific', methods=['POST'])
def staff_customer_specific():
    if valid_staff():
        airline = get_airline()
        customer = request.form['email']

        cursor = conn.cursor()
        q = 'SELECT * FROM purchases NATURAL JOIN ticket\
            WHERE airline_name = %s AND customer_email = %s'
        cursor.execute(q, (airline, customer))
        data = cursor.fetchall()
        print(data)
        cursor.close()

        error = request.args.get('error')
        return render_template('staff_customer_specific.html', error=error, results=data, customer=customer)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_view_reports')
def staff_view_reports():
    if valid_staff():
        airline = get_airline()
        sale = ''

        cursor = conn.cursor()
        q = 'SELECT year, month, COUNT(ticket_id)\
            FROM (SELECT YEAR(purchase_date) AS year, MONTH(purchase_date) AS month, ticket_id\
            FROM purchases NATURAL JOIN ticket\
            WHERE (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate()) AND airline_name = %s) AS a\
            GROUP BY year, month'
        cursor.execute(q, (airline))
        data = cursor.fetchall()
        for index in data:
            sale += str(index['year'])+'-'+str(index['month']) + \
                ' '+str(index['COUNT(ticket_id)'])+','
        cursor.close()

        error = request.args.get('error')
        return render_template('staff_view_reports.html', error=error, results=sale)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_view_reports/date', methods=['POST'])
def staff_view_reports_date():
    if valid_staff():
        airline = get_airline()
        start = request.form['start']
        end = request.form['end']

        if start > end:
            error = 'Invalid time.'
            return redirect(url_for('staff_view_reports', error=error))

        cursor = conn.cursor()
        q = 'SELECT COUNT(ticket_id) AS sales\
            FROM purchases NATURAL JOIN ticket\
            WHERE airline_name = %s AND purchase_date BETWEEN %s AND %s'
        cursor.execute(q, (airline, start, end))
        data1 = cursor.fetchall()
        print(data1)
        sale = ''
        q = 'SELECT year, month, COUNT(ticket_id)\
            FROM (SELECT YEAR(purchase_date) AS year, MONTH(purchase_date) AS month, ticket_id\
            FROM purchases NATURAL JOIN ticket\
            WHERE (purchase_date BETWEEN %s AND %s) AND airline_name = %s) AS a\
            GROUP BY year, month'
        cursor.execute(q, (airline, start, end))
        data2 = cursor.fetchall()
        for index in data2:
            sale += str(index['year'])+'-'+str(index['month']) + \
                ' '+str(index['COUNT(ticket_id)'])+','
        cursor.close()

        return render_template('staff_view_reports.html',
                               message='FROM: ' + start + ' ||   TO: ' + end +
                               ' (Ticket Amount: ' +
                               str(data1[0]['sales']) + ')',
                               results=sale)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_view_reports/period', methods=['POST'])
def staff_view_reports_period():
    if valid_staff():
        airline = get_airline()
        period = request.form['period']

        cursor = conn.cursor()
        q = 'SELECT COUNT(ticket_id) AS sales\
            FROM purchases NATURAL JOIN ticket\
            WHERE airline_name = %s\
            AND (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 ' + period + ') AND curdate())'
        cursor.execute(q, (airline))
        data1 = cursor.fetchall()
        print(data1)
        sale = ''
        q = 'SELECT year, month, COUNT(ticket_id)\
            FROM (SELECT YEAR(purchase_date) AS year, MONTH(purchase_date) AS month, ticket_id\
            FROM purchases NATURAL JOIN ticket\
            WHERE (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 ' + period + ') AND curdate()) AND airline_name = %s) AS a\
            GROUP BY year, month'
        cursor.execute(q, (airline))
        data2 = cursor.fetchall()
        print(data2)
        for index in data2:
            sale += str(index['year'])+'-'+str(index['month']) + \
                ' '+str(index['COUNT(ticket_id)'])+','
        cursor.close()

        return render_template('staff_view_reports.html',
                               message='LAST ' + period + ' ' +
                               str(data1[0]['sales']) + ' tickets are sold.',
                               results=sale)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_Revenues')
def staff_Revenues():
    if valid_staff():
        airline = get_airline()

        cursor = conn.cursor()
        q = 'SELECT SUM(price)\
            FROM flight NATURAL JOIN purchases NATURAL JOIN ticket\
            WHERE airline_name = %s AND (purchase_date BETWEEN date_sub(curdate(), INTERVAL 3 month) AND curdate())\
	        AND booking_agent_id IS null'
        cursor.execute(q, (airline))
        data1 = cursor.fetchall()

        q = 'SELECT SUM(price)\
            FROM flight NATURAL JOIN purchases NATURAL JOIN ticket\
            WHERE airline_name = %s AND (purchase_date BETWEEN date_sub(curdate(), INTERVAL 3 month) AND curdate())\
	        AND booking_agent_id IS NOT null'
        cursor.execute(q, (airline))
        data2 = cursor.fetchall()

        q = 'SELECT SUM(price)\
            FROM flight NATURAL JOIN purchases NATURAL JOIN ticket\
            WHERE airline_name = %s AND (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate())\
	        AND booking_agent_id IS null'
        cursor.execute(q, (airline))
        data3 = cursor.fetchall()

        q = 'SELECT SUM(price)\
            FROM flight NATURAL JOIN purchases NATURAL JOIN ticket\
            WHERE airline_name = %s AND (purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate())\
	        AND booking_agent_id IS NOT null'
        cursor.execute(q, (airline))
        data4 = cursor.fetchall()
        cursor.close()

        return render_template('staff_profits.html', mdirect=data1[0]['SUM(price)'], mindirect=data2[0]['SUM(price)'], ydirect=data3[0]['SUM(price)'], yindirect=data4[0]['SUM(price)'])
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_topDestinations')
def staff_topDestinations():
    if valid_staff():
        airline = get_airline()

        cursor = conn.cursor()
        q = 'SELECT flight.arrival_airport, airport.airport_city, COUNT(*) AS total_purchase\
            FROM (flight NATURAL JOIN purchases NATURAL JOIN ticket),airport \
            WHERE flight.arrival_airport = airport.airport_name AND ticket.airline_name = %s AND purchases.purchase_date BETWEEN date_sub(curdate(), INTERVAL 3 month) AND curdate()\
            GROUP BY flight.arrival_airport, airport.airport_city\
            ORDER BY count(*) DESC\
            LIMIT 5'
        cursor.execute(q, (airline))
        data1 = cursor.fetchall()
        q = 'SELECT flight.arrival_airport, airport.airport_city, COUNT(*) AS total_purchase\
            FROM (flight NATURAL JOIN purchases NATURAL JOIN ticket),airport \
            WHERE flight.arrival_airport = airport.airport_name AND ticket.airline_name = %s AND purchases.purchase_date BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate()\
            GROUP BY flight.arrival_airport, airport.airport_city\
            ORDER BY count(*) DESC\
            LIMIT 5'
        cursor.execute(q, (airline))
        data2 = cursor.fetchall()
        cursor.close()
        print(data2)
        return render_template('staff_pop_airport.html', results1=data1, results2=data2)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/staff_home/staff_grant_newpermissions')
def staff_grant_newpermissions():
    error = request.args.get('error')
    return render_template('staff_grant_newpermissions.html', error=error)


@app.route('/staff_home/staff_granting_newpermissions', methods=['POST'])
def staff_granting_newpermissions():
    username = session['username']

    cursor = conn.cursor()
    q = 'SELECT * FROM airline_staff NATURAL JOIN permission WHERE username = %s AND permission_type = "admin"'
    cursor.execute(q, (username))
    data = cursor.fetchone()

    if not (data):
        error = 'Access denied.'
        return redirect(url_for('staff_home', error=error))

    airline = get_airline()
    permission = request.form['username']
    permission_type = request.form['permission_type']

    q = 'SELECT * FROM airline_staff WHERE username = %s AND airline_name = %s'
    cursor.execute(q, (permission, airline))
    data = cursor.fetchone()
    cursor.close()

    if (data):
        cursor = conn.cursor()
        q = 'INSERT INTO permission VALUES( %s, %s)'
        cursor.execute(q, (permission, permission_type))
        conn.commit()
        cursor.close()
        return redirect('/staff_home')
    else:
        error = 'Operation failed.'
        return redirect(url_for('staff_grant_newpermissions', error=error))


@app.route('/staff_home/staff_addagent')
def staff_addagent():
    return render_template('staff_addagent.html')


@app.route('/staff_home/staff_addagent/adding', methods=['POST'])
def staff_addingagent():
    if valid_staff():
        airline = get_airline()
        username = request.form['username']

        cursor = conn.cursor()
        q = 'SELECT * FROM booking_agent_work_for WHERE email = %s'
        cursor.execute(q, (username))
        data = cursor.fetchone()
        cursor.close()

        if not (data):
            error = 'Agent has already existed.'
            return render_template('staff_addagent.html', error=error)
        else:
            cursor = conn.cursor()
            q = 'INSERT INTO booking_agent_work_for VALUES (%s, %s)'
            cursor.execute(q, (username, airline))
            cursor.close()
            return redirect('/staff_home')
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))

# -----------------ADDITIONAL FUNCTION----------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/customer_home/customer_view_flights/flight', methods=['POST'])
def customer_view_flights_flight():
    depart_city = request.form['depart_city']
    arrival_city = request.form['arrival_city']
    depart_date = request.form['depart_date']
    print(depart_city)
    print(arrival_city)
    print(depart_date)
    cursor = conn.cursor()
    q = '''SELECT airline_name, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price, status, airplane_id \
                FROM flight, airport AS a1, airport AS a2\
                WHERE status = 'Upcoming' \
                AND a1.airport_name = departure_airport AND a2.airport_name = arrival_airport \
                AND (departure_airport = "{}" OR a1.airport_city = "{}") \
                AND (arrival_airport = "{}" OR a2.airport_city = "{}") AND DATE(departure_time) = "{}"'''.format(depart_city, depart_city, arrival_city, arrival_city, depart_date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)
    error = None
    if (data):
        return render_template('customer_view_flights_flight.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('customer_home', error=error))


@app.route('/customer_home/customer_view_flights/status', methods=['POST'])
def customer_view_flights_status():
    flight_num = request.form['flight_num']
    date = request.form['date']
    print(flight_num)
    print(date)
    cursor = conn.cursor()
    q = 'SELECT airline_name, flight_num, status, departure_time, arrival_time FROM flight\
        WHERE flight_num = {} \
        AND (DATE(departure_time) = "{}" OR DATE(arrival_time) = "{}" )'.format(flight_num, date, date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)

    error = None
    if (data):
        return render_template('customer_view_flights_status.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('customer_home', error=error))


@app.route('/staff_home/staff_status_stats', methods=['GET', 'POST'])
def staff_status_stats():
    if valid_staff():
        airline = get_airline()

        cursor = conn.cursor()
        q = 'SELECT COUNT(DISTINCT flight_num) FROM flight\
            WHERE airline_name = %s AND status = "On-time"\
            AND departure_time BETWEEN date_sub(curdate(), INTERVAL 3 month) AND curdate()'
        cursor.execute(q, (airline))
        data1 = cursor.fetchall()

        q = 'SELECT COUNT(DISTINCT flight_num) FROM flight\
            WHERE airline_name = %s AND status = "Delayed"\
            AND departure_time BETWEEN date_sub(curdate(), INTERVAL 3 month) AND curdate()'
        cursor.execute(q, (airline))
        data2 = cursor.fetchall()
        if (int(data1[0]['COUNT(DISTINCT flight_num)']) + int(data2[0]['COUNT(DISTINCT flight_num)'])) != 0:
            index1 = str(int(data1[0]['COUNT(DISTINCT flight_num)'])/(int(
                data1[0]['COUNT(DISTINCT flight_num)']) + int(data2[0]['COUNT(DISTINCT flight_num)'])))
        else:
            index1 = '0'
        q = 'SELECT COUNT(DISTINCT flight_num) FROM flight\
            WHERE airline_name = %s AND status = "On-time"\
            AND departure_time BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate()'
        cursor.execute(q, (airline))
        data3 = cursor.fetchall()

        q = 'SELECT COUNT(DISTINCT flight_num) FROM flight\
            WHERE airline_name = %s AND status = "Delayed"\
            AND departure_time BETWEEN date_sub(curdate(), INTERVAL 1 year) AND curdate()'
        cursor.execute(q, (airline))
        data4 = cursor.fetchall()
        cursor.close()
        if (int(data3[0]['COUNT(DISTINCT flight_num)']) + int(data4[0]['COUNT(DISTINCT flight_num)'])) != 0:
            index2 = str(int(data3[0]['COUNT(DISTINCT flight_num)'])/(int(
                data3[0]['COUNT(DISTINCT flight_num)']) + int(data4[0]['COUNT(DISTINCT flight_num)'])))
        else:
            index2 = '0'
        error = request.args.get('error')
        return render_template('staff_status_stats.html', error=error, data1=data1[0]['COUNT(DISTINCT flight_num)'],
                               data2=data2[0]['COUNT(DISTINCT flight_num)'], results1=index1, data3=data3[
            0]['COUNT(DISTINCT flight_num)'],
            data4=data4[0]['COUNT(DISTINCT flight_num)'], results2=index2)
    else:
        error = 'Admission has been denied, retry please.'
        return redirect(url_for('hello', error=error))


@app.route('/agent_home/agent_view_flights/flight', methods=['POST'])
def agent_view_flights_flight():
    depart_city = request.form['depart_city']
    arrival_city = request.form['arrival_city']
    depart_date = request.form['depart_date']
    print(depart_city)
    print(arrival_city)
    print(depart_date)
    cursor = conn.cursor()
    q = '''SELECT airline_name, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price, status, airplane_id \
                FROM flight, airport AS a1, airport AS a2\
                WHERE status = 'Upcoming' \
                AND a1.airport_name = departure_airport AND a2.airport_name = arrival_airport \
                AND (departure_airport = "{}" OR a1.airport_city = "{}") \
                AND (arrival_airport = "{}" OR a2.airport_city = "{}") AND DATE(departure_time) = "{}"'''.format(depart_city, depart_city, arrival_city, arrival_city, depart_date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)
    error = None
    if (data):
        return render_template('agent_view_flights_flight.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('agent_home', error=error))


@app.route('/agent_home/agent_view_flights/status', methods=['POST'])
def agent_view_flights_status():
    flight_num = request.form['flight_num']
    date = request.form['date']
    print(flight_num)
    print(date)
    cursor = conn.cursor()
    q = 'SELECT airline_name, flight_num, status, departure_time, arrival_time FROM flight\
        WHERE flight_num = {} \
        AND (DATE(departure_time) = "{}" OR DATE(arrival_time) = "{}" )'.format(flight_num, date, date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)

    error = None
    if (data):
        return render_template('agent_view_flights_status.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('agent_home', error=error))


@app.route('/staff_home/staff_view_flights/flight', methods=['POST'])
def staff_view_flights_flight():
    depart_city = request.form['depart_city']
    arrival_city = request.form['arrival_city']
    depart_date = request.form['depart_date']
    print(depart_city)
    print(arrival_city)
    print(depart_date)
    cursor = conn.cursor()
    q = '''SELECT airline_name, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price, status, airplane_id \
                FROM flight, airport AS a1, airport AS a2\
                WHERE status = 'Upcoming' \
                AND a1.airport_name = departure_airport AND a2.airport_name = arrival_airport \
                AND (departure_airport = "{}" OR a1.airport_city = "{}") \
                AND (arrival_airport = "{}" OR a2.airport_city = "{}") AND DATE(departure_time) = "{}"'''.format(depart_city, depart_city, arrival_city, arrival_city, depart_date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)
    error = None
    if (data):
        return render_template('staff_view_flights_flight.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('staff_home', error=error))


@app.route('/staff_home/staff_view_flights/status', methods=['POST'])
def staff_view_flights_status():
    flight_num = request.form['flight_num']
    date = request.form['date']
    print(flight_num)
    print(date)
    cursor = conn.cursor()
    q = 'SELECT airline_name, flight_num, status, departure_time, arrival_time FROM flight\
        WHERE flight_num = {} \
        AND (DATE(departure_time) = "{}" OR DATE(arrival_time) = "{}" )'.format(flight_num, date, date)
    cursor.execute(q)
    data = cursor.fetchall()
    cursor.close()
    print(data)

    error = None
    if (data):
        return render_template('staff_view_flights_status.html', results=data)
    else:
        error = 'No results have been found.'
        return redirect(url_for('staff_home', error=error))


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

# invalid URL


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# internal server error


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == "__main__":

    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run("127.0.0.1", 5000, debug=True)
