from flask import Flask, jsonify, request
from faker import Faker
import random
import uuid


def get_fake_email(first_name: str, last_name: str, fake: Faker):
    separator = random.choice(['.','-','_'])
    domain = fake.free_email_domain()
    return f"{first_name.lower()}{separator}{last_name.lower()}@{domain}"

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():

    try:
        count = request.args.get('count', default=10, type=int)
        fake = Faker()
        data = []
        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            data.append({
                "id": str(uuid.uuid4()),
                "first_name": first_name,
                "last_name": last_name,
                "address": fake.address(),
                "email": get_fake_email(first_name=first_name, last_name=last_name, fake=fake),
                "phones": [fake.basic_phone_number() for _ in range(random.randint(1, 2))],
                "orders": [{
                    "item": uuid.uuid4(),
                    "color": fake.color_name(),
                    "cc_number": fake.credit_card_number(),
                    "total": random.randint(500, 50000)/100
                } for _ in range(random.randint(1, 4))]
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