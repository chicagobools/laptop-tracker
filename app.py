from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev')

# SQLite DB config
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laptops.db'

# PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

# Laptop model
class Laptop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(40), unique=True, nullable=False)
    model = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(40), nullable=False, default='Library')
    notes = db.Column(db.String(40), nullable=True)
    logs = db.relationship('StatusLog',
                           backref='laptop',
                           lazy=True,
                           cascade='all, delete-orphan'
    )


class StatusLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptop.id'), nullable=False)
    old_status = db.Column(db.String(40), nullable=False)
    new_status = db.Column(db.String(40), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/update_status/<int:laptop_id>', methods=['POST'])
def update_status(laptop_id):
    laptop = Laptop.query.get_or_404(laptop_id)
    new_status = request.form['status']
    if laptop.status != new_status:
        log = StatusLog(
            laptop_id=laptop.id,
            old_status=laptop.status,
            new_status=new_status
        )
        db.session.add(log)
        laptop.status = new_status
        db.session.commit()
    return redirect(url_for('laptops'))
                        
@app.route('/')
def home():
    return redirect(url_for('laptops'))

@app.route('/laptops', methods=['GET', 'POST'])
def laptops():
    query = request.args.get('search', '')
    laptops = Laptop.query.filter(Laptop.barcode.contains(query)).all()

    if request.method == 'POST':
        barcode = request.form['barcode']
        model = request.form['model']
        status = request.form['status']
        notes = request.form['notes'][:40]



        # Server-side length validation
        if any([len(field) > 40 for field in [barcode, model, status, notes]]):
            flash("One or more fields exceed their allowed character limits.")
            return redirect(url_for("laptops"))

        existing = Laptop.query.filter_by(barcode=barcode).first()
        if existing:
            flash("That barcode already exists.")
            return redirect(url_for("laptops"))

        new_laptop = Laptop(
            barcode=barcode,
            model=model,
            status=status,
            notes=notes
        )

        db.session.add(new_laptop)
        db.session.commit()
        return redirect(url_for("laptops"))

    return render_template('laptops.html', laptops=laptops, query=query, StatusLog=StatusLog)

@app.route('/delete/<int:laptop_id>', methods=['POST'])
def delete_laptop(laptop_id):
    laptop = Laptop.query.get_or_404(laptop_id)
    db.session.delete(laptop)
    db.session.commit()
    return redirect(url_for('laptops'))

if __name__ == '__main__':
    app.run(debug=True)

