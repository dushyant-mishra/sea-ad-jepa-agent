import importlib


def test_frozen_execution_driver_surface_exists_and_freezes_arm_order():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    assert m.ARMS == ("F0", "F1", "F2", "F3")
    assert m.DEFAULT_SEED == 7302
    assert m.DEFAULT_MEASUREMENT_SEED == 7302
    assert m.NO_POST_OUTCOME_RETUNING is True
    assert callable(m.run_frozen_tournament)
    assert callable(m.observe_frozen_arm)


def test_execution_driver_refuses_unready_gate():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    try:
        m.require_ready_gate({"status": "BLOCKED", "blockers": ["x"]})
    except PermissionError:
        pass
    else:
        raise AssertionError("blocked V78 gate must refuse scientific execution")
