from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class AttachmentService:

    @staticmethod
    def extract_text(attachment):

        if attachment.extracted_content:
            return attachment.extracted_content

        if attachment.mime_type != "application/pdf":
            return ""

        try:
            attachment.file.open("rb")

            try:
                reader = PdfReader(attachment.file)
                pages = []

                for page in reader.pages:
                    text = page.extract_text() or ""

                    if text.strip():
                        pages.append(text)

                extracted_text = "\n\n".join(pages)

            finally:
                attachment.file.close()

            if extracted_text:
                attachment.extracted_content = extracted_text
                attachment.save(update_fields=["extracted_content"])

            return extracted_text

        except Exception:
            logger.exception(
                "Failed to extract text from attachment %s",
                attachment.pk,
            )
            return ""
