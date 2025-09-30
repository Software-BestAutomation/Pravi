# from flask import Flask, render_template
# from flask_sqlalchemy import SQLAlchemy



# exp = Flask(__name__)
# exp.config['SECRET_KEY'] = 'your_secret_key'
# exp.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://DESKTOP-9TT6CR2\SQLEXPRESS/Pravi_DB?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes'
# exp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(exp)

# # Define the model
# class Defect(db.Model):
#     __tablename__ = 'DefectsCount'
#     id = db.Column(db.Integer, primary_key=True)
#     defects = db.Column(db.String(255), nullable=False)
#     counts = db.Column(db.Integer, nullable=False)


# # Route to render the defects page
# @exp.route('/')
# def home():
#     # Fetch all defects and their counts dynamically
#     defects_data = Defect.query.all()
#     return render_template('index.html', defects_data=defects_data)

import cv2
import data as dt
import numpy as np
import base64


