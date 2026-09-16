from flask import Flask, jsonify, request
from faker import Faker
from random import randint
import uuid

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():

    try:
        count = request.args.get('count', default=10, type=int)
        fake = Faker()
        data = []
        for _ in range(count):
            data.append({
                "id": str(uuid.uuid4()),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "address": fake.address(),
                "emails": [fake.free_email() for _ in range(randint(1, 3))],
                "phones": [fake.basic_phone_number() for _ in range(randint(1, 3))],
            })
        return jsonify({
            "status": "success",
            "count": count,
            "data": data
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "failure",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)