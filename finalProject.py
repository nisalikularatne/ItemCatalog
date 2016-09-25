from flask import Flask,render_template,request,redirect,url_for,flash,jsonify
from flask import session as login_session
import random,string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category,CategoryItem,User
from sqlalchemy.engine import Engine
from sqlalchemy import event
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()



category = {'name':'TheCRUDdyCrab','id': '1'}

categorys = [{'name':'The CRUDdy Crab','id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]



items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}



app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.debug = True

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "category item app"
engine = create_engine('sqlite:///categorywithitems.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token

    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']


    user_id=getUserID(login_session['email'])
    if not user_id:
        user_id=createUser(login_session)
        login_session['user_id']=user_id

    login_session['user_id']=user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


@app.route('/clearSession')
def clearSession():
    login_session.clear()
    flash("logged out")
    return redirect('/category')

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:

        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % credentials
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print
    'result is '
    print
    result
    if result['status'] == '200':

        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response





@app.route('/categorys/<int:category_id>/item/JSON')
def categoryItemJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    return jsonify(CategoryItems=[i.serialize for i in items])

@app.route('/categorys/<int:category_id>/item/<int:item_id>/JSON')
def ItemJSON(category_id,item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(
        id=item_id).all()
    return jsonify(CategoryItems=[i.serialize for i in items])


@app.route('/category',methods=['GET'])
@app.route('/')
def showcategory():
    category_first = session.query(Category).all()


    if 'username' not in login_session:
        return render_template('publiccategory.html', category_first=category_first)
    else:
        user = session.query(User).filter_by(name=login_session['username']).one()
        return render_template('category.html',category_first=category_first,user=user)


@app.route('/category/new',methods=['GET','POST'])
def newcategory():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method=='POST':
        newcategory=Category(name=request.form['name'],user_id=login_session['user_id'])
        session.add(newcategory)
        session.commit()
        flash('new category created')
        return redirect(url_for('showcategory'))
    else:
        return render_template('newcategory.html')


@app.route('/category/<int:category_id>/edit',methods=['GET','POST'])
def editcategory(category_id):
    category = session.query(Category).filter(Category.id==category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction()''>"
    if request.method=='POST':
        if request.form['name']:
            category.name=request.form['name']
        session.add(category)
        session.commit()
        flash('category edited')
        return redirect(url_for('showcategory'))
    else:
     return render_template('editcategory.html',category_id=category_id,category=category)

@app.route('/category/<int:category_id>/delete',methods=['GET','POST'])
def deletecategory(category_id):

    category = session.query(Category).filter(Category.id == category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this category. Please create your own category in order to delete.');}</script><body onload='myFunction()''> "
    if request.method == 'POST':
      session.delete(category)
      session.commit()
      flash('category deleted')
      return redirect(url_for('showcategory'))
    else:
      return render_template('deletecategory.html', category_id=category_id,category=category)


@app.route('/category/<int:category_id>')
@app.route('/category/<int:category_id>/item',methods=['GET','POST'])
def showItem(category_id):
    category = session.query(Category).filter(Category.id==category_id).one()
    creator = getUserInfo(category.user_id)
    items = session.query(CategoryItem).filter(category_id == CategoryItem.category_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicitem.html', items=items, category=category, creator=creator)
    else:
        return render_template('item.html', items=items, category=category, creator=creator)



@app.route('/category/<int:category_id>/item/new',methods=['GET','POST'])
def newCategoryItem(category_id):
    category = session.query(Category).filter(Category.id == category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add items to this category. Please create your own category in order to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newCategoryItem = CategoryItem(name=request.form['name'],description=request.form['description'],price=request.form['price'],category_id=category_id, user_id=category.user_id)
        session.add(newCategoryItem)
        session.commit()
        flash('new item created')
        return redirect(url_for('showItem',category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id,category=category)


@app.route('/category/<int:category_id>/item/<int:item_id>/edit',methods=['GET','POST'])
def editCategoryItem(category_id, item_id):
    category = session.query(Category).filter(Category.id == category_id).one()
    category_item = session.query(CategoryItem).filter(CategoryItem.id == item_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            category_item.name = request.form['name']
            category_item.description=request.form['description']
            category_item.price=request.form['price']
        session.add(category_item)
        session.commit()
        flash('category item edited')
        return redirect(url_for('showItem',category_id=category_id))
    else:
     return render_template('edititem.html', category_id=category_id, item_id=item_id,category_item=category_item,category=category)


@app.route('/category/<int:category_id>/item/<int:item_id>/delete',methods=['GET','POST'])
def deleteCategoryItem(category_id, item_id):
    category = session.query(Category).filter(Category.id == category_id).one()
    category_item = session.query(CategoryItem).filter(CategoryItem.id == item_id).one()
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        session.delete(category_item)
        session.commit()
        flash('category item deleted')
        return redirect(url_for('showItem',category_id=category_id))
    return render_template('deleteitem.html', category_id=category_id, item_id=item_id,category_item=category_item,category=category)


if __name__=="__main__":
    app.secret_key='super_secret_key'
    app.debug=True
    app.run(host='0.0.0.0',port=5000)
