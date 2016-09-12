from flask import Flask,render_template,request,redirect,url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


#Fake Restaurants
restaurant = {'name':'TheCRUDdyCrab','id': '1'}

restaurants = [{'name':'The CRUDdy Crab','id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}



app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/restaurants',methods=['GET'])
@app.route('/')
def showRestaurants():
    restaurant_first = session.query(Restaurant).all()
    return render_template('restaurants.html',restaurant_first=restaurant_first)


@app.route('/restaurants/new',methods=['GET','POST'])
def newRestaurant():
    if request.method=='POST':
        newrestaurant=Restaurant(name=request.form['name'])
        session.add(newrestaurant)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newrestaurant.html')


@app.route('/restaurants/<int:restaurant_id>/edit',methods=['GET','POST'])
def editRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter(Restaurant.id==restaurant_id).one()
    if request.method=='POST':
        if request.form['name']:
            restaurant.name=request.form['name']
        session.add(restaurant)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
     return render_template('editrestaurant.html',restaurant_id=restaurant_id,restaurant=restaurant)

@app.route('/restaurants/<int:restaurant_id>/delete',methods=['GET','POST'])
def deleteRestaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    if request.method == 'POST':
      session.delete(restaurant)
      session.commit()
      return redirect(url_for('showRestaurants'))
    else:
      return render_template('deleterestaurant.html', restaurant_id=restaurant_id,restaurant=restaurant)


@app.route('/restaurants/<int:restaurant_id>')
@app.route('/restaurants/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter(Restaurant.id==restaurant_id).one()
    items = session.query(MenuItem).filter(restaurant_id==restaurant.id).all()
    return render_template('menu.html', restaurant_id=restaurant_id,items=items,restaurant=restaurant)


@app.route('/restaurants/<int:restaurant_id>/menu/new',methods=['GET','POST'])
def newMenuItem(restaurant_id):
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    if request.method == 'POST':
        newMenuItem = MenuItem(name=request.form['name'],course=request.form['course'],description=request.form['description'],price=request.form['price'])
        session.add(newMenuItem)
        session.commit()
        return redirect(url_for('showMenu',restaurant_id=restaurant_id))
    else:
        return render_template('newmenu.html', restaurant_id=restaurant_id,restaurant=restaurant)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit',methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    menu_item = session.query(MenuItem).filter(MenuItem.id == menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            menu_item.name = request.form['name']
            menu_item.course=request.form['course']
            menu_item.description=request.form['description']
            menu_item.price=request.form['price']
        session.add(menu_item)
        session.commit()
        return redirect(url_for('showMenu',restaurant_id=restaurant_id))
    else:
     return render_template('editmenu.html', restaurant_id=restaurant_id, menu_id=menu_id,item=item,restaurant=restaurant)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete',methods=['GET','POST'])
def deleteMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    menu_item = session.query(MenuItem).filter(MenuItem.id == menu_id).one()
    if request.method == 'POST':
        session.delete(menu_item)
        session.commit()
        return redirect(url_for('showMenu',restaurant_id=restaurant_id))
    return render_template('deletemenu.html', restaurant_id=restaurant_id, menu_id=menu_id,menu_item=menu_item,restaurant=restaurant)


if __name__=="__main__":
    app.debug=True
    app.run(host='0.0.0.0',port=5000)
