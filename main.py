import datetime
import re
from flask import Flask,jsonify,request,make_response
from firebase import firebase
import jwt
from algoliasearch.search_client import SearchClient
from functools import wraps

#Algolia
client = SearchClient.create('Algolia app id', 'Algolia app key')
index = client.init_index('Doctors')

#Firebase Database
firebase = firebase.FirebaseApplication('link to firebase realtime database', None)

#Flask
app = Flask(__name__)


@app.route("/", methods = ['GET'])
def base_url():
    return jsonify('hello world')

    
@app.route("/login", methods = ['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    patients = firebase.get('opdoc-b7396-default-rtdb/patients',None)
    doctors = firebase.get('opdoc-b7396-default-rtdb/doctors',None)
    for account in patients:
        if email == patients[account]['email'] and patients[account]['password'] == password:
            #if user email and pssword are correct
            patients[account]['password'] = '***'
            return jsonify({'id' : account,
            'status' : True,
            'name' : patients[account]['name'],
            'account' : 'General'
            })
    for account in doctors:
        if email == doctors[account]['email'] and doctors[account]['password'] == password:
            #if user email and pssword are correct
            doctors[account]['password'] = '***'
            return jsonify({'status' : True,
            'id' : account,
            'name' : doctors[account]['name'],
            'account' : 'Professional'
            })

    # If creditinals adre invalid
    return jsonify({'status' : False})



@app.route("/register", methods = ['POST'])
def register():
    account_type = request.form["account"]
    name = request.form["name"]
    phone_no = request.form["phone number"]
    email = request.form["email"]
    city = request.form['city']
    password = request.form["password"]
    confirm = request.form["confirmation"]
    designation = request.form['designation']
    hospital = request.form['hospital']
    

    
    users = firebase.get('opdoc-b7396-default-rtdb/patients',None)
    doctors = firebase.get('opdoc-b7396-default-rtdb/doctors',None)
    ##Checks if user exists
    if users:
        for account in users:
            if email == users[account]['email']:
                return jsonify({'status' : True ,'exist' : True})
    if doctors:
        for account in doctors:
            if email == doctors[account]['email']:
                return jsonify({'status' : True ,'exist' : True})
    
    if password == confirm:
        if account_type == 'General':
            new_user = {
            "name" : name,
            "phone_no" : phone_no,
            "email" : email,
            'city' : city,
            "password" : password,
            "appointments":[],
            }
            id = firebase.post('opdoc-b7396-default-rtdb/patients',new_user)
            new_user['id'] = id['name']
            new_user['status'] = True
            new_user['exist'] = False
            new_user["password"] = '***'
            return jsonify(new_user)
        elif account_type == 'Professional':
            new_user = {
            "name" : name,
            "phone_no" : phone_no,
            "email" : email,
            "password" : password,
            "designation":designation,
            'hospital_name' : hospital,
            'city' : city,
            "appointments":[],
            "total_appointments":50,
            "online_appoinments":30,
            "rating" : 5,
            }
            id = firebase.post('opdoc-b7396-default-rtdb/doctors',new_user)
            new_user['id'] = id['name']
            new_user["password"] = '***'
            new_user['status'] = True
            new_user['exist'] = False
            ##Uploading data to algolia
            account = {
            'objectID' : id['name'],
            'Name' : name,
            'Designation' : designation,
            'Hospital' : hospital,
            'city' : city
            }
            
            index.save_object(account,{'autoGenerateObjectIDIfNotExist': True})
            return jsonify(new_user) 

    else:
        return jsonify({'status' : False ,'exist' : False})


@app.route('/bookapointment', methods =['POST'])
def bookAppointment():
    doctor_id = request.form['doctor_id']
    patient_id = request.form['patient_id']
    date = request.form['date']
    real_date = datetime.datetime.strptime(date,f"%d/%m/%Y")
    online_appoinments = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','online_appoinments')
    appointment_list =  firebase.get(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','appointments')
    patient_list = firebase.get(f'opdoc-b7396-default-rtdb/patients/{patient_id}','appointments')
    appointment = appointment_no = status = new_appointment = 0

    if appointment_list != None:
        doc_list = list(appointment_list)
        appointment_list = list(appointment_list)
        print(appointment_list)
        for i in doc_list:
            temp_date = datetime.datetime.strptime(i['date'],f"%d/%m/%Y")
            if temp_date != real_date:
                doc_list.remove(i)

    if appointment_list == None:
        appointment_no = 1
        status = False
        appointment = [{
            'patient_id' : patient_id,
            'status' : status,
            'appointment_no' : appointment_no,
            'date': date
        }]
        firebase.put(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','appointments',appointment)

    elif len(doc_list) < online_appoinments:
        print('entered')
        print(doc_list)
        appointment_no = len(doc_list) + 1
        status = False
        appointment = {
            'patient_id' : patient_id,
            'status' : status,
            'appointment_no' : appointment_no,
            'date': date
        }
        appointment_list.append(appointment)
        firebase.put(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','appointments',appointment_list)
        print('exit')

    else:
        return jsonify({'status' : False})

    if patient_list == None:
        new_appointment = [{
            'doctor_id' : doctor_id,
            'date' : date,
            'appointment_no' : appointment_no,
            'status' : False
        }]
        patient_list = new_appointment
    else:
        new_appointment = {
            'doctor_id' : doctor_id,
            'date' : date,
            'appointment_no' : appointment_no,
            'status' : False
        }
        patient_list = list(patient_list)
        patient_list.append(new_appointment)
    
    firebase.put(f'opdoc-b7396-default-rtdb/patients/{patient_id}',"appointments",patient_list)
    return jsonify({'status' : True})


@app.route('/profile',methods = ['POST'])
def profile():
    id = request.form['id']
    patients = firebase.get(f'opdoc-b7396-default-rtdb/patients/{id}',None)

    if patients:
        details ={
            "name" : patients['name'],
            "phone_no" : patients['phone_no'],
            "email" : patients['email'],
        }
        return jsonify(details)
    doctors = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{id}',None)
    if doctors:
        details ={
            "name" : doctors['name'],
            "phone_no" : doctors['phone_no'],
            "email" : doctors['email'],
            "designation" : doctors['designation'],
            'hospital_name' : doctors['hospital_name'],
            'rating' : doctors['rating'],
            'comments' : None
        }
        if 'comments' in doctors:
            details['comments'] = doctors['comments']
        return jsonify(details)
    
    return jsonify({'message' : 'Invalid Id'})


@app.route('/getappointments', methods = ['POST'])
def getAppointments():
    def keys(item):
            temp_date = datetime.datetime.strptime(item['date'],f"%d/%m/%Y")
            return temp_date
    id = request.form['id']
    appointments = firebase.get(f'opdoc-b7396-default-rtdb/patients/{id}','appointments')
    if appointments:
        appointments = list(appointments)
        def keys(item):
            temp_date = datetime.datetime.strptime(item['date'],f"%d/%m/%Y")
            return temp_date
        appointments.sort(reverse=True ,key = keys)
        return jsonify(appointments)
    appointments = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{id}','appointments')
    if appointments:
        appointments = list(appointments)
        appointments.sort(reverse=True ,key = keys)
        return jsonify(appointments)
    
    return jsonify({"message" : 'Invalid Id'})


@app.route('/upcomingappointments')
def upcomingAppointments():
    id = request.form['id']
    date = datetime.date.today()
    appointments = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{id}','appointments')

    if appointments:
        appointments = list(appointments)
        for i in appointments:
            if i['date'] != date:
                appointments.remove(i)
        def keys(e):
            return e['appointment_no']
        appointments.sort(key = keys)
        return jsonify(appointments)
    return jsonify({'message' : 'Invalid Id'})

@app.route('/search', methods = ['POST'])
def search():
    text = request.form['text']
    result = index.search(text,{'attributesToHighlight': None})
    return jsonify({'result':result['hits'] , 'count' : result['nbHits']})

@app.route('/addcomment',methods = ['POST'])
def addcomment():
    name= request.form['name']
    id = request.form['id']
    comment = request.form['comment']
    reviews = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{id}','comments')

    if reviews == None:
        reviews = [{
            'name' : name,
            'comment' : comment 
        }]
    else:
        reviews = list(reviews)
        reviews.append({
            'name' : name,
            'comment' : comment 
        })

    firebase.put(f'opdoc-b7396-default-rtdb/doctors/{id}','comments',reviews)
    return jsonify({'status' : True})


if __name__ == "__main__":
    app.run(debug = True)