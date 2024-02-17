from flask import Flask, jsonify, request
import sys
import json
from raft_node import RaftNode
from threading import Thread

topics = {}

# Set up before request
raft_node = RaftNode()
internal_app = Flask("internal_app")
external_app = Flask("external_app")


# Topic APIs
# Put a topic
@external_app.route('/topic', methods=['PUT'])
def create_topic():
    topic = request.json.get('topic')
    if topic and topic not in topics:
        topics[topic] = []
        return jsonify(success=True)
    else:
        return jsonify(success=False), 400


# Return all the topics in a list
@external_app.route('/topic', methods=['GET'])
def get_topics():
    return jsonify(success=True, topics=list(topics.keys()))


# Message APIs
# Put a message
@external_app.route('/message', methods=['PUT'])
def put_message():
    topic = request.json.get('topic')
    message = request.json.get('message')
    if topic not in topics:
        return jsonify(success=False), 404
    else:
        topics[topic].append(message)
        return jsonify(success=True)


# Get a message
@external_app.route('/message/<topic>', methods=['GET'])
def get_message(topic):
    if topic not in topics or topics[topic] == []:
        return jsonify(success=False)
    else:
        message = topics[topic].pop(0)
        return jsonify(success=True, message=message)


# Status API
@external_app.route('/status', methods=['GET'])
def get_status():
    return jsonify(role=raft_node.role, term=raft_node.current_term)


# Request Vote RPC, logic to respond a vote request
# If term < candidate's term, update term to same as candidate
# Situation that will lead to NOT VOTE
# already voted at this term
# self.term is > candidate's term
# self log is more up to date (last log term > candidate's or last log index > candidate's)
# NOTE I DO NOT CHECK LOG FOR NOW BECAUSE I HAVE NOT IMPLEMENT REPLICATE LOG
# If grant vote, reset the election timeout
@internal_app.route('/request_vote', methods=['POST'])
def request_vote():
    data = request.json
    print(" node " + str(raft_node.id) + " received " +str(data))
    candidate_term = data['term']
    candidate_id = data['candidateId']
    last_log_index = data['lastLogIndex']
    last_log_term = data['lastLogTerm']

    # Add logic to compare logs in future
    if raft_node.last_voted_term >= candidate_term or raft_node.current_term > candidate_term:
        print(str(raft_node.id) + " do not grant vote to " + str(candidate_id))
        return jsonify(term=raft_node.current_term, voteGranted=False)
    else:
        raft_node.restart_election_timer()
        print(str(raft_node.id) + " grant vote to " + str(candidate_id))
        return jsonify(term=raft_node.current_term, voteGranted=True)


# Logic respond to append entries RPC
# Reset the election timeout
# Update term
# Change back to follower
@internal_app.route('/append_entries', methods=['POST'])
def append_entries():
    data = request.json
    leader_id = data["leaderId"]
    print("node " + str(raft_node.id) + "received APE from " + str(leader_id))
    raft_node.from_candidate_to_follower()
    raft_node.restart_election_timer()
    return jsonify(term=raft_node.current_term, success=True)


def run_internal():
    internal_app.run(debug=False, port=internal_port)


def run_external():
    external_app.run(debug=False, port=port)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 src/node.py config.json <index_of_node>")
        exit(1)

    config_path = sys.argv[1]
    index_of_node = int(sys.argv[2])

    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)

    raft_node.id = index_of_node
    port = config_data['addresses'][index_of_node]['port']
    internal_port = config_data['addresses'][index_of_node]['internal_port']
    raft_node.port = port
    raft_node.internal_port = internal_port

    t1 = Thread(target=run_internal)
    t2 = Thread(target=run_external)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
