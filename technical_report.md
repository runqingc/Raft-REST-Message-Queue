# RRMQ Technical Report

## 1. Introduction

This report delves into the implementation specifics of the Raft consensus algorithm within the Raft REST Message Queue (RRMQ) project. Emphasizing the core aspects of leader election, log replication, and fault tolerance, we detail how these components collectively ensure a consistent, distributed state across nodes in the system.

## 2. Code Structure

The implementation is divided into three primary Python files:

- `raft_node.py`: Contains the `RaftNode` class, implementing the core Raft protocol, including leader election, log replication, and maintaining the node's state. The nodes maintained several important variables shown below:

  - | Variable                                                     | Description                                                  |
    | ------------------------------------------------------------ | ------------------------------------------------------------ |
    | `id`, `port`, `internal_port`                                | Identifiers and communication endpoints.                     |
    | `current_term`                                               | The node's current term in the election.                     |
    | `logs`                                                       | Log entries for replication.                                 |
    | `state_machine`                                              | The application state managed by the cluster.                |
    | `role`                                                       | Node's role: Follower, Leader, or Candidate.                 |
    | `vote_count`                                                 | Votes received in the current election.                      |
    | `state_lock`                                                 | Synchronizes access to shared resources.                     |
    | `heartbeat_thread`                                           | Sends heartbeats to other nodes as the leader.               |
    | `last_voted_term`, `commit_index`, `last_applied`            | Voting history, highest committed log entry, and highest applied log entry. |
    | `next_index`, `match_index`                                  | Tracks log replication progress on followers.                |
    | `heartbeat_received`                                         | Tracks heartbeats from each node.                            |
    | `timer_generation`, `election_timeout_event`, `election_timeout_thread` | Manages the election timeout mechanism.                      |

- `node.py`: Utilizes Flask to create RESTful APIs for external and internal communication, handling client requests and inter-node communication.

  - `internal_app` for internal communications within the Raft cluster, such as leader elections and log replication
  - `external_app` for external interactions, handling client requests to the raft swam. 

- `log.py`: Defines the `Log` class, representing the log entries that are replicated across nodes to ensure consistency.

  - 
    The `Log` class maintains the following variables:

    | Variable    | Description                                                |
    | ----------- | ---------------------------------------------------------- |
    | `term`      | The term number in which the log entry was created.        |
    | `topic`     | The topic associated with the log entry.                   |
    | `message`   | The message content of the log entry.                      |
    | `operation` | The operation type, indicating the action to be performed. |

    Operations include:

    - `PUT_TOPIC_FLAG` (+1) for adding a new topic.
    - `PUT_MESSAGE_FLAG` (+2) for adding a new message to a topic.
    - `GET_TOPIC_FLAG` (-1) for retrieving topics (not explicitly used in the provided `Log` class).
    - `GET_MESSAGE_FLAG` (-2) for consuming a message from a topic.



## 3. Part2 Message Queue Implementation

