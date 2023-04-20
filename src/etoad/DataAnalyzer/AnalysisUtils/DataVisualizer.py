from typing import Union
import warnings
import numpy as np
import matplotlib.figure
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def suppress_warnings(func):
    """
    Decorator to suppress warnings (relevant for matplotlib functions raising multiple warnings).
    """
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return_value = func(*args, **kwargs)
        return return_value

    return wrapper


class DataVisualizer(object):
    """
    Class that combines helpful functions for visualizing / plotting experimental data as wrappers for matplotlib
    (currently mainly developed for electrochemical techniques).

    Operates solely on class method / class variable level, does not require instantiation.

    API / Public Methods:
        plot_single_curve(x_values, y_values, x_label, y_label, title, color)
        plot_multiple_curves(data_to_plot, x_label, y_label, title, colors, legend)
    """

    @classmethod
    @suppress_warnings
    def plot_single_curve(
            cls,
            x_values: Union[np.ndarray, list],
            y_values: Union[np.ndarray, list],
            x_label: str = "",
            y_label: str = "",
            title: str = "",
            color: tuple = (4/255, 129/255, 69/255),
            yaxis_percent: bool = False
    ) -> matplotlib.figure.Figure:
        """
        Plots a single curve.

        Args:
            x_values: Numpy array of x values.
            y_values: Numpy array of y values.
            x_label: Label of the x axis.
            y_label: Label of the y axis.
            title: Title of the plot.
            color: RGB tuple of the plot color.
            yaxis_percent: Format the y axis as percent.

        Returns:
            matplotlib._figure.Figure object of the plot.
        """
        figure: matplotlib.figure.Figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)

        ax.plot(x_values, y_values, marker="s", markersize=3, color=color)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)

        if yaxis_percent:
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
            ax.set_ylim(bottom=0)

        return figure

    @classmethod
    @suppress_warnings
    def plot_multiple_curves(
            cls,
            data_to_plot: Union[list, np.ndarray],
            x_label: str = "",
            y_label: str = "",
            title: str = "",
            colors: Union[tuple, list] = ((4/255, 129/255, 69/255), (207/255, 254/255, 232/255)),
            legend: Union[None, list] = None,
    ) -> matplotlib.figure.Figure:
        """
        Plots multiple curves (given as a list or ndarray) into a single diagram.

        Args:
            data_to_plot: List or ndarray of all data to be plotted ([[x1, y1], [x2, y2], ...]).
            x_label: Label of the x axis.
            y_label: Label of the y axis
            title: Title of the plot.
            colors: Tuple or list of colors.
                    - length = 1 -> all curves will be plotted in this single color
                    - length = 2 -> curves will be plotted as a gradient between these two colors
                    - length = len(data_to_plot) -> curves will be plotted in the given colors
            legend: List of legend entries for each curve to be plotted.

        Returns:
            matplotlib._figure.Figure object of the plot.

        Raises:
            IndexError if the color array does not have a length of 1, 2 or len(data_to_plot)
        """
        figure: matplotlib.figure.Figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)

        # sets colors
        if len(colors) == 1:
            colors = [colors[0]] * len(data_to_plot)
        elif len(colors) == 2:
            colors = cls._color_gradient(*colors, data_points=len(data_to_plot))
        elif len(colors) != len(data_to_plot):
            raise IndexError("The length of the color series could not be interpreted.")

        # plots the data
        for idx, curve in enumerate(data_to_plot):
            ax.plot(curve[0], curve[1], color=colors[idx], zorder=-idx)
            # ax.plot(curve[0], curve[1], marker="s", markersize=3, color=colors[idx], zorder=-idx)
            # plot with markers or without?

        # sets labels and titles
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)

        # modifies the legend to show maximum 10 entries (if applicable), sets the legend
        if legend:
            if len(legend) <= 10:
                ax.legend(legend)
            else:
                skip_every: int = int(len(legend) / 10) + 1
                for idx in range(len(legend)):
                    if (idx + 1) % skip_every != 0:
                        legend[idx] = "_" + legend[idx]
            ax.legend(legend)

        return figure

    @classmethod
    @suppress_warnings
    def plot_multiple_points(
            cls,
            data_to_plot: Union[list, np.ndarray],
            x_label: str = "",
            y_label: str = "",
            title: str = "",
            colors: Union[tuple, list] = ((4/255, 129/255, 69/255), (207/255, 254/255, 232/255)),
            legend: Union[None, list] = None,
    ) -> matplotlib.figure.Figure:
        """
        Plots multiple curves (given as a list or ndarray) into a single diagram.

        Args:
            data_to_plot: List or ndarray of all data to be plotted ([[x1, y1], [x2, y2], ...]).
            x_label: Label of the x axis.
            y_label: Label of the y axis
            title: Title of the plot.
            colors: Tuple or list of colors.
                    - length = 1 -> all curves will be plotted in this single color
                    - length = 2 -> curves will be plotted as a gradient between these two colors
                    - length = len(data_to_plot) -> curves will be plotted in the given colors
            legend: List of legend entries for each curve to be plotted.

        Returns:
            matplotlib.figure.Figure object of the plot.

        Raises:
            IndexError if the color array does not have a length of 1, 2 or len(data_to_plot)
        """
        figure: matplotlib.figure.Figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)

        # sets colors
        if len(colors) == 1:
            colors = [colors[0]] * len(data_to_plot)
        elif len(colors) == 2:
            colors = cls._color_gradient(*colors, data_points=len(data_to_plot))
        elif len(colors) != len(data_to_plot):
            raise IndexError("The length of the color series could not be interpreted.")

        # plots the data
        for idx, curve in enumerate(data_to_plot):
            ax.plot(curve[0], curve[1], "o",color=colors[idx], zorder=-idx)

        # sets labels and titles
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)

        # modifies the legend to show maximum 10 entries (if applicable), sets the legend
        if legend:
            if len(legend) <= 10:
                ax.legend(legend)
            else:
                skip_every: int = int(len(legend) / 10) + 1
                for idx in range(len(legend)):
                    if (idx + 1) % skip_every != 0:
                        legend[idx] = "_" + legend[idx]
            ax.legend(legend)

        return figure

    @classmethod
    def _color_gradient(
            cls,
            init_color: tuple,
            final_color: tuple,
            data_points: int
    ):
        """
        Performs linear interpolation between two colors.

        Args:
            init_color: RGB Tuple of the starting color of the gradient.
            final_color: RGB Tuple of the final color of the gradient.
            data_points: Number of data points for the color gradient.

        Returns:
            color_gradient: Np.ndarray of RGB tuples
        """
        color_gradient: np.ndarray = np.linspace(
            start=init_color,
            stop=final_color,
            num=data_points
        )

        return color_gradient



