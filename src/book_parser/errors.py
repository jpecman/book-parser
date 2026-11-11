# An expected problem caused by the user's input or setup. The CLI prints the
# message and exits; anything else is a bug and keeps its traceback.
class BookParserError(Exception):
    pass