- ### Topic

  #### PUT Topic

  - **Process Flow**:
    - Checks if the current node is the leader. If not, returns an error (HTTP 400).
    - Validates if the topic exists. If it does or no topic is provided, returns an error (HTTP 400).
    - If the topic is new, it adds a log entry with the `PUT_TOPIC_FLAG`.
    - Waits for the log entry to be committed to the state machine.
      - If successful, applies the log to the state machine and returns success.
      - If not successful within a certain timeout, returns an error (HTTP 408).
  - **Involved Methods and Logic**:
    - `create_topic()`: Main function to handle PUT topic requests.
    - `add_log_entry(term, topic, message="", flag=None)`: Adds a new log entry for the topic.
    - `await_commit_confirmation(log_index)`: Waits for the commit confirmation of the log entry.

  #### GET Topic

  - **Process Flow**:
    - Returns a list of all topics stored in the state machine.
  - **Involved Methods and Logic**:
    - `get_topics()`: Main function to handle GET topic requests.

  ### Message

  #### PUT Message

  - **Process Flow**:
    - Checks if the current node is the leader. If not, returns an error (HTTP 400).
    - Validates if the topic exists. If not, returns an error (HTTP 404).
    - If the topic exists, adds a log entry with the `PUT_MESSAGE_FLAG` and the message.
    - Waits for the log entry to be committed to the state machine.
      - If successful, applies the log to the state machine and returns success.
      - If not successful within a certain timeout, returns an error (HTTP 408).
  - **Involved Methods and Logic**:
    - `put_message()`: Main function to handle PUT message requests.
    - Uses `add_log_entry` and `await_commit_confirmation` similar to PUT Topic.

  #### GET Message

  - **Process Flow**:
    - Checks if the current node is the leader. If not, returns an error (HTTP 400).
    - Validates if the topic exists and has messages. If not, returns an error.
    - Adds a log entry with the `GET_MESSAGE_FLAG`.
    - Waits for the log entry to be committed to the state machine.
      - If successful, retrieves the first message from the state machine for the topic and returns it.
      - If not successful within a certain timeout, returns an error (HTTP 408).
  - **Involved Methods and Logic**:
    - `get_message(topic)`: Main function to handle GET message requests.
    - Uses similar auxiliary functions as PUT operations..

  ### Status

  - **Process Flow**:
    - Returns the current role (`Follower`, `Leader`, `Candidate`) and term of the node.
  - **Involved Methods and Logic**:
    - `get_status()`: Main function to provide the status of the node.
  - **Variables and Execution Content**:
    - `raft_node.role`, `raft_node.current_term`: The current role and term of the node.

  ### Auxiliary Functions

  ###### `await_commit_confirmation(log_index)`

  - **Purpose**: Waits for a log entry at a specified index to be committed to the state machine.
  - **Logic**: Executes `wait_for_commit` within a ThreadPoolExecutor to check if the `commit_index` is greater than or equal to the `log_index` within a timeout.

  ###### `add_log_entry(term, topic, message="", flag=None)`

  - **Purpose**: Adds a new log entry for either a topic or message operation



## 4. Part1 Leader Election Implementation

- To detail the leader election logic in the provided code, focusing on the transitions between follower, candidate, and follower roles, including function design, variable comparisons, and special case handling:
  1. **Initial State (Follower)**: Each node begins as a follower with a randomized election timeout (`get_randomized_election_timeout()`).
  2. **Election Timeout**: If a follower doesn't hear from a leader within its timeout, it transitions to a candidate (`from_follower_to_candidate()`), increments its `current_term`, votes for itself, and resets its election timeout.
  3. **Requesting Votes**: As a candidate, it sends `request_vote` messages to all nodes (`send_request_vote()`), including its `current_term` and last log index/term for log integrity comparison.
  4. **Vote Collection**:
     - Nodes respond to vote requests based on several conditions: not having voted in the current term, the candidate's log being at least as up-to-date as the responder’s log.
     - If receiving a vote request with a higher term, a node updates its term and reverts to follower status.
  5. **Majority Votes**: If a candidate receives a majority, it transitions to a leader (`from_candidate_to_leader()`), begins sending heartbeats (`send_heartbeat()`), and manages log replication.
  6. **Split Vote**: If multiple candidates vie for votes, leading to no majority, nodes reset their election timeout. The process repeats until a single leader is elected.
  7. **Leader Heartbeats**: The leader periodically sends heartbeats to all followers to assert its role and manage the cluster's state.
  8. **Reverting to Follower**:
     - During elections, if a node discovers another node with a higher term or receives a valid heartbeat, it transitions back to follower status (`from_candidate_to_follower()`).
     - This ensures that only one leader exists per term and that the leader has the most up-to-date logs.
  9. **Variables and Functions**:
     - `current_term`, `vote_count`, and `logs` track the node's state.
     - `election_timeout_event` and related functions manage the timing for elections.
     - `state_lock` ensures thread-safe operations.
  10. **Handling Edge Cases**:
      - The implementation accounts for network partitions and node failures by allowing re-elections and using heartbeats to detect unreachable leaders.
      - Log integrity checks during the voting process prevent electing leaders with outdated logs.



