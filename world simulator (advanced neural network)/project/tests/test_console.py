import unittest
try:
    import pygame
    HAS_PYGAME = True
    from project.renderer.ui import Console
except ImportError:
    HAS_PYGAME = False
    Console = None  # type: ignore


@unittest.skipUnless(HAS_PYGAME, "pygame not installed")
class TestConsole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        # Initialize screen/font context so tests can run
        pygame.display.set_mode((100, 100), pygame.HIDDEN)

    def test_console_initialization(self):
        console = Console(x=0, y=0, width=500, height=350)
        self.assertFalse(console.active)
        self.assertEqual(console.input_text, "")
        self.assertGreater(len(console.history), 0)

    def test_console_toggle(self):
        console = Console(x=0, y=0, width=500, height=350)
        console.toggle()
        self.assertTrue(console.active)
        console.toggle()
        self.assertFalse(console.active)

    def test_console_log(self):
        console = Console(x=0, y=0, width=500, height=350)
        original_length = len(console.history)
        console.log("Test log entry")
        self.assertEqual(len(console.history), original_length + 1)
        self.assertEqual(console.history[-1], "Test log entry")

    def test_console_event_handling_inactive(self):
        console = Console(x=0, y=0, width=500, height=350)
        # Event should toggle activation on Backquote (~)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKQUOTE, unicode='`')
        res = console.handle_event(event)
        self.assertTrue(res is None)
        self.assertTrue(console.active)

    def test_console_event_handling_typing(self):
        console = Console(x=0, y=0, width=500, height=350)
        console.active = True
        
        # Test character key down
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f, unicode='f')
        console.handle_event(event)
        self.assertEqual(console.input_text, "f")

        # Test enter key executes command
        event_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        cmd = console.handle_event(event_enter)
        self.assertEqual(cmd, "f")
        self.assertEqual(console.input_text, "")

if __name__ == "__main__":
    unittest.main()
