from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, AppMaker, FavApps, User

# NEW IMPORTS FOR THIS STEP (OAuth)
from flask import session as login_session
import random, string

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "FavApps"


# Connect to Database and create database session
engine = create_engine('sqlite:///appmakerinfowithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    ''' 
        Due to the formatting for the result from the server token exchange we have to 
        split the token first on commas and select the first index which gives us the key : value 
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

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
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if the user is already logged in
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
    
    data = json.loads(answer.text)
    
    
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # Add provider to login
    login_session['provider'] = 'google'
    
    # See if user exists, if it doesn't, make a new one.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    # updatePhoto(user_id)
    

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions


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
    
'''def updatePhoto(user_id):
    thisUser = session.query(User).filter_by(id=user_id).one()
    thisUser.picture = login_session['picture']
    session.add(thisUser)
    session.commit()'''


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('access_token')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke token.
    access_token = login_session['credentials']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: ' 
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['credentials']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token'] 
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        print result['status']
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
    


# JSON APIs to view Appmaker Information  
@app.route('/appmaker/<int:appmaker_id>/favapp/JSON')
def appmakerAppsJSON(appmaker_id):
    appmaker = session.query(AppMaker).filter_by(id=appmaker_id).one()
    items = session.query(FavApps).filter_by(
        appmaker_id=appmaker_id).all()
    return jsonify(FavApp=[i.serialize for i in items])


@app.route('/appmaker/<int:appmaker_id>/favapp/<int:favapps_id>/JSON')
def favAppsJSON(appmaker_id, favapps_id):
    Fav_App = session.query(FavApps).filter_by(id=favapps_id).one()
    return jsonify(Fav_App=Fav_App.serialize)


@app.route('/appmaker/JSON')
def appmakersJSON():
    appmakers = session.query(AppMaker).all()
    return jsonify(appmakers=[r.serialize for r in appmakers])
  

# Show AppMakers
@app.route('/')
@app.route('/appmaker/')
def showAppMakers():
    appmakers = session.query(AppMaker).all()
    # page that will show AppMakers
    if 'username' not in login_session:
        return render_template('publicappmakers.html', appmakers=appmakers)
    else:
        return render_template('appmaker.html', appmakers=appmakers)

# Create new AppMaker
@app.route('/appmaker/new/', methods=['GET', 'POST'])
@login_required
def newAppMakers():
    # return "This page will be for making new appmakers."
    if request.method == 'POST':
        newAppMaker = AppMaker(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newAppMaker)
        flash('New Appmaker %s Successfully Created' % newAppMaker.name)
        session.commit()
        return redirect(url_for('showAppMakers'))
    else:
        return render_template('newappmaker.html')
    
# Edit an AppMaker
@app.route('/appmaker/<int:appmaker_id>/edit/', methods=['GET', 'POST'])
@login_required
def editAppMakers(appmaker_id):
    editedAppMaker = session.query(AppMaker).filter_by(id=appmaker_id).one()
    if editedAppMaker.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert(\
                'You are not authorized to edit this appmaker. \
                Please create your own appmaker in order to delete. \
                ');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedAppMaker.name = request.form['name']
        return redirect(url_for('showAppMakers'))
    else:
        return render_template(
                'editAppMaker.html', appmaker=editedAppMaker)
    #return "This page will be editing %s" % appmaker_id
    
# Delete an AppMaker    
@app.route('/appmaker/<int:appmaker_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteAppMakers(appmaker_id):
    #return "This page will be deleting %s" % appmaker_id
    appmakerToDelete = session.query(
    AppMaker).filter_by(id=appmaker_id).one()
    if appmakerToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert(\
                'You are not authorized to delete this appmaker. Please\
                create your own appmaker in order to delete.\
                ');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(appmakerToDelete)
        session.commit()
        return redirect(
        url_for('showAppMakers', appmaker_id=appmaker_id))
    else:
        return render_template(
        'deleteappmaker.html', appmaker=appmakerToDelete)

# Show FavApps
@app.route('/appmaker/<int:appmaker_id>/')
@app.route('/appmaker/<int:appmaker_id>/favapp/')
def showFavApps(appmaker_id):
    appmaker = session.query(AppMaker).filter_by(id=appmaker_id).one()
    items = session.query(FavApps).filter_by(
        appmaker_id=appmaker_id).all()
    creator = getUserInfo(appmaker.user_id)
    items = session.query(FavApps).filter_by(appmaker_id=appmaker_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicfavapps.html', items=items, appmaker=appmaker, creator=creator)
    else:
        return render_template('favapps.html', items=items, appmaker=appmaker, creator=creator)
        
    #return "This page will show all my FavApps."
    #return render_template('favapps.html', items=items, appmaker=appmaker)

# Create FavApps
@app.route('/appmaker/<int:appmaker_id>/favapp/new/', methods=['GET','POST'])
@login_required
def newFavApps(appmaker_id):
    appmaker = session.query(AppMaker).filter_by(id=appmaker_id).one()
    if request.method == 'POST':
        newItem = FavApps(name=request.form['name'], 
                    description=request.form['description'],
                    price=request.form['price'],
                    catch_phrase=request.form['catch_phrase'],
                    appmaker_id=appmaker_id,
                    user_id=appmaker.user_id)
        session.add(newItem)
        session.commit()
        flash("A FavApp has been created!")
        return redirect(url_for('showFavApps', appmaker_id=appmaker_id))
    else:
        return render_template('newfavapps.html', appmaker_id=appmaker_id)
    
# Edit FavApps
@app.route('/appmaker/<int:appmaker_id>/favapp/<int:favapps_id>/edit/', methods=['GET', 'POST'])
@login_required
def editFavApps(appmaker_id, favapps_id):
    # return "This page is for editing FavApps %s." % favapps_id
    editedItem = session.query(FavApps).filter_by(id=favapps_id).one()
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert(\
                'You are not authorized to edit this item. Please create \
                your own item in order to delete.');}</script><body \
                onload='myFunction()''>"
        if request.method == 'POST':
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['price']:
                editedItem.price = request.form['price']
            if request.form['catch_phrase']:
                editedItem.catch_phrase = request.form['catch_phrase']
                session.add(editedItem)
                session.commit()
                flash("A FavApp has been edited!")
            return redirect(url_for('showFavApps', appmaker_id=appmaker_id))
        else:
            return render_template(
                'editfavapps.html', appmaker_id=appmaker_id, favapps_id=favapps_id, item=editedItem)

@app.route('/appmaker/<int:appmaker_id>/favapp/<int:favapps_id>/delete',
            methods = ['GET', 'POST'])
@login_required
def deleteFavApps(appmaker_id, favapps_id):
    itemToDelete = session.query(FavApps).filter_by(id = favapps_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert(\
                'You are not authorized to delete this item. Please create \
                your own item in order to delete.');}</script><body \
                onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("A FavApps has been deleted.")
        return redirect(url_for('showFavApps', appmaker_id=appmaker_id))
    else:
        return render_template('deletefavapps.html', appmaker_id=appmaker_id, item=itemToDelete)
        
# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showAppMakers'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showAppMakers'))
    
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)  
    