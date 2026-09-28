"""The ledger must REFUSE, not warn. Every test below can actually fail."""
from __future__ import annotations
import importlib.util, sys
from pathlib import Path
import pytest

_P = Path(__file__).resolve().parents[1] / "src" / "sea_ad_jepa" / "v5" / \
    "regulatory_exposure_ledger_v1.py"
_s = importlib.util.spec_from_file_location("regledger", _P)
L = importlib.util.module_from_spec(_s); sys.modules["regledger"] = L
_s.loader.exec_module(L)


def test_stage75f_cannot_confirm_itself_in_morabito_rna():
    """THE case this file exists for: edges derived from Morabito RNA cannot
    be scored against Morabito RNA and called independent."""
    led = L.seed_known_objects()
    with pytest.raises(L.ConfirmationRefused) as e:
        led.assert_confirmation_eligible("STAGE75F_SPI1_V1", "MORABITO_RNA")
    assert "DEFINED using" in str(e.value)


def test_stage75f_IS_eligible_in_morabito_atac():
    """Positive control. The ATAC matrix was unused by Stage75F, so the refusal
    must NOT fire here - otherwise the ledger just blocks everything."""
    led = L.seed_known_objects()
    led.assert_confirmation_eligible("STAGE75F_SPI1_V1", "MORABITO_ATAC")


def test_full104_program_cannot_confirm_itself_in_full104():
    led = L.seed_known_objects()
    with pytest.raises(L.ConfirmationRefused):
        led.assert_confirmation_eligible("FULL104_PROGRAM_APOE_LIPID_V1",
                                         "FULL104_RNA")


def test_unknown_contribution_blocks_rather_than_permits():
    """Conservatism rule: silence is not independence."""
    led = L.seed_known_objects()
    with pytest.raises(L.ConfirmationRefused) as e:
        led.assert_confirmation_eligible("STAGE75F_SPI1_V1", "SEAAD_SPATIAL")
    assert "UNKNOWN" in str(e.value)


def test_unregistered_object_is_refused_not_defaulted():
    led = L.seed_known_objects()
    with pytest.raises(KeyError):
        led.assert_confirmation_eligible("SOMETHING_INVENTED", "MORABITO_ATAC")


def test_unknown_dataset_is_refused_so_new_sources_cannot_slip_in():
    led = L.seed_known_objects()
    with pytest.raises(ValueError):
        led.get("STAGE75F_SPI1_V1").contribution_to("A_NEW_COHORT")


def test_duplicate_registration_refused():
    led = L.seed_known_objects()
    obj = led.get("STAGE75F_SPI1_V1")
    with pytest.raises(ValueError):
        led.register(obj)


def test_mutation_flipping_contribution_to_NO_would_wrongly_permit():
    """Adversarial: prove the refusal is driven by the recorded provenance and
    not by the object's name. Flipping the record flips the verdict - which is
    why the record must be authored from evidence, not convenience."""
    led = L.seed_known_objects()
    o = led.get("STAGE75F_SPI1_V1")
    with pytest.raises(L.ConfirmationRefused):
        led.assert_confirmation_eligible(o.object_id, "MORABITO_RNA")
    o.contributions["MORABITO_RNA"] = L.Contribution.NO      # the mutation
    led.assert_confirmation_eligible(o.object_id, "MORABITO_RNA")  # now passes


def test_every_seeded_object_declares_every_dataset_or_is_blocked():
    led = L.seed_known_objects()
    for oid in list(led._objects):
        for ds in L.DATASETS:
            ok, why = led.get(oid).confirmation_eligible_in(ds)
            if led.get(oid).contribution_to(ds) is L.Contribution.UNKNOWN:
                assert not ok and "UNKNOWN" in why


def test_ledger_serialises_with_the_conservatism_rule_visible():
    import json
    d = json.loads(L.seed_known_objects().to_json())
    assert d["schema"] == "V5_REGULATORY_EXPOSURE_LEDGER_V1"
    assert "UNKNOWN blocks confirmation" in d["conservatism_rule"]
    assert len(d["objects"]) == 13          # 10 Stage75F TFs + 3 programs
