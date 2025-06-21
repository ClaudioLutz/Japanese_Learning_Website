#!/usr/bin/env python3
"""
Simple redirect server for old admin URLs.
This handles any bookmarks or links to the old /admin/login route.
"""

from flask import Flask, redirect, url_for

app = Flask(__name__)

@app.route('/admin/login')
def old_admin_login():
    """Redirect old admin login to new unified login"""
    return redirect('http://localhost:5000/login')

@app.route('/admin')
@app.route('/admin/')
def old_admin_index():
    """Redirect old admin index to new unified login"""
    return redirect('http://localhost:5000/login')

@app.route('/')
def index():
    """Redirect root to new unified system"""
    return redirect('http://localhost:5000/')

if __name__ == '__main__':
    print("Old admin redirect server running on port 5001")
    print("Redirecting old admin URLs to the new unified system on port 5000")
    app.run(debug=True, port=5001)
