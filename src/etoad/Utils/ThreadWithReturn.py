from typing import Any
import threading


class ThreadWithReturn(threading.Thread):
    """
    Threading object that returns the return value of the target function upon calling the join() method.
    """

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        """
        Constructor of the ThreadWithReturn class. Calls the constructor of the threading.Thread class.
        Sets the attribute _return to None.

        Args [from threading.Thread documentation]:
            group: Should be None; reserved for future extension when a ThreadGroup class is implemented.
            target: Callable object to be invoked by the run() method. Defaults to None, meaning nothing is called.
            name: Thread name. By default, a unique name is constructed of the form "Thread-N" where N is a small decimal number.
            args: Argument tuple for the target invocation. Defaults to ().
            kwargs: Dictionary of keyword arguments for the target invocation. Defaults to {}.
        """
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self) -> None:
        """
        Re-defines the run() method of threading.Thread.
        Calls and executes the target function, and saves the return value into the _return attribute.
        """
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args) -> Any:
        """
        Re-defines the join() method of threading.Thread.
        Joins the thread into the main thread, and returns the previously saved _return attribute.
        """
        threading.Thread.join(self, *args)
        return self._return
