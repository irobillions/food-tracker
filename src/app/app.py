from flask import Flask, render_template, request, g
from .database import get_db
from datetime import datetime

app = Flask(__name__)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite3'):
        g.sqlite_db.close()


@app.route('/')
@app.route('/home', methods=['POST', 'GET'])
def home():
    class_variable = 'active'
    db = get_db()
    if request.method == 'POST':
        date = request.form['date']
        print(date)
        dt = datetime.strptime(date, '%Y-%m-%d')
        database_date = datetime.strftime(dt, '%Y%m%d')
        date = None
        db.execute('insert into log_dates(entry_date) values (?)', [database_date])
        db.commit()

    cursor = db.execute('SELECT log_dates.entry_date,  sum(food.protein) as protein, sum(food.carbohydrates) as '
                        'carbohydrates, sum(food.fat) as fat, sum(food.calories) as calories from log_dates left join '
                        'food_date on food_date.log_date_id = log_dates.id '
                        'left join food on food.id = food_date.food_id '
                        'group by log_dates.id order by log_dates.entry_date desc')
    results = cursor.fetchall()
    dates_results = []

    for i in results:
        single_date = dict()

        single_date['entry_date'] = i['entry_date']
        single_date['protein'] = i['protein']
        single_date['carbohydrates'] = i['carbohydrates']
        single_date['fat'] = i['fat']
        single_date['calories'] = i['calories']

        d = datetime.strptime(str(i['entry_date']), '%Y%m%d')
        single_date['pretty_date'] = datetime.strftime(d, '%B %d, %Y')
        dates_results.append(single_date)

    return render_template('home.html', dclasshome=class_variable, results=dates_results)


@app.route('/addFood', methods=['POST', 'GET'])
def addfood():
    db = get_db()
    class_variable = 'active'
    if request.method == 'POST':
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbohydrates = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])
        calories = protein * 4 + carbohydrates * 4 + fat * 9

        db.execute('insert into food(name, protein, carbohydrates, fat, calories) values (?,?,?,?,?) ',
                   [name, protein, carbohydrates, fat, calories])
        db.commit()

    cursor = db.execute('select name,protein,carbohydrates,fat,calories from food')
    results = cursor.fetchall()

    return render_template('add_food.html', dclassfood=class_variable, results=results)


@app.route('/view/<date>', methods=['POST', 'GET'])
def day(date):
    db = get_db()
    cursor = db.execute('select id, entry_date from log_dates where entry_date=?', [date])
    result = cursor.fetchone()

    if request.method == 'POST':

        db.execute('insert into food_date (food_id,log_date_id) values (?,?)',
                   [request.form['food-list'], result['id']])
        db.commit()

    d = datetime.strptime(str(result['entry_date']), '%Y%m%d')
    pretty_date = datetime.strftime(d, '%B %d , %Y')

    log_cursor = db.execute('select food.name, food.protein, food.carbohydrates, food.fat, food.calories from '
                            'log_dates join food_date on food_date.log_date_id=log_dates.id join food on '
                            'food.id=food_date.food_id where log_dates.entry_date=?', [date])
    log_list = log_cursor.fetchall()

    totals = {'protein': 0, 'carbohydrates': 0, 'fat': 0, 'calories': 0}
    keys = totals.keys()

    for i in keys:
        for food in log_list:
            totals[i] += food[i]

    food_cursor = db.execute('select id,name from food')
    food_list = food_cursor.fetchall()

    return render_template('day.html', entry_date=result['entry_date'],
                           pretty_date=pretty_date,
                           food_list=food_list,
                           log_result=log_list,
                           total=totals)
