from flask import Flask, jsonify, request
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import json
import time
from raft_node import RaftNode
from threading import Thread
from log import Log

PUT_TOPIC_FLAG = 1
PUT_MESSAGE_FLAG = 2
GET_TOPIC_FLAG = -1
GET_MESSAGE_FLAG = -2

CLIENT_REQUEST_TIMEOUT = 1
topics = {}

# Set up before request
raft_node = RaftNode()
internal_app = Flask("internal_app")
external_app = Flask("external_app")


def wait_for_commit(log_index, timeout):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if raft_node.commit_index >= log_index:
            return True
        time.sleep(0.1)
    return False


# Topic APIs
# Put a topic
@external_app.route('/topic', methods=['PUT'])
def create_topic():
    topic = request.json.get('topic')
    # add to log
    # wait for follower's reply
    # check continuously if the commit_index has covered the index in log
    # if true, then apply to state machine and return true to client
    # if timed out, return false to client
    if topic and topic not in raft_node.state_machine:
        this_index = len(raft_node.logs)
        raft_node.logs.append(Log(raft_node.current_term, topic, "", PUT_TOPIC_FLAG))
        print(str(raft_node.id) + " leader write a new log: " + str(raft_node.logs))
        raft_node.match_index[raft_node.id] = this_index
        # case 1: only 1 node in swarm, no need to wait majority consent
        if len(raft_node.config['addresses']) == 1:
            raft_node.apply_to_state_machine(this_index)
            return jsonify(success=True)
        # case 2: > 1 node in swarm, wait until success
        log_index = len(raft_node.logs) - 1
        with ThreadPoolExecutor() as executor:
            future = executor.submit(wait_for_commit, log_index, CLIENT_REQUEST_TIMEOUT)
            success = future.result()
        if success:
            raft_node.apply_to_state_machine(this_index)
            return jsonify(success=True)
        else:
            return jsonify(success=False), 408
    else:
        return jsonify(success=False), 400


# Return all the topics in a list
@external_app.route('/topic', methods=['GET'])
def get_topics():
    return jsonify(success=True, topics=list(raft_node.state_machine.keys()))


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
    print(" node " + str(raft_node.id) + " received " + str(data))
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

    raft_node.from_candidate_to_follower()
    # raft_node.restart_election_timer()
    # make the node's log same as leader's log
    raft_node.logs = [Log.from_dict(entry) for entry in data["entries"]]
    print("node " + str(raft_node.id) + "received APE from " + str(leader_id) + " logs: " + str(raft_node.logs))
    # commit to same stage as leader does [TO DO]
    # if leader_commit > my_last_commit, then commit these logs
    if data["leaderCommit"] > raft_node.commit_index:
        raft_node.follower_commit(data["leaderCommit"])
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
