import random
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread, Event
from threading import Lock

import requests

CONFIG_PATH = "../config.json"

FOLLOWER = "Follower"
LEADER = "Leader"
CANDIDATE = "Candidate"

MIN_ELECTION_TIMEOUT = 0.15
MAX_ELECTION_TIMEOUT = 0.3
HEARTBEAT_INTERVAL = 0.02


def get_randomized_election_timeout():
    return random.uniform(MIN_ELECTION_TIMEOUT, MAX_ELECTION_TIMEOUT)


def send_request_vote(server, data):
    # print(f'http://{server["ip"]}:{server["internal_port"]}/request_vote')
    try:
        # print(server)
        # print("server type: " + str(type(server)))
        response = requests.post(f'http://{server["ip"]}:{server["internal_port"]}/request_vote', json=data)
        print("response = " + str(response))
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException:
        return None


def send_append_entries(server, data):
    try:
        response = requests.post(f'http://{server["ip"]}:{server["internal_port"]}/append_entries', json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException:
        return None


class RaftNode:
    def __init__(self):
        # Configure information

        self.id = -1
        self.port = -1
        self.internal_port = -1

        self.current_term = 0
        self.logs = []
        self.role = FOLLOWER
        # Vote information
        self.vote_count = 0
        self.state_lock = Lock()
        # Leader related
        self.heartbeat_thread = None
        # change according to need
        self.last_voted_term = -1
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = {}
        self.match_index = {}

        # Timer used to track the election timeout
        self.timer_generation = 0
        self.election_timeout_event = Event()
        self.start_election_timer()
        self.election_timeout_thread = None

    # Timer handling methods
    def start_election_timer(self):
        current_generation = self.timer_generation
        self.election_timeout_thread = Thread(target=self.handle_election_timeout, args=(current_generation,))
        self.election_timeout_thread.daemon = True
        self.election_timeout_thread.start()

    def handle_election_timeout(self, my_generation):
        time_duration = get_randomized_election_timeout()
        election_timeout_occurred = not self.election_timeout_event.wait(time_duration)
        if election_timeout_occurred and self.role is not LEADER and my_generation == self.timer_generation:
            print("node" + str(self.id) + "changed to candidate")
            # Election timed out and change to candidate
            self.from_follower_to_candidate()

    def restart_election_timer(self):
        self.timer_generation += 1
        self.election_timeout_event.clear()
        self.start_election_timer()

    def from_follower_to_candidate(self):
        # Increase current term
        # Change to candidate
        # Vote for itself (May then be leader if there's only one node)
        # Update last_voted_term
        # Issue Request Vote RPC in parallel to others
        # Reset election timeout
        self.current_term += 1
        self.role = CANDIDATE
        self.vote_count += 1
        self.last_voted_term = self.current_term
        garbage = -1

        with open("../config.json", 'r') as config_file:
            config = json.load(config_file)

        # Address the case with single node
        if len(config['addresses']) == 1:
            self.from_candidate_to_leader()
            return

        data = {
            "term": self.current_term,
            "candidateId": self.id,
            "lastLogIndex": garbage,
            "lastLogTerm": garbage
        }

        # Send request Vote in parallel
        # with ThreadPoolExecutor() as executor:
        with ThreadPoolExecutor() as executor:
            futures = []
            for server in config['addresses']:
                if server["internal_port"] != self.internal_port:
                    futures.append(executor.submit(send_request_vote, server, data))

            for future in as_completed(futures):
                result = future.result()
                print("node " + str(self.id) + " result = " + str(result))
                if result and result.get('term') > self.current_term:
                    self.current_term = result.get('term')
                    self.from_candidate_to_follower()
                    break
                if result and result.get('voteGranted') and self.role == CANDIDATE:
                    with self.state_lock:
                        self.vote_count += 1
                        if self.vote_count > len(config['addresses']) / 2:
                            self.from_candidate_to_leader()  # Transition to leader if majority votes received
                            break

        self.restart_election_timer()

    # Send append entries RPC to all others so that it can be recognized
    # Clear all votes received
    def from_candidate_to_leader(self):
        print(str(self.id) + " CHANGED TO LEADER")
        # with self.state_lock:
        self.role = LEADER
        self.vote_count = 0
        # Send append entries RPC to all others so that it can be recognized
        print(str(self.id) + " READY TO START HEARTBEAT")
        self.heartbeat_thread = Thread(target=self.start_heartbeat_loop)
        self.heartbeat_thread.start()

    def send_heartbeat(self):
        data = {
            "term": self.current_term,
            "leaderId": self.id,
            "prevLogIndex": len(self.logs) - 1 if self.logs else 0,
            "prevLogTerm": self.logs[-1]["term"] if self.logs else 0,
            "entries": [],  # No new entries to replicate initially
            "leaderCommit": self.commit_index,
        }

        with open("../config.json", 'r') as config_file:
            config = json.load(config_file)

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(send_append_entries, server, data)
                for server in config['addresses'] if server["internal_port"] != self.internal_port]
            # if one do not receive, re-send
            for future in as_completed(futures):
                result = future.result()

    def start_heartbeat_loop(self):
        print("node " + str(self.id) + "started heart_beat_loop")
        while self.role == LEADER:
            self.send_heartbeat()
            time.sleep(HEARTBEAT_INTERVAL)

    # Called when receive append entries RPC
    # Clear all votes received
    # Reset the election timeout
    def from_candidate_to_follower(self):
        self.role = FOLLOWER
        self.vote_count = 0
        self.restart_election_timer()

    def from_leader_to_candidate(self):
        self.role = FOLLOWER
        self.heartbeat_thread.join()
