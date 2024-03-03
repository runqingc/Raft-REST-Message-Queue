import time
import pytest

from test_utils import Swarm

# Define an array for the number of nodes to be used in parameterized tests
NUM_NODES_ARRAY = [5]
PROGRAM_FILE_PATH = "../src/node.py"
TEST_TOPIC = "test_topic"
TEST_TOPIC_2 = "test_topic_2"
TEST_MESSAGE = "Test Message"
TEST_MESSAGE_2 = "Test Message_2"

ELECTION_TIMEOUT = 2.0
NUMBER_OF_LOOP_FOR_SEARCHING_LEADER = 3

@pytest.fixture
def swarm(num_nodes):
    """
    Setup a swarm of Raft nodes for testing.
    """
    swarm = Swarm(PROGRAM_FILE_PATH, num_nodes)
    swarm.start(ELECTION_TIMEOUT)
    yield swarm
    swarm.clean()

def wait_for_commit(seconds=1):
    """
    Wait for a specified amount of time to simulate commit delay.
    """
    time.sleep(seconds)





@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_all_followers_down_and_recovery(swarm: Swarm, num_nodes: int):
    """
    Test the cluster's ability to function and recover after multiple followers fail.
    """
    initial_leader = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)
    assert(initial_leader != None)

    # Shut down a majority of follower nodes
    followers_to_close = num_nodes - 1
    closed_followers = []
    for node in swarm.nodes:
        if node != initial_leader and len(closed_followers) < followers_to_close:
            node.clean()
            closed_followers.append(node)

    time.sleep(ELECTION_TIMEOUT * NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    # Attempt operations with a minority of nodes; expect failure
    response = initial_leader.create_topic(TEST_TOPIC_2).json()
    assert(response == {"success": False})

    # Restart the closed nodes
    for node in closed_followers:
        node.start()

    time.sleep(ELECTION_TIMEOUT * NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    # Verify the cluster can recover and elect a new leader
    new_leader = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)
    assert(new_leader != None)
    assert(new_leader.create_topic(TEST_TOPIC_2).json() == {"success": True})
