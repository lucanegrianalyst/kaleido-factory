from __future__ import annotations

from kaleido_factory.geometry.echo_lines import EchoBranch, generate_echo_lines


def test_echo_lines_generates_scaled_branches() -> None:
    pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    branches = generate_echo_lines(
        pts,
        echo_count=3,
        scale_step=0.8,
        origin=(0.0, 0.0),
        include_original=True,
    )
    assert len(branches) >= 2
    assert all(isinstance(b, EchoBranch) for b in branches)
    assert len(branches[0].points) == 3


def test_echo_lines_max_total_points_cap() -> None:
    pts = [(float(i), float(i % 7)) for i in range(50)]
    branches = generate_echo_lines(pts, echo_count=10, scale_step=0.9, max_total_points=120)
    total_pts = sum(len(b.points) for b in branches)
    assert total_pts <= 120
