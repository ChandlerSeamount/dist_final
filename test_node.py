import unittest
from unittest.mock import patch, MagicMock
from lib import Node

class TestNode(unittest.TestCase):

    def setUp(self):
        """Simplified setup with mocked sockets and listen process."""
        self.network_size = 5
        self.name = "localhost"
        self.basis_port = 5000
        self.num_nodes = 3
        self.node_id = 0

        with patch("lib.socket") as MockSocket, patch("lib.multiprocessing.Process") as MockProcess:
            self.mock_socket = MockSocket.return_value
            self.mock_process = MockProcess.return_value
            self.mock_process.start = MagicMock()  #Start method
            self.node = Node(
                networkSize=self.network_size,
                location=0,
                name=self.name,
                basis=self.basis_port + self.node_id * 10,
                numNodes=self.num_nodes,
                id=self.node_id
            )

    def tearDown(self):
        if self.node.isActive():
            self.node.exit()

    def test_initialization(self):
        """Test that Node initializes correctly."""
        self.assertEqual(self.node.myLocation, 0)
        self.assertEqual(len(self.node.T), self.num_nodes)
        self.assertEqual(list(self.node.T), [0] * self.num_nodes)  #Convert to list
        self.assertTrue(self.node.active)

    def test_broadcast(self):
        """Test that broadcasting does not throw errors."""
        try:
            self.node.broadcast("Test message")
        except Exception as e:
            self.fail(f"Broadcast raised an exception: {e}")

    def test_internal_event(self):
        """Test that internal events update time vector."""
        initial_T = list(self.node.T[:])  #Convert to list
        self.node.internalEvent()
        self.assertNotEqual(list(self.node.T), initial_T)  #Convert to list
        self.assertEqual(self.node.T[self.node.myID], initial_T[self.node.myID] + 1)

    def test_exit(self):
        """Test node exit functionality."""
        self.node.exit()
        self.assertFalse(self.node.isActive())

    def test_snapshot_initialization(self):
        """Test that a snapshot is initialized correctly."""
        self.node.getSnapshot()
        snapshot = list(self.node.snapshot)  #Convert to list
        self.assertIsNotNone(snapshot)
        self.assertIsInstance(snapshot, list)

    def test_snapshot_state_capture(self):
        """Test that a snapshot captures the current state."""
        self.node.T[self.node.myID] = 10  #Simulate state changes
        self.node.getSnapshot()
        snapshot = list(self.node.snapshot)  #Convert to list
        self.assertGreater(len(snapshot), 0, "Snapshot is empty")  #Snapshot is not empty
        self.assertEqual(snapshot[self.node.myID], 10)  #Check state is captured

    def test_snapshot_consistency(self):
        """Test that a snapshot is consistent across events."""
        self.node.T[self.node.myID] = 5  #Simulate initial state
        self.node.getSnapshot()
        snapshot_before = list(self.node.snapshot)  #Convert to list

        self.node.T[self.node.myID] = 10  #State change
        self.node.getSnapshot()
        snapshot_after = list(self.node.snapshot)

        self.assertGreater(len(snapshot_after), 0, "Snapshot is empty after state change")  #Snapshot is not empty
        self.assertNotEqual(snapshot_before, snapshot_after)  #Snapshots reflect changes
        self.assertEqual(snapshot_after[self.node.myID], 10)  #Verify updated state

class TestNodeNetwork(unittest.TestCase):

    def setUp(self):
        """Simplified setup for a small network of nodes."""
        self.network_size = 5
        self.name = "localhost"
        self.basis_port = 5000
        self.num_nodes = 2
        self.nodes = []

        with patch("lib.socket") as MockSocket, patch("lib.multiprocessing.Process") as MockProcess:
            self.mock_socket = MockSocket.return_value
            self.mock_process = MockProcess.return_value
            self.mock_process.start = MagicMock()  #Start method
            for i in range(self.num_nodes):
                node = Node(
                    networkSize=self.network_size,
                    location=i,
                    name=self.name,
                    basis=self.basis_port + i * 10,
                    numNodes=self.num_nodes,
                    id=i
                )
                self.nodes.append(node)

    def tearDown(self):
        for node in self.nodes:
            if node.isActive():
                node.exit()

    def test_network_initialization(self):
        """Test that all nodes initialize without errors."""
        for node in self.nodes:
            self.assertTrue(node.isActive())

if __name__ == "__main__":
    unittest.main()
