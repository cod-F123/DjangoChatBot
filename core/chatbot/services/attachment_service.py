from pypdf import PdfReader


class AttachmentService:

    @staticmethod
    def extract_text(attachment):

        mime_type = attachment.mime_type

        if mime_type != "application/pdf":
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

                return "\n\n".join(pages)

            finally:
                attachment.file.close()

        except Exception as e:
            return ""
