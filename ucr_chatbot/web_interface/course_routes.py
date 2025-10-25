import typing as t


from flask import (
    Blueprint,
    request,
    jsonify,
    abort,
)
from flask_login import login_required  # type: ignore
from pydantic import BaseModel as PydanticModel

from ucr_chatbot.decorators import roles_required
from ucr_chatbot.db.models import (
    Session,
    get_engine,
    Course,
)


bp = Blueprint("course_routes", __name__)


def get_course_from_url(kwargs: dict[str, t.Any]):
    """Gets the course id from the url"""
    return int(kwargs["course_id"])


@bp.get("/courses/<int:course_id>")
@login_required
@roles_required(["instructor"], get_course_from_url)
def get_course(course_id: int):
    """Respnds with a JSON representation of a course."""
    with Session(get_engine()) as session:
        course = session.get(Course, course_id)
        if course is None:
            abort(404)
        return jsonify(
            CourseResponse(
                id=course.id,  # type: ignore
                name=str(course.name),
                chatbot_instructions=str(course.chatbot_instructions),
            )
        )


@bp.patch("/courses/<int:course_id>")
@login_required
@roles_required(["instructor"], get_course_from_url)
def patch_course(course_id: int):
    """Updates a conversation."""
    data = PatchCourseRequest.model_validate(request.json)
    with Session(get_engine()) as session:
        course = session.get(Course, course_id)
        if course is None:
            abort(404)
        if data.chatbot_instructions is not None:
            course.chatbot_instructions = data.chatbot_instructions  # type: ignore
        session.commit()

    return "", 204


class CourseResponse(PydanticModel):
    id: int
    name: str
    chatbot_instructions: str


class PatchCourseRequest(PydanticModel):
    chatbot_instructions: t.Optional[str]
