import pymupdf


def get_number_of_chapters(path: str) -> int:
    with pymupdf.open(path) as doc:
        return doc.chapter_count


def read_chapter(path: str, chapter: int = 0) -> str:
    with pymupdf.open(path) as doc:
        return "\n".join(
            doc[(chapter, pno)].get_text()
            for pno in range(doc.chapter_page_count(chapter))
        )
