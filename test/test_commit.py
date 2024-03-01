import time
import pytest

from test_utils import Swarm

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
    swarm = Swarm(PROGRAM_FILE_PATH, num_nodes)
    swarm.start(ELECTION_TIMEOUT)
    yield swarm
    swarm.clean()

def wait_for_commit(seconds=1):
    time.sleep(seconds)

@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_multi_leaders(swarm: Swarm, num_nodes: int):
    # get leader node, put topics and messages
    leader1 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader1 != None)
    assert (leader1.create_topic(TEST_TOPIC).json() == {"success": True})
    assert (leader1.put_message(TEST_TOPIC, TEST_MESSAGE).json() == {"success": True})
    
    # kill leader1 get leader2, get topics
    leader1.commit_clean(ELECTION_TIMEOUT)
    leader2 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader2 != None)
    assert (leader2.get_message(TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE})

    # kill leader2, get leader3, get topic and message
    leader2.commit_clean(ELECTION_TIMEOUT)
    leader3 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader3 != None)
    assert (leader3.get_topics().json() == {"success": True, "topics": [TEST_TOPIC]})
    assert (leader3.get_message(TEST_TOPIC).json() == {"success": False})

@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_complex_requests(swarm: Swarm, num_nodes: int):
    # get leader1
    leader1 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)
    assert (leader1 != None)
    assert leader1.get_message(TEST_TOPIC).json() == {"success": False}
    assert leader1.create_topic(TEST_TOPIC).json() == {"success": True}
    wait_for_commit(0.1)
    assert leader1.put_message(TEST_TOPIC, TEST_MESSAGE).json() == {"success": True}
    wait_for_commit(0.1)
    assert leader1.get_message(TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE}

    leader1.commit_clean(ELECTION_TIMEOUT)
    leader2 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert leader2 is not None
    assert leader2.get_message(TEST_TOPIC).json() == {"success": False}
    wait_for_commit(0.1)
    assert leader2.put_message(TEST_TOPIC, TEST_MESSAGE).json() == {"success": True}
    assert leader2.get_message(TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE}
    wait_for_commit(0.1)
    assert leader2.create_topic(TEST_TOPIC).json() == {"success": False}

    leader2.commit_clean(ELECTION_TIMEOUT)
    leader3 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert leader3 is not None
    assert leader3.put_message(TEST_TOPIC, TEST_MESSAGE).json() == {"success": True}
    wait_for_commit(0.1)
    assert leader3.get_topics().json() == {"success": True, "topics": [TEST_TOPIC]}
    assert leader3.get_message(TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE}


@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_follower_dead(swarm: Swarm, num_nodes: int):
    # get leader node, put topics and messages
    leader1 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader1 != None)
    assert (leader1.create_topic(TEST_TOPIC).json() == {"success": True})
    assert (leader1.put_message(TEST_TOPIC, TEST_MESSAGE).json() == {"success": True})
    
    follower_nodes = [node for node in swarm.nodes if node != leader1]
    assert len(follower_nodes) > 0
    node_to_remove = follower_nodes[0]
    node_to_remove.commit_clean(ELECTION_TIMEOUT)

    assert (leader1.create_topic(TEST_TOPIC_2).json() == {"success": True})
    assert (leader1.put_message(TEST_TOPIC_2, TEST_MESSAGE_2).json() == {"success": True})

    node_to_remove.start()

    time.sleep(ELECTION_TIMEOUT * NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    # 检查节点是否有所有的话题
    """
    topics = node_to_remove.get_topics().json()
    assert topics == {"success": True, "topics": [TEST_TOPIC, TEST_TOPIC_2]}
    
    for topic, expected_message in [(TEST_TOPIC, TEST_MESSAGE), (TEST_TOPIC_2, TEST_MESSAGE_2)]:
        message_response = node_to_remove.get_message(topic).json()
        assert message_response == {"success": True, "message": expected_message}
    """
    topics = node_to_remove.get_topics().json()
    assert (topics == {"success": True, "topics": [TEST_TOPIC, TEST_TOPIC_2]})
    
    """assert(node_to_remove.get_message(
        TEST_TOPIC_2).json() == {"success": True, "message": TEST_MESSAGE_2})
    """
    
    """assert(node_to_remove.get_message(
        TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE})
    """
    """
    message_response_test_topic = node_to_remove.get_message(TEST_TOPIC).json()
    print(f"Message for {TEST_TOPIC}:", message_response_test_topic)
    
    message_response_test_topic_2 = node_to_remove.get_message(TEST_TOPIC_2).json()
    print(f"Message for {TEST_TOPIC_2}:", message_response_test_topic_2)

    """
