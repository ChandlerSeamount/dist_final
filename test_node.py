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
            self.mock_process.start = MagicMock()  #start method
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
            self.mock_process.start = MagicMock()  #start method
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
