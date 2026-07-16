"""Unit tests for cone_mapper.map_data (no ROS required).

Run:  pytest perception_ws/src/cone_mapper/test/test_map_data.py -v
"""
import pytest

from cone_mapper.constants import ConeColor
from cone_mapper.map_data import LocalConeBuffer, PersistentGlobalMap


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


# ── LocalConeBuffer ──────────────────────────────────────────────────────

def test_new_detection_creates_cone():
    clock = FakeClock()
    buf = LocalConeBuffer(now_fn=clock)
    buf.add_cone_detection(5.0, 2.0, 0.3, ConeColor.BLUE)
    cones = buf.get_all_cones()
    assert len(cones) == 1
    assert cones[0]['color'] == ConeColor.BLUE


def test_detection_confidence_scales_initial_confidence():
    clock = FakeClock()
    buf = LocalConeBuffer(now_fn=clock)
    buf.add_cone_detection(2.0, 0.0, 0.3, ConeColor.BLUE, confidence=1.0)
    buf.add_cone_detection(50.0, 50.0, 0.3, ConeColor.YELLOW, confidence=0.0)
    blue = next(c for c in buf.get_all_cones() if c['color'] == ConeColor.BLUE)
    yellow = next(c for c in buf.get_all_cones() if c['color'] == ConeColor.YELLOW)
    assert blue['confidence'] > yellow['confidence']


def test_nearby_same_colour_detection_merges():
    clock = FakeClock()
    buf = LocalConeBuffer(now_fn=clock)
    buf.add_cone_detection(5.0, 2.0, 0.3, ConeColor.BLUE)
    buf.add_cone_detection(5.4, 2.1, 0.3, ConeColor.BLUE)
    cones = buf.get_all_cones()
    assert len(cones) == 1
    assert cones[0]['detections'] == 2
    # position moved toward the second observation
    assert 5.0 < cones[0]['x'] < 5.4


def test_different_colour_never_merges():
    clock = FakeClock()
    buf = LocalConeBuffer(now_fn=clock)
    buf.add_cone_detection(5.0, 2.0, 0.3, ConeColor.BLUE)
    buf.add_cone_detection(5.1, 2.0, 0.3, ConeColor.YELLOW)
    assert len(buf.get_all_cones()) == 2


def test_continuously_seen_cone_survives_past_max_age():
    """Aging must use last_seen: a cone still in view is never evicted."""
    clock = FakeClock()
    buf = LocalConeBuffer(max_age=6.0, now_fn=clock)
    for _ in range(20):          # re-seen every second for 20 s > max_age
        buf.add_cone_detection(5.0, 2.0, 0.3, ConeColor.BLUE)
        clock.advance(1.0)
        buf.update_frame()
    assert len(buf.get_all_cones()) == 1
    assert buf.get_all_cones()[0]['detections'] == 20


def test_unseen_cone_expires_after_max_age():
    clock = FakeClock()
    buf = LocalConeBuffer(max_age=6.0, now_fn=clock)
    buf.add_cone_detection(5.0, 2.0, 0.3, ConeColor.BLUE)
    clock.advance(7.0)
    buf.update_frame()
    assert buf.get_all_cones() == []


# ── PersistentGlobalMap ──────────────────────────────────────────────────

def _cone(x, y, color=ConeColor.BLUE, confidence=0.9, detections=5):
    return {'x': x, 'y': y, 'z': 0.3, 'color': color,
            'confidence': confidence, 'detections': detections}


def test_promotion_requires_confidence_and_detections():
    gm = PersistentGlobalMap(confidence_threshold=0.7, min_detections=3,
                             now_fn=FakeClock())
    assert not gm.try_add_cone(_cone(1, 1, confidence=0.5))          # low conf
    assert not gm.try_add_cone(_cone(1, 1, detections=2))            # few dets
    assert gm.try_add_cone(_cone(1, 1))                              # passes


def test_redetection_refines_position_instead_of_duplicating():
    gm = PersistentGlobalMap(now_fn=FakeClock())
    assert gm.try_add_cone(_cone(10.0, 5.0))
    # re-detected 1 m away (e.g. after loop closure improved the pose):
    assert not gm.try_add_cone(_cone(11.0, 5.0))     # merged, not added
    cones = gm.get_global_map()
    assert len(cones) == 1
    assert 10.0 < cones[0]['x'] < 11.0               # position refined


def test_orange_needs_stricter_promotion():
    gm = PersistentGlobalMap(now_fn=FakeClock())
    weak_orange = _cone(1, 1, color=ConeColor.ORANGE,
                        confidence=0.8, detections=3)
    assert not gm.try_add_cone(weak_orange)          # blue bar not enough
    strong_orange = _cone(1, 1, color=ConeColor.ORANGE,
                          confidence=0.9, detections=6)
    assert gm.try_add_cone(strong_orange)


def test_far_apart_same_colour_cones_both_kept():
    gm = PersistentGlobalMap(now_fn=FakeClock())
    assert gm.try_add_cone(_cone(0.0, 0.0))
    assert gm.try_add_cone(_cone(5.0, 0.0))
    assert len(gm.get_global_map()) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
