"""Unit tests for orchestrator phase detection and escalation."""

import importlib.util
from pathlib import Path

# Load orchestrator module without pulling full app settings when possible
_orch_path = Path(__file__).resolve().parent.parent / "agents" / "orchestrator.py"
_spec = importlib.util.spec_from_file_location("orchestrator_mod", _orch_path)
_orch = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_orch)

OrchestratorAgent = _orch.OrchestratorAgent


def test_should_escalate_availability():
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    assert agent._should_escalate("Is the cabana available on December 15?") == "availability"


def test_should_escalate_human_request():
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    assert agent._should_escalate("Can I speak to someone on your team?") == "human_request"


def test_should_escalate_complaint():
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    assert agent._should_escalate("I am not happy with the response") == "complaint"


def test_contact_skip_phrase():
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    assert agent._is_contact_skip("no thanks, skip the email")
