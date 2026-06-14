import unittest

from agent.data import Message


class TestMessage(unittest.TestCase):
    def test_to_msg(self):
        msg = Message(role="user", content="hello")
        self.assertEqual(msg.to_msg(), {"role": "user", "content": "hello"})

    def test_to_msg_system(self):
        msg = Message(role="system", content="you are a helper")
        self.assertEqual(
            msg.to_msg(), {"role": "system", "content": "you are a helper"}
        )

    def test_to_msg_assistant(self):
        msg = Message(role="assistant", content="hi there")
        self.assertEqual(msg.to_msg(), {"role": "assistant", "content": "hi there"})

    def test_to_msg_empty_content(self):
        msg = Message(role="user", content="")
        self.assertEqual(msg.to_msg(), {"role": "user", "content": ""})

    def test_role_field(self):
        msg = Message(role="user", content="test")
        self.assertEqual(msg.role, "user")

    def test_content_field(self):
        msg = Message(role="user", content="test")
        self.assertEqual(msg.content, "test")


if __name__ == "__main__":
    unittest.main()
