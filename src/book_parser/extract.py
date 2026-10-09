import pymupdf


def read_all_pages(path: str) -> str:
    with pymupdf.open(path) as doc:
        return "\n".join(page.get_text() for page in doc)


def read_first_pages(path: str, count: int = 3) -> str:
    texts: list[str] = []
    i = 0
    with pymupdf.open(path) as doc:
        for page in doc:
            texts.append(page.get_text())
            i += 1
            if i == count:
                break
    return "\n".join(texts)
