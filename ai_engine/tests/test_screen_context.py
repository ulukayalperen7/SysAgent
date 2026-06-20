import unittest

from core.screen_context import prepare_device_context_for_graph, redact_device_context_for_audit


class ScreenContextTests(unittest.TestCase):
    def test_summarizes_and_removes_raw_screen_image(self):
        context = {
            "execution_mode": "remote_device",
            "screen_context": {
                "active_process_name": "Code.exe",
                "screen_image_mime_type": "image/jpeg",
                "screen_image_base64": "abc",
            },
        }

        prepared = prepare_device_context_for_graph(
            context,
            summarizer=lambda mime, image: "VS Code is visible with an editor tab open.",
        )

        screen = prepared["screen_context"]
        self.assertEqual(screen["vision_status"], "summarized")
        self.assertIn("VS Code", screen["vision_summary"])
        self.assertNotIn("screen_image_base64", screen)
        self.assertNotIn("screen_image_mime_type", screen)

    def test_redacts_raw_screen_image_for_audit(self):
        redacted = redact_device_context_for_audit(
            {
                "screen_context": {
                    "screen_image_mime_type": "image/jpeg",
                    "screen_image_base64": "secret",
                    "vision_summary": "A terminal is open.",
                }
            }
        )

        screen = redacted["screen_context"]
        self.assertEqual(screen["vision_summary"], "A terminal is open.")
        self.assertNotIn("screen_image_base64", screen)
        self.assertNotIn("screen_image_mime_type", screen)


if __name__ == "__main__":
    unittest.main()
