from inference.src.models.base import Detection
from inference.src.violation_logic import find_violations


def motorbike(box, confidence=0.9):
    return Detection(class_name="motorbike", box=box, confidence=confidence)


def bare_head(box, confidence=0.8):
    # Non-helmet boxes cover the whole rider, so they are taller than wide.
    return Detection(class_name="non-helmet", box=box, confidence=confidence)


def test_every_person_sized_non_helmet_is_a_violation():
    heads = [
        bare_head((120.0, 240.0, 180.0, 340.0)),
        bare_head((900.0, 240.0, 960.0, 340.0)),
        bare_head((120.0, 20.0, 180.0, 120.0), confidence=0.27),
    ]
    violations = find_violations(heads)
    assert len(violations) == len(heads)
    assert {v.non_helmet for v in violations} == set(heads)


def test_head_only_box_is_dropped():
    """A roughly square box covers just the head, not the rider, so it is ignored."""
    head_only = bare_head((130.0, 240.0, 175.0, 285.0))  # 45x45, aspect ~1.0
    assert find_violations([head_only]) == []


def test_low_confidence_person_box_still_counts():
    head = bare_head((120.0, 240.0, 180.0, 340.0), confidence=0.1)
    assert len(find_violations([head])) == 1


def test_motorbike_is_attached_when_the_head_is_its_rider():
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    head = bare_head((120.0, 240.0, 180.0, 340.0))

    violations = find_violations([bike, head])

    assert len(violations) == 1
    assert violations[0].motorbike is bike
    assert violations[0].non_helmet is head


def test_pedestrian_head_is_a_violation_without_a_motorbike():
    """Any non-helmet counts; a far-away head just has no motorbike attached."""
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    head = bare_head((900.0, 240.0, 960.0, 340.0))

    violations = find_violations([bike, head])

    assert len(violations) == 1
    assert violations[0].motorbike is None


def test_helmeted_rider_is_not_a_violation():
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    helmet = Detection(class_name="helmet", box=(120.0, 240.0, 180.0, 340.0), confidence=0.9)

    assert find_violations([bike, helmet]) == []
