import pytest
import time

from test_utils import Swarm, simulate_network_partition, restore_network

NUM_NODES_ARRAY = [10]
PROGRAM_FILE_PATH = "../src/node.py"
TEST_TOPIC_PARTITION_1 = "test_topic_partition_1"
TEST_TOPIC_PARTITION_2 = "test_topic_partition_2"
TEST_MESSAGE_PARTITION_1 = "Test Message for Partition 1"
TEST_MESSAGE_PARTITION_2 = "Test Message for Partition 2"

ELECTION_TIMEOUT = 2.0
NUMBER_OF_LOOP_FOR_SEARCHING_LEADER = 3

@pytest.fixture
def swarm(num_nodes):
    swarm = Swarm(PROGRAM_FILE_PATH, num_nodes)
    swarm.start(ELECTION_TIMEOUT)
    yield swarm
    swarm.clean()

@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_network_partition(swarm: Swarm, num_nodes: int):
    # 等待领导者选举完成
    initial_leader = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)
    assert initial_leader is not None

    # 模拟网络分区
    partition1, partition2 = swarm.simulate_network_partition(swarm)

    # 分区1内操作
    leader1 = partition1.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)
    assert leader1.create_topic(TEST_TOPIC_PARTITION_1).json() == {"success": True}
    assert leader1.put_message(TEST_TOPIC_PARTITION_1, TEST_MESSAGE_PARTITION_1).json() == {"success": True}

    # 分区2内操作
    leader2 = partition2.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)
    assert leader2.create_topic(TEST_TOPIC_PARTITION_2).json() == {"success": True}
    assert leader2.put_message(TEST_TOPIC_PARTITION_2, TEST_MESSAGE_PARTITION_2).json() == {"success": True}

    # 恢复网络连接
    swarm.restore_network(swarm)

    # 等待系统稳定
    time.sleep(ELECTION_TIMEOUT * NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    # 验证数据一致性
    new_leader = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)
    topics = new_leader.get_topics().json()["topics"]
    assert TEST_TOPIC_PARTITION_1 in topics and TEST_TOPIC_PARTITION_2 in topics

    message1 = new_leader.get_message(TEST_TOPIC_PARTITION_1).json()["message"]
    message2 = new_leader.get_message(TEST_TOPIC_PARTITION_2).json()["message"]
    assert message1 == TEST_MESSAGE_PARTITION_1 and message2 == TEST_MESSAGE_PARTITION_2
