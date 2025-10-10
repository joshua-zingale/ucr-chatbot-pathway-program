import io

from sqlalchemy.orm import Session

from ucr_chatbot.api.embedding import embed_text
from ucr_chatbot.api.hashing import hash_bytes
from ucr_chatbot.api.file_parsing import FileParsingError, parse_file
from ucr_chatbot.api.file_storage import get_storage_service

from .models import get_engine, Document, Segment, Embedding


def add_document_to_course(
    file_data: io.BytesIO, name: str, extension: str, course_id: int
) -> None:
    """Adds a document to a course, parsing it into segments for the RAG database.

    Must be called from inside a flask app context.

    :param file_data: the file data
    :param name: the name of the file
    :param extension: the file extension of the file without the '.', for example 'pdf'
    :param course_id: the id of the course in which to add the document

    :throws FileParsingError: if the file cannot be parsed.
        If thrown, the document is not added.
    :throws ValueError: if an identical file has already been uploaded for the course.
        If thrown, the document is not added.
    """

    file_hash = hash_bytes(file_data)

    with Session(get_engine()) as session:
        document = (
            session.query(Document)
            .filter_by(
                file_hash=file_hash,
                course_id=course_id,
            )
            .first()
        )
        if document:
            raise ValueError(
                f"An identical file, '{document.name}', has already been uploaded for this course.",
            )

    segments = None
    file_data.seek(0)

    segments = parse_file(file_data, extension)

    if len(segments) == 0:
        raise FileParsingError(
            "Could not understand any textual data from the uploaded file.", "error"
        )

    with Session(get_engine()) as session:
        document = Document(
            name=name,
            file_hash=file_hash,
            course_id=course_id,
            file_extension=extension,
        )
        session.add(document)
        session.flush()
        for seg in segments:
            segment = Segment(text=seg, document_id=document.id)
            session.add(segment)
            session.flush()
            session.add(Embedding(vector=embed_text(seg), segment_id=segment.id))
        session.commit()

        file_path = document.full_file_path

    file_data.seek(0)
    get_storage_service().save_file(file_data, file_path)
