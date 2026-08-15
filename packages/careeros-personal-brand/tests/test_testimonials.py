"""Tests for Testimonial / TestimonialRepository."""

from __future__ import annotations

from careeros_personal_brand import Testimonial


def test_saved_testimonial_appears_in_list_all(testimonial_repository):
    testimonial = Testimonial(author_name="Jane Smith", quote="Great to work with.")
    testimonial_repository.save(testimonial)
    assert testimonial_repository.list_all() == [testimonial]


def test_list_for_project_filters_by_project_id(testimonial_repository, project):
    matching = Testimonial(author_name="Jane", quote="Loved it.", project_id=project.id)
    other = Testimonial(author_name="Bob", quote="Also good.", project_id="other-project")
    testimonial_repository.save(matching)
    testimonial_repository.save(other)
    assert testimonial_repository.list_for_project(project.id) == [matching]
