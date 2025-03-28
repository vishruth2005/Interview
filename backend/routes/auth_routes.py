from flask import Blueprint, redirect, session, url_for, jsonify
from ..db.auth import auth0, requires_auth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login():
    return auth0.authorize_redirect(
        redirect_uri=url_for('auth.callback', _external=True)
    )

@auth_bp.route('/')
def callback():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'email': userinfo['email']
    }
    return redirect('/')

# @auth_bp.route('/logout')
# def logout():
#     session.clear()
#     return redirect(
#         f'https://{os.getenv("AUTH0_DOMAIN")}/v2/logout?'
#         f'client_id={os.getenv("AUTH0_CLIENT_ID")}&'
#         f'returnTo={url_for("home", _external=True)}'
#     )

@auth_bp.route('/is-authenticated')
def is_authenticated():
    return jsonify({'authenticated': 'profile' in session})
