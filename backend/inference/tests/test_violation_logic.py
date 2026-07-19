from inference.src.models.base import Detection
from inference.src.violation_logic import find_violations


def motorbike(box, confidence=0.9):
    return Detection(class_name="motorbike", box=box, confidence=confidence)


def bare_head(box, confidence=0.8):
    # Non-helmet boxes cover the whole rider, so they are taller than wide.
    return Detection(class_name="non-helmet", box=box, confidence=confidence)


def test_all_riders_on_one_bike_group_into_one_violation():
    bike = motorbike((100.0, 300.0, 260.0, 420.0))  # wide bike carrying several
    left = bare_head((110.0, 210.0, 150.0, 320.0))
    mid = bare_head((170.0, 200.0, 210.0, 320.0))
    right = bare_head((220.0, 210.0, 260.0, 320.0))

    violations = find_violations([bike, left, mid, right])

    assert len(violations) == 1
    assert violations[0].motorbike is bike
    assert set(violations[0].non_helmets) == {left, mid, right}


def test_crop_box_covers_the_whole_bike_and_every_rider():
    bike = motorbike((100.0, 300.0, 260.0, 420.0))
    left = bare_head((110.0, 210.0, 150.0, 320.0))
    right = bare_head((220.0, 210.0, 260.0, 320.0))

    box = find_violations([bike, left, right])[0].crop_box()

    # Union spans the leftmost/topmost to the rightmost/bottommost corner.
    assert box == (100.0, 210.0, 260.0, 420.0)


def test_head_only_box_still_counts_with_an_expanded_crop():
    """A head-only detection is still a violation; its crop is expanded downward."""
    head_only = bare_head((130.0, 240.0, 175.0, 285.0))  # 45x45, aspect ~1.0
    violations = find_violations([head_only])
    assert len(violations) == 1
    # Crop extends below the head box to include the body.
    assert violations[0].crop_box()[3] > 285.0


def test_pedestrian_head_is_its_own_violation_without_a_motorbike():
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    far = bare_head((900.0, 240.0, 960.0, 340.0))

    violations = find_violations([bike, far])

    assert len(violations) == 1
    assert violations[0].motorbike is None
    assert violations[0].non_helmets == (far,)


def test_helmeted_rider_is_not_a_violation():
    bike = motorbike((100.0, 300.0, 200.0, 400.0))
    helmet = Detection(class_name="helmet", box=(120.0, 240.0, 180.0, 340.0), confidence=0.9)

    assert find_violations([bike, helmet]) == []


def test_head_inside_body_box_is_merged_into_one_violation():
    """A head-only box contained by a whole-body box is one rider, not two."""
    body = bare_head((216.0, 77.0, 288.0, 345.0), confidence=0.49)
    head = bare_head((236.0, 79.0, 285.0, 134.0), confidence=0.44)  # inside body

    violations = find_violations([body, head])

    assert len(violations) == 1
    # The higher-confidence (body) box survives the merge.
    assert violations[0].non_helmets == (body,)


def test_track_box_is_independent_of_the_motorbike():
    """The dedup anchor is the same whether or not a bike is grouped in."""
    head = bare_head((130.0, 80.0, 175.0, 130.0))
    bike = motorbike((90.0, 120.0, 210.0, 240.0))

    grouped = find_violations([bike, head])[0]
    loose = find_violations([head])[0]

    assert grouped.motorbike is bike and loose.motorbike is None
    # Same rider, same tracking identity, regardless of the flickering bike box.
    assert grouped.track_box() == loose.track_box()


def test_group_confidence_is_the_max_rider_confidence():
    bike = motorbike((100.0, 300.0, 260.0, 420.0))
    low = bare_head((110.0, 210.0, 150.0, 320.0), confidence=0.3)
    high = bare_head((220.0, 210.0, 260.0, 320.0), confidence=0.85)

    assert find_violations([bike, low, high])[0].confidence == 0.85
