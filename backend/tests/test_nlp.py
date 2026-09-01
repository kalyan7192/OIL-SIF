import pytest
from app.services.nlp_preprocessor import preprocessor
from app.services.sif_classifier import sif_classifier
from app.services.rule_classifier import rule_classifier
from app.services.precursor_extractor import precursor_extractor

def test_abbreviation_expansion():
    raw_text = "Technician worked on pump without LOTO and no PTW while wearing standard PPE."
    expanded = preprocessor.expand_abbreviations(raw_text)
    assert "lockout tagout" in expanded.lower()
    assert "permit to work" in expanded.lower()

def test_sif_classifier_high_risk():
    text = "Technician opened electrical switchgear without applying LOTO while circuit was live with 415V."
    is_sif, conf, is_uncertain, reasons = sif_classifier.predict(text)
    assert is_sif is True
    assert conf > 0.50

def test_sif_classifier_low_risk():
    text = "Small water puddle noticed near workshop entrance walkway, minor slip hazard."
    is_sif, conf, is_uncertain, reasons = sif_classifier.predict(text)
    assert is_sif is False

def test_life_saving_rule_mapping():
    loto_text = "Flange unbolted without verifying energy isolation on pressurized crude line."
    rule_id, rule_name, _, _ = rule_classifier.classify(loto_text)
    assert rule_id == "ENERGY_ISOLATION"

    height_text = "Worker on scaffolding at 10 meters height without clipping safety harness."
    rule_id, rule_name, _, _ = rule_classifier.classify(height_text)
    assert rule_id == "WORKING_AT_HEIGHT"

    gas_text = "H2S sour gas release detected at wellhead, worker evacuated."
    rule_id, rule_name, _, _ = rule_classifier.classify(gas_text)
    assert rule_id == "TOXIC_GAS_H2S"

def test_precursor_extractor():
    text = "Mobile crane was lifting a 5-ton motor skid using a damaged synthetic sling with workers standing under the suspended load at Naharkatiya Rig D-14."
    precursor = precursor_extractor.extract(text)
    assert "Crane & Mechanical Lifting" in precursor.activity
    assert "Rigging" in precursor.barrier_failure
    assert len(precursor.evidence_snippets) > 0
