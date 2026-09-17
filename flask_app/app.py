from flask import Flask, jsonify, request, render_template
from faker import Faker
import random
import uuid


def get_fake_email(first_name: str, last_name: str, fake: Faker):
    separator = random.choice(['.','-','_'])
    domain = fake.free_email_domain()
    return f"{first_name.lower()}{separator}{last_name.lower()}@{domain}"

def get_fake_record():
    fake = Faker()
    first_name = fake.first_name()
    last_name = fake.last_name()
    record = {
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
    }
    return record

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():

    try:  
        records = request.args.get('records', default=1, type=int)
        data = []
        for _ in range(records):
            data.append(get_fake_record())

        return jsonify({
            "status": "success",
            "records_counr": records,
            "data": data
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "failure",
            "error": str(e)
        }), 500

@app.route("/get-record")
def record_route():
    data = get_fake_record()
    if request.headers.get("HX-Request"):
        return render_template("partials/get_record.html", record=data)
    return render_template("index.html", record=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)