## 5. Part3 Log Replication Implementation

- ### Overview

  Log replication in Raft ensures that all replicated state machines are kept in sync by having the leader node propagate its logs to all follower nodes. This mechanism guarantees that each node in the cluster will eventually store an identical copy of the log, allowing the system to maintain a consistent state.

  ### Key Components

  1. **Leader Election**: Before log replication can occur, a leader must be elected. The leader handles log entries and replicates them to the followers.
  2. **Log Entries**: Changes to the system state are encapsulated in log entries, which are sequentially indexed. Each entry contains a term number, the command to execute, and potentially other metadata.
  3. **Commit Index**: This is the index of the highest log entry known to be committed. It's crucial for ensuring consistency across the cluster.

  ### Variables and Structures

  - `current_term`: The current term of the node, incremented during elections.
  - `logs[]`: An array storing the log entries.
  - `commit_index`: The highest log index known to be committed.
  - `match_index[]`: An array indexed by node ID, storing the highest log index replicated on each server.
  - `heartbeat_received`: A dictionary tracking the heartbeats received from each node, used to ensure a majority of nodes are still in communication.

  ### Log Replication Process

  1. **Initiation by Leader**:
     - The leader appends new log entries to its log as it receives commands from clients.
     - It then sends an `AppendEntries` RPC to each of the follower nodes containing the new entries.
  2. **Appending Entries**:
     - Followers append the entries if the log entries are consistent with their logs (i.e., if the previous log index and term match their log).
     - Each follower responds to the leader, indicating success or failure.
  3. **Updating `match_index` and `commit_index`**:
     - On successful replication, the leader updates the `match_index` for each follower.
     - The leader examines its `match_index` array to find the highest log index replicated on a majority of nodes and updates its `commit_index` accordingly.
  4. **Committing Entries**:
     - Once the `commit_index` is advanced, the leader applies the log entries up to the `commit_index` to its state machine and informs followers to do the same in subsequent `AppendEntries` RPCs.

  ### Methods and Execution

  - `send_append_entries(server, data)`: Sends an `AppendEntries` RPC to a follower. It contains log entries to replicate, along with the leader's `commit_index`.
  - `send_heartbeat()`: This method sends heartbeat messages (which are essentially `AppendEntries` RPCs with no log entries) to each follower to maintain authority and replicate any outstanding logs.
  - `leader_try_to_commit()`: This method is invoked by the leader to update its `commit_index` based on the replication progress (`match_index` array). It tries to find the highest index replicated on a majority of nodes.
  - `apply_to_state_machine(index)`: Applies the command specified in the log entry at the given index to the state machine. This is done after the entry is committed.
  - `increment_heartbeat_received(from_id)`: Increments the count of heartbeats received from a specific node. This helps in determining if the leader is still in the majority.
  - `check_majority_heartbeats()`: Checks if heartbeats have been received from the majority of nodes. This is crucial for the leader to decide whether it should step down.

  ### Locks

  To ensure thread safety, especially when accessing and modifying shared data structures like `logs`, `commit_index`, `match_index`, and `heartbeat_received`, the code makes use of a `state_lock`. This lock is critical for maintaining consistency across the system state in a concurrent environment.

## 6. Conclusion

RRMQ successfully implements a distributed message queue using the Raft consensus algorithm, ensuring data consistency and fault tolerance. Through detailed design and robust implementation of leader election, log replication, and message queue management, RRMQ represents a resilient distributed system capable of handling dynamic cluster changes and node failures.

This report has dissected the essential components and functions integral to RRMQ's operation, demonstrating the comprehensive application of the Raft algorithm to manage distributed systems effectively.