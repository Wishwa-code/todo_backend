from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient('mongodb+srv://vishva2017087:ckGzmJoKMoXkeMuQ@cluster0.i62acyf.mongodb.net/todoapp')
db = client.get_default_database()  # Get the default database
app.logger.info("Successfully connected to MongoDB")
tasks_collection = db['tasks']

# Helper function to convert ObjectId to string
def serialize_object_id(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Helper function to serialize a task
def serialize_task(task):
    # Helper function to handle datetime or string
    def parse_datetime(dt):
        if isinstance(dt, str):
            return datetime.fromisoformat(dt.rstrip('Z'))
        return dt
    
    dueDate = parse_datetime(task.get('dueDate', datetime.utcnow()))
    created_at = parse_datetime(task.get('created_at', datetime.utcnow()))
    updated_at = parse_datetime(task.get('updated_at', datetime.utcnow()))

    return {
        'id': serialize_object_id(task['_id']),
        'text': task['text'],
        'description': task.get('description', ''),
        'completed': task['completed'],
        'status': task.get('status', 'Pending'),
        'dueDate' : dueDate.isoformat() + 'z',
        'created_at': created_at.isoformat() + 'Z',
        'updated_at': updated_at.isoformat() + 'Z'
    }

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = list(tasks_collection.find())
    return jsonify([serialize_task(task) for task in tasks])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    task_data = request.json
    task_data['completed'] = False
    task_data['created_at'] = datetime.utcnow()
    task_data['updated_at'] = datetime.utcnow()
    result = tasks_collection.insert_one(task_data)
    new_task = tasks_collection.find_one({'_id': result.inserted_id})
    return jsonify(serialize_task(new_task)), 201

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    task = tasks_collection.find_one({'_id': ObjectId(task_id)})
    if task:
        return jsonify(serialize_task(task))
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    task_data = request.json
    task_data['updated_at'] = datetime.utcnow()
    result = tasks_collection.update_one(
        {'_id': ObjectId(task_id)},
        {'$set': task_data}
    )
    if result.modified_count:
        updated_task = tasks_collection.find_one({'_id': ObjectId(task_id)})
        return jsonify(serialize_task(updated_task))
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    result = tasks_collection.delete_one({'_id': ObjectId(task_id)})
    if result.deleted_count:
        return '', 204
    return jsonify({'error': 'Task not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)