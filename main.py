import datetime
from flask import Flask,jsonify,request,make_response
from firebase import firebase
import jwt
from algoliasearch.search_client import SearchClient
from functools import wraps

#Algolia
client = SearchClient.create('7DAT5C8CD8', 'd86b1174fc66519642a491d77e7a44bd')
index = client.init_index('Doctors')

#Firebase Database
firebase = firebase.FirebaseApplication('https://opdoc-b7396-default-rtdb.firebaseio.com/', None)

#Flask
app = Flask(__name__)

app.config['SECRET_KEY'] = 'Hrush!kesh'

# def token_required(f):
#     @wraps(f)
#     def decorated(*args,**kwargs):
#         token = request.args.get('token')

#         if not token:
#             return jsonify({'status' : False , 'message' : 'No token'}),403
#         try:
#             data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=['HS256'])
#             print(data)
#         except:
#             return jsonify({'status' : False , 'message' : 'Invalid token'}),403

#         return f(*args,**kwargs)

#     return decorated

@app.route("/", methods = ['GET'])
def base_url():
    return jsonify('hello world')

    
@app.route("/login", methods = ['GET'])
def login():
    email = request.form['email']
    password = request.form['password']
    users = firebase.get('opdoc-b7396-default-rtdb/patients',None)
    print(users)
    for account in users:
        print(account)
        if email == users[account]['email'] and users[account]['password'] == password:
            token = jwt.encode({"user": email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=100)} , app.config['SECRET_KEY'], algorithm="HS256")
            print("login sucessful")
            users[account]['password'] = '***'
            return jsonify({'token' : token,
            'status' : True,
            'details' : users[account],
            })
    
    print("Incorrrect credentials.")
    return make_response('Invalid Credentials',401,{'WWW-Authentication' : 'Login required'})



@app.route("/register", methods = ['POST'])
def register():
    account_type = request.form["account"]
    name = request.form["name"]
    phone_no = request.form["phone number"]
    email = request.form["email"]
    password = request.form["password"]
    confirm = request.form["confirmation"]
    
    users = firebase.get('opdoc-b7396-default-rtdb/patients',None)
    doctors = firebase.get('opdoc-b7396-default-rtdb/doctors',None)

    if users:
        for account in users:
            if email == users[account]['email']:
                return jsonify({'message' : 'Account already exists'})
    if doctors:
        for account in doctors:
            if email == doctors[account]['email']:
                return jsonify({'message' : 'Account already exists'})
    
    if password == confirm:
        token = jwt.encode({"user": email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=100)} , app.config['SECRET_KEY'], algorithm="HS256")
        if account_type == 'patient':
            new_user = {
            "name" : name,
            "phone_no" : phone_no,
            "email" : email,
            "password" : password,
            "appointments":[],
            "token" : token
            }
            id = firebase.post('opdoc-b7396-default-rtdb/patients',new_user)
            new_user['id'] = id['name']
            new_user["password"] = '***'
            return jsonify(new_user)
        elif account_type == 'doctor':
            new_user = {
            "name" : name,
            "phone_no" : phone_no,
            "email" : email,
            "password" : password,
            "designation":'MBBS',
            'hospital_name' : 'Aster',
            "history":[],
            "total_appointments":50,
            "online_appoinments":10,
            "upcoming_appointments": [],
            "rating" : 5,
            "token" : token
            }
            id = firebase.post('opdoc-b7396-default-rtdb/doctors',new_user)
            new_user['id'] = id['name']
            new_user["password"] = '***'

            account = {
            'objectID' : id,
            'Name' : name,
            'Designation' : 'MBBS',
            'Hospital' : 'Aster'
            }
            index.save_object(account,{'autoGenerateObjectIDIfNotExist': True})
            return jsonify(new_user) 

    else:
        return jsonify({"message" : "Passwords are not matched."})


@app.route('/bookapointment', methods =['POST'])
def bookAppointment():
    doctor_id = request.form['doctor_id']
    patient_id = request.form['patient_id']
    date = request.form['date']
    date = datetime.datetime.now() #####################################
    online_appoinments = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','online_appoinments')
    doc_list =  firebase.get(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','upcoming_appointments')
    patient_list = firebase.get(f'opdoc-b7396-default-rtdb/patients/{patient_id}','appointments')
    appointment = appointment_no = status = new_appointment = 0
    
    if doc_list == None:
        appointment_no = 1
        status = False
        appointment = [{
            'patient_id' : patient_id,
            'status' : status,
            'appointment_no' : appointment_no,
            'date': date
        }]
        firebase.put(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','upcoming_appointments',appointment)

    elif len(doc_list) < online_appoinments:
        appointment_no = len(doc_list) + 1
        status = False
        appointment = {
            'patient_id' : patient_id,
            'status' : status,
            'appointment_no' : appointment_no,
            'date': date
        }
        doc_list = list(doc_list)
        doc_list.append(appointment)
        firebase.put(f'opdoc-b7396-default-rtdb/doctors/{doctor_id}','upcoming_appointments',doc_list)

    else:
        return jsonify({'message' : 'No appointments'})

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
    return jsonify(new_appointment)


@app.route('/profile',methods = ['GET'])
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
            'rating' : doctors['rating']
        }
        return jsonify(details)
    
    return jsonify({'message' : 'Invalid Id'})


@app.route('/getappointments', methods = ['GET'])
def getAppointments():
    id = request.form['id']
    appointments = firebase.get(f'opdoc-b7396-default-rtdb/patients/{id}','appointments')
    if appointments:
        appointments = list(appointments)
        def keys(e):
            return e['date']
        appointments.sort(key = keys)
        return jsonify(appointments)
    appointments = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{id}','history')
    if appointments:
        appointments = list(appointments)
        def keys(e):
            return e['date']
        appointments.sort(key = keys)
        return jsonify(appointments)
    
    return jsonify({"message" : 'Invalid Id'})


@app.route('/upcomingappointments')
def upcomingAppointments():
    id = request.form['id']
    appointments = firebase.get(f'opdoc-b7396-default-rtdb/doctors/{id}','upcoming_appointments')
    if appointments:
        appointments = list(appointments)
        def keys(e):
            return e['date']
        appointments.sort(key = keys)
        return jsonify(appointments)
    return jsonify({'message' : 'Invalid Id'})

@app.route('/search', methods = ['GET'])
def search():
    text = request.form['text']
    result = index.search(text,{'attributesToHighlight': None})
    return jsonify(result['hits'])

if __name__ == "__main__":
    app.run(debug = True)