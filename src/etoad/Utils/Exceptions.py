class WorkflowError(Exception):
    """Base class for specific exceptions related to workflow management."""

    def __init__(self, *args):
        super().__init__(*args)


class SkipExecution(WorkflowError):
    """Exception to be raised when a certain operation is to be skipped."""

    def __init__(self, *args):
        super().__init__(*args)


class StopExecution(WorkflowError):
    """Exception to be raised when a certain measurement should be cancelled."""

    def __init__(self, *args):
        super().__init__(*args)
