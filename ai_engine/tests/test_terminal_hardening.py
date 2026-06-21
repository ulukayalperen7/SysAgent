import unittest

from agents.langgraph.nodes.chat import direct_chat_node
from agents.langgraph.nodes.intent import _detect_intent_deterministic
from agents.langgraph.nodes.planner import _deterministic_decompose, decompose_task_node
from agents.langgraph.nodes.synthesis import final_synthesis_node
from core.response_parse import parse_explanation_and_script
from core.script_policy import propose_deterministic_script, validate_command_risk


class TerminalHardeningTests(unittest.TestCase):
    def test_decompose_mixed_queue_steps(self):
        tasks = _deterministic_decompose(
            "open notepad sonra next song sonra create test.txt on desktop"
        )

        self.assertEqual(tasks, ["open notepad", "next song", "create test.txt on desktop"])

    def test_decompose_accepts_common_turkish_typo(self):
        tasks = _deterministic_decompose("notepad a\u00e7 sorna sonraki \u015fark\u0131")

        self.assertEqual(tasks, ["notepad a\u00e7", "sonraki \u015fark\u0131"])

    def test_planner_keeps_single_terminal_task_deterministic(self):
        result = decompose_task_node({"user_input": "deneme2.py ad\u0131nda dosya olu\u015ftur", "task_queue": []})

        self.assertEqual(result["task_queue"], ["deneme2.py ad\u0131nda dosya olu\u015ftur"])

    def test_planner_keeps_english_media_command_deterministic(self):
        result = decompose_task_node({"user_input": "previous song pls ?", "task_queue": []})

        self.assertEqual(result["task_queue"], ["previous song pls ?"])

    def test_planner_keeps_gui_click_task_deterministic(self):
        result = decompose_task_node({"user_input": "Submit butonuna t\u0131kla", "task_queue": []})

        self.assertEqual(result["task_queue"], ["Submit butonuna t\u0131kla"])

    def test_planner_resumes_queue_with_turkish_continue(self):
        result = decompose_task_node({"user_input": "devam", "task_queue": ["open notepad"]})

        self.assertEqual(result["task_queue"], ["open notepad"])

    def test_planner_keeps_verification_repair_prompt_atomic(self):
        prompt = "VERIFICATION_FAILED: The previous approved desktop action did not verify cleanly.\nPrevious script:\nclick 120,240"

        result = decompose_task_node({"user_input": prompt, "task_queue": ["create note.txt"]})

        self.assertEqual(result["task_queue"], [prompt])

    def test_chat_shortcut_does_not_need_llm(self):
        result = direct_chat_node(
            {
                "user_input": "hello",
                "messages": [],
                "explanation": "",
                "script": "NONE",
            }
        )

        self.assertEqual(result["script"], "NONE")
        self.assertIn("SysAgent is ready", result["explanation"])

    def test_final_synthesis_reuses_ready_terminal_answer(self):
        result = final_synthesis_node(
            {
                "explanation": "Summary:\nAlready formatted.",
                "script": "NONE",
                "errors": [],
                "messages": [],
            }
        )

        self.assertEqual(result["explanation"], "Summary:\nAlready formatted.")

    def test_deterministic_intent_detects_app_and_file_write(self):
        self.assertEqual(_detect_intent_deterministic("open notepad"), "APP_CONTROL")
        self.assertEqual(_detect_intent_deterministic("delete test.txt from desktop"), "FILE_SYSTEM_WRITE")

    def test_deterministic_intent_routes_verification_repair_to_worker(self):
        self.assertEqual(
            _detect_intent_deterministic("VERIFICATION_UNCERTAIN: button may not have been clicked"),
            "UNKNOWN",
        )

    def test_windows_open_app_proposal_is_review_only(self):
        proposal = propose_deterministic_script("open notepad", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn("Start-Process", proposal.script)
        self.assertIn("Test-AppRunning", proposal.script)
        self.assertEqual(proposal.risk_level, "Medium")

    def test_windows_app_open_uses_generic_resolver_not_hardcoded_aliases(self):
        proposal = propose_deterministic_script("open teams", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn("Get-StartApps", proposal.script)
        self.assertIn("App Paths", proposal.script)
        self.assertIn("StartMenu", proposal.script)
        self.assertIn("HKEY_CLASSES_ROOT", proposal.script)
        self.assertNotIn("ms-teams.exe", proposal.script)
        self.assertNotIn('"teams:"', proposal.script)
        self.assertIn("Could not start application or verify process", proposal.script)

    def test_windows_media_next_proposal_uses_virtual_key(self):
        proposal = propose_deterministic_script("next song", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn("0xB0", proposal.script)

    def test_windows_media_previous_proposal_uses_virtual_key(self):
        proposal = propose_deterministic_script("previous song pls ?", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn("0xB1", proposal.script)

    def test_file_delete_is_high_risk(self):
        proposal = propose_deterministic_script("delete test.txt from desktop", "FILE_SYSTEM_WRITE", "Windows")

        self.assertIsNotNone(proposal)
        risk = validate_command_risk(proposal.script, "FILE_SYSTEM_WRITE", "Windows")
        self.assertEqual(risk.risk_level, "High")

    def test_turkish_create_extracts_clean_filename(self):
        proposal = propose_deterministic_script(
            "masaüstüne deneme.txt oluştursana",
            "FILE_SYSTEM_WRITE",
            "Windows",
        )

        self.assertIsNotNone(proposal)
        self.assertIn('Join-Path $targetDir "deneme.txt"', proposal.script)
        self.assertNotIn("Create deneme.txt", proposal.script)

    def test_turkish_followup_write_uses_recent_file_from_history(self):
        proposal = propose_deterministic_script(
            "tamam içine deneme alperen ulukaya yaz",
            "FILE_SYSTEM_WRITE",
            "Windows",
            context_messages=[
                {"role": "user", "content": "masaüstüne deneme.txt oluştursana"},
                {"role": "ai", "content": "You want to create 'deneme.txt' in the selected local folder."},
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn('Join-Path $targetDir "deneme.txt"', proposal.script)
        self.assertIn('deneme alperen ulukaya', proposal.script)

    def test_real_turkish_create_named_file_does_not_include_prompt_words(self):
        proposal = propose_deterministic_script(
            "deneme2.py ad\u0131nda bi dosya olu\u015ftur masa\u00fcst\u00fcnde",
            "FILE_SYSTEM_WRITE",
            "Windows",
        )

        self.assertIsNotNone(proposal)
        self.assertIn('Join-Path $targetDir "deneme2.py"', proposal.script)
        self.assertNotIn("Create a file named", proposal.script)

    def test_real_turkish_followup_fastapi_write_uses_recent_python_file(self):
        proposal = propose_deterministic_script(
            "i\u00e7ine basit bi fast api kodu yaz onun",
            "FILE_SYSTEM_WRITE",
            "Windows",
            context_messages=[
                {"role": "user", "content": "deneme2.py ad\u0131nda bi dosya olu\u015ftur masa\u00fcst\u00fcnde"},
                {"role": "ai", "content": "You want to create 'deneme2.py' in the selected local folder."},
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn('Join-Path $targetDir "deneme2.py"', proposal.script)
        self.assertIn("from fastapi import FastAPI", proposal.script)
        self.assertNotIn("onun", proposal.script)

    def test_real_turkish_app_open_trailing_verb(self):
        proposal = propose_deterministic_script("notepad a\u00e7", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn('$app = "notepad"', proposal.script)

    def test_real_turkish_app_open_strips_object_suffix(self):
        proposal = propose_deterministic_script("notepad'\u0131 a\u00e7", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn('$app = "notepad"', proposal.script)
        self.assertNotIn("notepad'\u0131", proposal.script)

    def test_contextual_app_open_resolves_it_from_current_prompt(self):
        proposal = propose_deterministic_script(
            "I closed notepad can u open it again",
            "APP_CONTROL",
            "Windows",
        )

        self.assertIsNotNone(proposal)
        self.assertIn('$app = "notepad"', proposal.script)
        self.assertNotIn('$app = "it again"', proposal.script)

    def test_contextual_app_open_resolves_it_from_history(self):
        proposal = propose_deterministic_script(
            "open it again",
            "APP_CONTROL",
            "Windows",
            context_messages=[
                {"role": "ai", "content": "You want to open the local application 'notepad'."},
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn('$app = "notepad"', proposal.script)

    def test_contextual_app_close_resolves_this_app_from_screen_context(self):
        proposal = propose_deterministic_script(
            "close this app",
            "APP_CONTROL",
            "Windows",
            context_messages=[
                {"role": "system", "content": "Current desktop active application/process named 'Code.exe'."},
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn('Stop-Process -Name "Code"', proposal.script)
        self.assertNotIn('"this app"', proposal.script)

    def test_gui_type_targets_active_process_from_screen_context(self):
        self.assertEqual(_detect_intent_deterministic('write into this "hello world"'), "APP_CONTROL")
        proposal = propose_deterministic_script(
            'write into this "hello world"',
            "APP_CONTROL",
            "Windows",
            context_messages=[
                {"role": "system", "content": "Current desktop active application/process named 'Code.exe'."},
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn('$targetProcess = "Code"', proposal.script)
        self.assertIn("System.Windows.Forms", proposal.script)
        self.assertIn('SendWait("hello world")', proposal.script)

    def test_gui_click_can_use_explicit_coordinates(self):
        self.assertEqual(_detect_intent_deterministic("click 120,240"), "APP_CONTROL")
        proposal = propose_deterministic_script(
            "click 120,240",
            "APP_CONTROL",
            "Windows",
            context_messages=[
                {"role": "system", "content": "Current desktop active application/process named 'Code.exe'."},
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn("$x = 120", proposal.script)
        self.assertIn("$y = 240", proposal.script)
        self.assertIn("mouse_event", proposal.script)

    def test_gui_click_can_target_label_from_vision_summary(self):
        proposal = propose_deterministic_script(
            "click Submit",
            "APP_CONTROL",
            "Windows",
            context_messages=[
                {
                    "role": "system",
                    "content": "Current desktop screenshot summary: Target: Submit @ x=640 y=512.",
                },
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn("$x = 640", proposal.script)
        self.assertIn("$y = 512", proposal.script)
        self.assertIn("mouse_event", proposal.script)

    def test_gui_click_can_target_turkish_button_label_from_vision_summary(self):
        proposal = propose_deterministic_script(
            "Submit butonuna t\u0131kla",
            "APP_CONTROL",
            "Windows",
            context_messages=[
                {
                    "role": "system",
                    "content": "Current desktop screenshot summary: Target: Submit @ x=640 y=512.",
                },
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn("$x = 640", proposal.script)
        self.assertIn("$y = 512", proposal.script)
        self.assertIn("mouse_event", proposal.script)

    def test_linux_gui_click_uses_xdotool_with_vision_target(self):
        proposal = propose_deterministic_script(
            "click Submit",
            "APP_CONTROL",
            "Linux",
            context_messages=[
                {
                    "role": "system",
                    "content": "Current desktop screenshot summary: Target: Submit @ x=640 y=512.",
                },
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn("xdotool", proposal.script)
        self.assertIn("mousemove 640 512 click 1", proposal.script)

    def test_macos_gui_click_uses_cliclick_with_vision_target(self):
        proposal = propose_deterministic_script(
            "click Submit",
            "APP_CONTROL",
            "macOS",
            context_messages=[
                {
                    "role": "system",
                    "content": "Current desktop screenshot summary: Target: Submit @ x=640 y=512.",
                },
            ],
        )

        self.assertIsNotNone(proposal)
        self.assertIn("cliclick", proposal.script)
        self.assertIn("c:640,512", proposal.script)

    def test_real_turkish_intent_detects_trailing_app_open(self):
        self.assertEqual(_detect_intent_deterministic("notepad'\u0131 a\u00e7"), "APP_CONTROL")

    def test_real_turkish_next_song_uses_media_key(self):
        proposal = propose_deterministic_script("sonraki \u015fark\u0131ya ge\u00e7", "APP_CONTROL", "Windows")

        self.assertIsNotNone(proposal)
        self.assertIn("0xB0", proposal.script)

    def test_parser_strips_fences_and_extra_sections(self):
        explanation, script = parse_explanation_and_script(
            "Explanation: do thing\nScript: ```powershell\nGet-Process\n```\nRollback: none"
        )

        self.assertEqual(explanation, "do thing")
        self.assertEqual(script, "Get-Process")


if __name__ == "__main__":
    unittest.main()
