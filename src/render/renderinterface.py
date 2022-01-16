from io import TextIOWrapper
from core.traceprocessor import TraceProcessor
import pickle


class RenderInterface:
    def __init__(self, fileObject: TextIOWrapper, **argv):
        self.traceProcessor: TraceProcessor = pickle.load(fileObject)

    def render(self, **argv):
        pass
