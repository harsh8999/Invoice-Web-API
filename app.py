from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_cors import CORS
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import Column,ForeignKey,Integer, String, update
from sqlalchemy.orm import relationship,session
from itertools import zip_longest


app = Flask(__name__)
CORS(app)
api = Api(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'prod.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db = SQLAlchemy(app)    #instance of database


class Customer(db.Model):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True, autoincrement=True)
    total = Column(Integer)
    subtotal = Column(Integer)
    discount = Column(Integer)
    tax = Column(Integer)
    product = relationship('Product',backref='customer', cascade='all,delete')


class Product(db.Model):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(50))
    quantity = Column(Integer)
    price = Column(Integer)
    amount = Column(Integer)
    
    cust_id = Column(Integer, ForeignKey('customer.id'))
 
@app.route("/bill",methods=['POST'])
def addProd():
    print(request.json)
    disc = request.json['total']['discount']
    tot = request.json['total']['total']
    subtot = request.json['total']['subtotal']
    ta = request.json['total']['tax']
    cust = Customer(discount=disc,total=tot,subtotal=subtot,tax=ta)   #add user
    db.session.add(cust)
    db.session.commit()

    for data in request.json['item']:
        name_ = data['name']
        quantity_ = data['quantity']
        price_ = data['price']
        amount_ = data['amount']

        prod = Product(name = name_, quantity = quantity_, price=price_ , amount=amount_ , customer=cust)
        db.session.add(prod)
        db.session.commit()
        
    return jsonify('done')




@app.route('/bill',methods=['GET'])
def get_bill():
    cArr = Customer.query.all()
    cust = dict()
    final = []
    for customer in cArr:
        cust = dict(id=customer.id,total=customer.total,subtotal=customer.subtotal,discount=customer.discount,tax=customer.tax,item=[])
        for product in Product.query.filter(Product.cust_id==customer.id):
            item=dict(
                    name=product.name, 
                    quantity = product.quantity, 
                    price=product.price , 
                    amount=product.amount , 
                    customer=product.cust_id
                    )
            cust['item'].append(item)
        final.append(cust)    
        print(final)
    return jsonify(final)

@app.route('/bill/<int:idreceived>',methods=['GET'])
def get_bill_by_id(idreceived):
    customer = Customer.query.filter(Customer.id == idreceived).first()
    cust = dict()    
    
    cust = dict(id=customer.id,total=customer.total,subtotal=customer.subtotal,discount=customer.discount,tax=customer.tax,item=[])
    for product in Product.query.filter(Product.cust_id == customer.id):
        item=dict(
                name=product.name, 
                quantity = product.quantity, 
                price=product.price , 
                amount=product.amount , 
                customer=product.cust_id
                )
        cust['item'].append(item)
       
    
    return jsonify(cust)


@app.route("/bill/<int:id>",methods=['PUT'])
def updateProd(id):
    # print("----------------PUT-------------")
    # print(id)
    # print(request.json)
    disc = request.json['discount']
    tot = request.json['total']
    subtot = request.json['subtotal']
    ta = request.json['tax']
    cust = Customer.query.filter_by(id=id).first()
    cust.discount = disc
    cust.total = tot
    cust.subtotal = subtot
    cust.tax = ta
    
    for product, data in zip_longest(Product.query.filter(Product.cust_id == cust.id), request.json['item']):
        
        print('product',product,"data",data)
        
        if product != None and data != None:
            if product.cust_id == id:
                
                product.quantity = data['quantity']
                product.name = data['name']
                product.price = data['price']
                product.amount = data['amount']
        elif data==None:
            db.session.delete(product)

        elif product == None:
            name_ = data['name']
            quantity_ = data['quantity']
            price_ = data['price']
            amount_ = data['amount']

            prod = Product(name = name_, quantity = quantity_, price=price_ , amount=amount_ , customer=cust)
            db.session.add(prod)
            db.session.commit()
    db.session.commit()    
    return jsonify('put done')


@app.route("/bill/<int:id>",methods=['DELETE'])    
def deleteInvoice(id):
    customer = Customer.query.filter(Customer.id==id).first()
    db.session.delete(customer)
    db.session.commit()
    return jsonify('delete done')

if __name__ == '__main__':
    app.run(debug=True)