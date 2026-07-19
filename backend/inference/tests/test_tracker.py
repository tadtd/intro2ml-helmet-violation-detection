from inference.src.tracker import IoUTracker


def test_fast_mover_keeps_one_id_via_velocity_prediction():
    """A box marching across the frame stays one track instead of fragmenting."""
    tracker = IoUTracker(iou_threshold=0.3, max_missed=10)
    ids = []
    for step in range(6):
        # Moves ~60px/frame; consecutive boxes overlap little, so plain IoU on the
        # last box would drop it. Prediction keeps it on the same id.
        dx = 60.0 * step
        tracks = tracker.update([(100.0 + dx, 100.0, 180.0 + dx, 260.0)])
        ids.append(tracks[0].track_id)
    # After the first move (when velocity becomes known) the id must stop changing.
    assert len(set(ids[2:])) == 1


def test_two_distinct_riders_do_not_merge():
    """Two boxes far apart stay two tracks; the gates never link them."""
    tracker = IoUTracker(iou_threshold=0.3, max_missed=10)
    tracker.update([(100.0, 100.0, 180.0, 260.0)])
    tracks = tracker.update([(100.0, 100.0, 180.0, 260.0), (700.0, 100.0, 780.0, 260.0)])
    assert len({t.track_id for t in tracks}) == 2


def test_lost_track_is_dropped_after_max_missed():
    tracker = IoUTracker(iou_threshold=0.3, max_missed=2)
    tracker.update([(100.0, 100.0, 180.0, 260.0)])
    for _ in range(4):
        tracker.update([])
    assert tracker.update([]) == []
