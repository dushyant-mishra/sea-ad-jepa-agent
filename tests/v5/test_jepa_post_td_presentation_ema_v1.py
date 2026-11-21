from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_harness_contract_v1.py"
CSPEC = importlib.util.spec_from_file_location("jepa_post_td_harness_contract_v1", CONTRACT_PATH)
assert CSPEC and CSPEC.loader
C = importlib.util.module_from_spec(CSPEC)
sys.modules[CSPEC.name] = C
CSPEC.loader.exec_module(C)

MODULE_PATH = ROOT / "scripts" / "v5" / "jepa_post_td_presentation_ema_v1.py"
SPEC = importlib.util.spec_from_file_location("jepa_post_td_presentation_ema_v1", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


class FakeController:
    def __init__(self):
        self.global_update_step = 0
        self.ema_update_count = 0
        self.momenta = []

    def after_successful_optimizer_step(self, *, momentum):
        self.momenta.append(momentum)
        self.global_update_step += 1
        self.ema_update_count += 1


class PresentationEMATests(unittest.TestCase):
    def test_advance_requires_proved_optimizer_step(self):
        state = M.PresentationEMAState(half_life_presentations=20_000)
        with self.assertRaisesRegex(M.PresentationEMAError, "proved optimizer"):
            M.advance_after_proved_optimizer_step(
                controller=FakeController(),
                state=state,
                successful_presentations=128,
                proved_optimizer_advanced=False,
            )

    def test_advance_uses_presentation_momentum_and_updates_state(self):
        controller = FakeController()
        state = M.PresentationEMAState(half_life_presentations=20_000)
        new_state, report = M.advance_after_proved_optimizer_step(
            controller=controller,
            state=state,
            successful_presentations=128,
            proved_optimizer_advanced=True,
        )
        expected = C.ema_momentum_for_presentations(128, 20_000)
        self.assertAlmostEqual(controller.momenta[0], expected, places=15)
        self.assertEqual(new_state.successful_presentations, 128)
        self.assertEqual(new_state.ema_updates, 1)
        self.assertEqual(report["successful_presentations_this_update"], 128)
        self.assertAlmostEqual(report["momentum"], expected, places=15)

    def test_restart_state_must_match_controller_counts(self):
        controller = FakeController()
        controller.global_update_step = 3
        controller.ema_update_count = 3
        state = M.PresentationEMAState(
            half_life_presentations=20_000,
            successful_presentations=384,
            ema_updates=2,
        )
        with self.assertRaisesRegex(M.PresentationEMAError, "counter mismatch"):
            M.validate_restart_binding(controller=controller, state=state)

    def test_checkpoint_overlay_binds_portfolio_architecture_and_base_checkpoint(self):
        state = M.PresentationEMAState(
            half_life_presentations=20_000,
            successful_presentations=12_800,
            ema_updates=100,
        )
        overlay = M.build_checkpoint_overlay(
            base_checkpoint_sha256="a" * 64,
            portfolio_sha256="b" * 64,
            architecture_sha256="c" * 64,
            ema_state=state,
        )
        self.assertEqual(overlay["schema"], "JEPA_POST_TD_CHECKPOINT_OVERLAY_V1")
        self.assertEqual(overlay["ema"]["successful_presentations"], 12_800)
        self.assertFalse(overlay["authority"]["training_authorized"])
        self.assertFalse(overlay["authority"]["continuation_authorized"])

    def test_checkpoint_overlay_rejects_invalid_hashes(self):
        state = M.PresentationEMAState(half_life_presentations=1_000)
        with self.assertRaisesRegex(M.PresentationEMAError, "SHA-256"):
            M.build_checkpoint_overlay(
                base_checkpoint_sha256="bad",
                portfolio_sha256="b" * 64,
                architecture_sha256="c" * 64,
                ema_state=state,
            )


if __name__ == "__main__":
    unittest.main()
