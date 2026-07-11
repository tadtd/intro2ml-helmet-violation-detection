from inference.src.models.base import Detection
from inference.src.violation_logic import find_violations


def motorbike(box, confidence=0.9):
    return Detection(class_name="motorbike", box=box, confidence=confidence)


def bare_head(box, confidence=0.8):
    return Detection(class_name="non-helmet", box=box, confidence=confidence)


def test_head_above_motorbike_is_a_violation():
    """The rider's head sits above the bike, so the boxes never overlap."""
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    head = bare_head((130.0, 240.0, 170.0, 290.0))

    violations = find_violations([bike, head])

    assert len(violations) == 1
    assert violations[0].motorbike is bike
    assert violations[0].non_helmet is head


def test_head_far_from_motorbike_is_not_a_violation():
    """A pedestrian across the street must not be attributed to a rider."""
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    head = bare_head((900.0, 240.0, 940.0, 290.0))

    assert find_violations([bike, head]) == []


def test_head_far_above_motorbike_is_not_a_violation():
    """A head high above the bike belongs to somebody else, e.g. on a balcony."""
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    head = bare_head((130.0, 20.0, 170.0, 60.0))

    assert find_violations([bike, head]) == []


def test_low_confidence_head_is_ignored():
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    head = bare_head((130.0, 240.0, 170.0, 290.0), confidence=0.27)

    assert find_violations([bike, head]) == []


def test_head_between_two_motorbikes_is_reported_once_for_the_nearest():
    near = motorbike((100.0, 300.0, 200.0, 400.0))
    far = motorbike((170.0, 300.0, 270.0, 400.0))
    head = bare_head((140.0, 240.0, 180.0, 290.0))

    violations = find_violations([near, far, head])

    assert len(violations) == 1
    assert violations[0].motorbike is near


def test_pedestrian_walking_beside_a_motorbike_is_not_a_violation():
    """The bike is 100px wide; a person one bike-width to the side is a bystander."""
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    pedestrian = bare_head((230.0, 250.0, 300.0, 420.0))

    assert find_violations([bike, pedestrian]) == []


def test_helmeted_rider_is_not_a_violation():
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    helmet = Detection(class_name="helmet", box=(130.0, 240.0, 170.0, 290.0), confidence=0.9)

    assert find_violations([bike, helmet]) == []
