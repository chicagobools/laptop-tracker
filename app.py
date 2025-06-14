from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laptops.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Laptop model
class Laptop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(100), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Library')
    notes = db.Column(db.String(4), nullable=True)
    logs = db.relationship('StatusLog',
                           backref='laptop',
                           lazy=True,
                           cascade='all, delete-orphan'
    )

class StatusLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptop.id'), nullable=False)
    old_status = db.Column(db.String(50), nullable=False)
    new_status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

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
    if request.method == 'POST':
        new_laptop = Laptop(
            barcode=request.form['barcode'],
            model=request.form['model'],
            status=request.form['status'],
            notes=request.form['notes'][:40]
        )
        db.session.add(new_laptop)
        db.session.commit()
        return redirect(url_for('laptops'))

    query = request.args.get('search', '').strip()

    if query:
        laptops = Laptop.query.filter(Laptop.barcode.ilike(f"%{query}%")).all()
    else:
        laptops = Laptop.query.all()
                    
    return render_template('laptops.html', laptops=laptops, query=query, StatusLog=StatusLog)

    #laptops = Laptop.query.all()
    #return render_template('laptops.html', laptops=laptops)

@app.route('/delete/<int:laptop_id>', methods=['POST'])
def delete_laptop(laptop_id):
    laptop = Laptop.query.get_or_404(laptop_id)
    db.session.delete(laptop)
    db.session.commit()
    return redirect(url_for('laptops'))


'''
@app.route('/laptops', methods=['GET', 'POST'])
def laptops():
    if request.method == 'POST':
        new_laptop = Laptop(
            barcode=request.form['barcode'],
            model=request.form['model'],
            status=request.form['status'],
            notes=request.form['notes'][:40]
        )
        db.session.add(new_laptop)
        db.session.commit()
        return redirect(url_for('laptops'))

    query = request.args.get('search', '').strip()
    if query:
        laptops = Laptop.query.filter(Laptop.barcode.ilike(f"%{query}%")).all()
    else:
        laptops = Laptop.query.all()
        
    return render_template('laptops.html', laptops=laptops, query=query)
''' 
    
if __name__ == '__main__':
    app.run(debug=True)

