# Raft REST Message Queue (RRMQ)


<img src="./Raft_Picture.svg" alt="./Raft_Picture" width="300"/>

## Overview

This project implements the Raft consensus algorithm, designed for managing a replicated log across cluster in a distributed system. The Raft algorithm ensures that each node in the cluster agrees upon the same series of log entries to apply to their state machines, achieving consensus even in the face of failures. This implementation covers the core functionalities of Raft, including message queue handling, leader election, log replication.

## Features

- **Message Queue Handling**: Implements a basic message queue that allows clients to create topics, publish messages to topics, and consume messages from topics. This feature demonstrates how Raft can be used to build distributed systems with consistent state
- **Leader Election**: Dynamically elects a leader among the nodes in the cluster to coordinate log replication. The leader election process is designed to ensure that there is at most one leader per term, addressing scenarios of network partitions and node failures.
- **Log Replication**: Once a leader is elected, it handles log entries from clients, replicating these entries across the cluster. This ensures that all nodes maintain an up-to-date and consistent log to apply to their state machines.
- **Fault Tolerance**: Designed to handle failures, allowing the system to continue operating as long as 2N+1 nodes are functional. 

## Project Structure

-  `src/`：
    - `log.py` - Handling of log entries. 
    - `node.py` - Definition of a single node behavior. 
    - `raft_node.py` - Implementation of Raft consensus protocol node.
- `config.json`: Configuration file specifying the addresses of the nodes in the cluster.
- `test/`: Directory containing tests that validate various aspects of the implementation, such as leader election, log replication, and message queue functionality. Detailed Guide could be found in testing_report.md.





