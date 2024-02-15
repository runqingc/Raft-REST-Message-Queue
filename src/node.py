from flask import Flask, jsonify, request
import sys
import json

app = Flask(__name__)

topics = {}


# Topic APIs

# Put a topic
@app.route('/topic', methods=['PUT'])
def create_topic():
    topic = request.json.get('topic')
    if topic and topic not in topics:
        topics[topic] = []
        return jsonify(success=True)
    else:
        return jsonify(success=False), 400


# Return all the topics in a list
@app.route('/topic', methods=['GET'])
def get_topics():
    return jsonify(success=True, topics=list(topics.keys()))


# Message APIs
# Get a message
@app.route('/message', methods=['PUT'])
def put_message():
    topic = request.json.get('topic')
    message = request.json.get('message')
    if topic not in topics:
        return jsonify(success=False), 404
    else:
        topics[topic].append(message)
        return jsonify(success=True)


@app.route('/message/<topic>', methods=['GET'])
def get_message(topic):
    if topic not in topics or topics[topic] == []:
        return jsonify(success=False)
    else:
        message = topics[topic].pop(0)
        return jsonify(success=True, message=message)


@app.route('/status', methods=['GET'])
def get_status():
    pass





if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 src/node.py config.json <index_of_node>")
        exit(1)

    config_path = sys.argv[1]
    index_of_node = int(sys.argv[2])

    with open(config_path, 'r') as config_file:
        data = json.load(config_file)

    port = data['addresses'][index_of_node]['port']

    app.run(debug=True, port=port)

