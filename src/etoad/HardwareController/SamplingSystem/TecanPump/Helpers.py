__author__ = "Tony C. Wu (@verysure), Felix Strieth-Kalthoff (@felix-s-k)"


from functools import wraps
from typing import Optional, Any, List, Tuple, Iterable, Callable, Union


class CmdNameMap(object):
    """
    Object to handle the mapping between command names / levels and the corresponding numerical values.
    """
    def __init__(self, pairs: List[Tuple[int, str]]):
        """
        Instantiates the CmdNameMap. Saves all command names as UPPERCASE strings.

        Args:
            pairs: List of (int, str) tuples.
        """
        self.forward: dict = {}
        self.reverse: dict = {}
        for cmd, name in pairs:
            self.forward[cmd] = name.upper()
            self.reverse[name.upper()] = cmd

    def get(self, cmd: int) -> str:
        """
        Get the command level string from the numerical value.

        Args:
            cmd: Numerical value

        Returns: str
        """
        return self.forward.get(cmd, None)

    def rget(self, name: str) -> int:
        """
        Get the numerical value from the command level string.

        Args:
            name: Command level string.

        Returns: int
        """
        return self.reverse.get(name.upper(), None)

    @property
    def cmds(self) -> Iterable[int]:
        """
        Returns all numerical values saved in the mapping.
        """
        return self.forward.keys()

    @property
    def names(self) -> Iterable[str]:
        """
        Returns all command level names in the mapping.
        """
        return self.reverse.keys()


def mapgetmethod(
        cmd_name_map: CmdNameMap
):
    """
    Decorator generation for methods that require mapping of integer command settings and command names
    (as specified in the CmdNameMap).

    Args:
        cmd_name_map: CmdNameMap object

    Raises:
        ValueError: If the required name is not part of the cmd_name_map.
    """
    def func_wrapper(func_ret_cmd):
        @wraps(func_ret_cmd)
        def func_ret_name(self):
            name: str = cmd_name_map.get(func_ret_cmd(self))
            if name is not None:
                return name
            else:
                raise ValueError(f"Error in function {func_ret_name.__name__}")
        return func_ret_name
    return func_wrapper


def mapsetmethod(cmd_name_map):
    """
    Decorator generation for methods that require mapping of command names and integer command settings
    (as specified in the CmdNameMap).

    Args:
        cmd_name_map: CmdNameMap object

    Raises:
        ValueError: If the required name is not part of the cmd_name_map.
    """
    def func_wrapper(func_with_cmd):
        @wraps(func_with_cmd)
        def func_with_name(self, name):
            cmd: int = cmd_name_map.rget(name)
            if cmd is not None:
                return func_with_cmd(self, cmd)
            else:
                raise ValueError(f"Variable <{func_with_cmd.__name__[4:]}> should be {', '.join(cmd_name_map.names)}")
        return func_with_name
    return func_wrapper


def rangemethod(
        min_value: Any,
        max_value: Any,
        dtype: Optional[type] = None
):
    """
    Decorator generation for a method that can operate with argument values of a given type and in a given range.

    Args:
         min_value: Minimum value of the argument.
         max_value: Maximum value of the argument.
         dtype: Data type of the argument data.

    Raises:
        TypeError: If the data type of the variable and the specified dtype are incompatible.
        ValueError: If the passed value is outside the boundaries.
    """
    def func_wrapper(func):
        @wraps(func)
        def func_with_range(self, value: Any, lower_boundary: Any = min_value, upper_boundary: Any = max_value):
            # get the numeric values of the min and max values if the values are passed as strings
            lower_boundary = getattr(self, lower_boundary)() if isinstance(lower_boundary, str) else lower_boundary
            upper_boundary = getattr(self, upper_boundary)() if isinstance(upper_boundary, str) else upper_boundary

            if (dtype is not None) and (not isinstance(value, dtype)):
                raise TypeError(f"Variable <{func.__name__[4:]}> should be of type {dtype}")
            elif lower_boundary <= value <= upper_boundary:
                return func(self, value)  # ATTN: Modified for return (FSK, Sep 19)
            else:
                raise ValueError(f"Variable <{func.__name__[4:]}> should be between {lower_boundary} and {upper_boundary}.")
        return func_with_range
    return func_wrapper


def add_set_get(cls):
    """
    Class decorator to add a get at set method to a class, which can get / set all attributes of a class in a single
    function call.

    Requires the individual getters / setters to be named as "get_{VAR}" and "set_{VAR}", respectively.
    """

    def _get_method(self, method: str) -> Callable:
        """
        Returns a method from the parent class based on its method name, passed as a string.
        """
        def err_message(*args):
            print(f"No method {method}")
        return getattr(self, method, err_message)

    def set_func(self, **kwargs) -> None:
        """
        General set function that sets each variable passed as a kwarg to the respective value.
        """
        for var, value in kwargs.items():
            _get_method(self, 'set_'+var)(value)

    def get_func(self, *args) -> Union[Any, List]:
        """
        General get function that gets all values of the variables passed as args.
        """
        responses = []
        for var in args:
            value = _get_method(self, 'get_'+var)()
            if value is not None:
                responses.append(value)

        if len(responses) == 1:
            return responses[0]
        else:
            return responses

    setattr(cls, 'set', set_func)
    setattr(cls, 'get', get_func)

    return cls
