import logging
import tkinter
from logging import Logger
import tkinter as tk
from pathlib import Path
from tkinter.scrolledtext import ScrolledText
from typing import Optional
import matplotlib
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from etoad.Utils import ConfigLoader
from PIL import Image, ImageTk
from .GenericHandler import GenericHandler
from .SlackBotHandler import SlackBotHandler
from .TkErrorHandling import TkErrorCatcher

tkinter.CallWrapper = TkErrorCatcher

matplotlib.use("Agg")

BACKGROUND = "#192B28"
BACKGROUND_LIGHT = "#fff"
WHITE = "#fff"
GREEN = "#048145"


class GraphicalInterface(Logger):

    # Defines the color scheme according to the MatterLab slide style
    dark_color = "#192B28"
    light_color = "#fff"
    highlight_color = "#048145"

    def __init__(self, logging_config: Path, log_file: Optional[Path] = None, refresh_rate: float = 5):
        """
        Constructor of the GraphicalInterface (combined logger and tkinter GUI).

        Sets the following attributes:
            _gui: Tkinter root object
            _gui_details: Dictionary of tkinter child objects embedded in the gui
            _figure: Matplotlib _figure for real-time plotting.
            _figure_details: Dictionary of matplotlib sub-objects and details.
            _refresh_time: Refreshing interval (in ms)
            _terminate: Boolean describing the status of the graphical interface (closed if True).
            _measurement_details: Dictionary of measurement names to generate the title.

        Args:
            logging_config: Path to the json file that contains the logging configuration.
            log_file: Path to the log file (optional).
            refresh_rate: Refresh rate for the plots (in Hz)
        """
        Logger.__init__(self, "EChem", "DEBUG")

        self._measurement_details: dict = {"sample": "Initialization", "experiment": "Establishing Connections"}
        self._refresh_time = int(1000 / refresh_rate)
        self._terminate = False

        self._gui: tk.Tk = tk.Tk()
        self._gui_details: dict = dict()
        self._setup_gui()

        self._figure = Figure()
        self._figure_details: dict = dict()
        self._setup_plot()

        self._setup_logging(logging_config, log_file)

    def _setup_gui(self) -> None:
        """
        Private method to set up the general structure of the tkinter graphical interface, composed of three frames.
            - title_frame (containing the current title and the logo)
            - plot_window (containing the matplotlib live plot)
            - log_window (containing the logging information)
        """
        # Set Up the Entire GUI Window
        self._gui.title("EToad – Electrochemical Technique Operation for Autonomous Discovery")
        height = int(0.9 * self._gui.winfo_screenheight())
        width = int(0.6 * self._gui.winfo_screenwidth())
        self._gui.geometry(f"{width}x{height}")
        self._gui.config(background=BACKGROUND)

        # Set Up the Title / Label at the Top
        self._gui_details["title_frame"] = tk.Frame(self._gui, width=0.9 * width, height=0.1 * height, background=BACKGROUND)
        img = ImageTk.PhotoImage(Image.open(Path(__file__).parent / "MatterLab.png").resize(size=(int(0.1*height), int(0.1*height))))
        self._gui_details["logo_label"] = tk.Label(self._gui_details["title_frame"], background=BACKGROUND, image=img)
        self._gui_details["logo_label"].image = img
        self._gui_details["title_label"] = tk.Label(self._gui_details["title_frame"], text=self.title, background=BACKGROUND, foreground=WHITE, font=("Arial", 24))
        self._gui_details["title_frame"].pack(side="top", fill="both")
        self._gui_details["logo_label"].pack(side="right", fill="both")
        self._gui_details["title_label"].pack(side="top", fill="both", expand=True, padx=(int(0.1 * height), 0))

        # Set Up The Plotting Window
        self._gui_details["plot_window"] = tk.Frame(self._gui, height=0.6 * height, width=0.9 * width, background=BACKGROUND_LIGHT)
        self._gui_details["plot_window"].pack(side="top", fill="both", padx=20, pady=10)

        # Set Up the Logging Window
        self._gui_details["log_window"] = tk.Frame(self._gui, height=0.3 * height, width=0.9 * width, background=BACKGROUND)
        self._gui_details["log_record"] = ScrolledText(self._gui, background=BACKGROUND_LIGHT, foreground=BACKGROUND, font=("Arial", 12), spacing3=4, highlightbackground=BACKGROUND_LIGHT)
        self._gui_details["log_record"].pack(in_=self._gui_details["log_window"], expand=True, fill="both", side="left")
        self._gui_details["log_window"].pack(side="bottom", fill="both", padx=20, pady=10)

    def _setup_logging(self, config_file: Path, log_file: Optional[Path] = None) -> None:
        """
        Private method to set up all formatters and handlers for the logging machinery.
        Parses the logging config dictionary (format standards as required by the logging module).

        Args:
            config_file: Path to the configuration dictionary (json file).
            log_file: Optional: Path to the specific log file. If None is given, the default file is used.
        """
        logging_config: dict = ConfigLoader.load_config(config_file, required_keys={"formatters", "handlers"})

        formatters: dict = dict()
        for formatter, settings in zip(logging_config["formatters"], logging_config["formatters"].values()):
            formatters[formatter] = logging.Formatter(**settings)

        for handler, settings in zip(logging_config["handlers"], logging_config["handlers"].values()):
            handler_type = settings.pop("class")
            formatter = settings.pop("formatter")
            level = settings.pop("level")

            # Specific treatment for GenericHandler (logging via GUI) and FileHandler (optional setting of logfile).
            if handler_type == "GenericHandler":
                settings["logging_function"] = self._log_message
            if handler_type == "logging.FileHandler" and log_file:
                settings["filename"] = str(log_file)

            handler_object = eval(handler_type)(**settings)
            handler_object.setFormatter(formatters[formatter])
            handler_object.setLevel(level)
            self.addHandler(handler_object)

    def _setup_plot(self):
        """
        Private method to set up all the formatting and display details of the plot (colors, styles, fonts, ...).
        Generates the Canvas and the Navigation Toolbar and packs them into the GUI.
        """
        self._figure.patch.set_facecolor(BACKGROUND_LIGHT)
        self._figure_details["plot"] = self._figure.add_subplot(111)
        self._figure_details["plot"].patch.set_facecolor(BACKGROUND_LIGHT)
        self._figure_details["x_axis_title"] = ""
        self._figure_details["y_axis_title"] = ""
        for label in (self._figure_details["plot"].get_xticklabels() + self._figure_details["plot"].get_yticklabels()):
            label.set_fontname("Arial")

        # Sets up the Canvas in which the Figure is displayed, and the Toolbar
        canvas = FigureCanvasTkAgg(self._figure, self._gui_details["plot_window"])
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, self._gui_details["plot_window"])
        toolbar.config(background=BACKGROUND_LIGHT, highlightcolor=WHITE)
        for child in toolbar.winfo_children():
            child.config(background=BACKGROUND_LIGHT)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    @property
    def sample_name(self) -> str:
        """
        Getter for the sample name that is currently running.

        Returns:
            str: Name of the sample.
        """
        return self._measurement_details["sample"]

    @sample_name.setter
    def sample_name(self, sample_name: str) -> None:
        """
        Setter for the sample name property.

        Args:
            sample_name: New sample name to be set.
        """
        self._measurement_details["sample"] = sample_name
        self._gui_details["title_label"]["text"] = self.title

    @property
    def experiment_name(self) -> str:
        """
        Getter for the experiment name that is currently running.

        Returns:
            str: Name of the experiment
        """
        return self._measurement_details["experiment"]

    @experiment_name.setter
    def experiment_name(self, experiment_name: str) -> None:
        """
        Setter for the name of the experiment that is currently running.

        Args:
            experiment_name: Name of the experiment
        """
        self._measurement_details["experiment"] = experiment_name
        self._gui_details["title_label"]["text"] = self.title

    @property
    def title(self) -> str:
        """
        Getter for the title of the current experiment (composed of sample name and experiment name).

        Returns:
            str: Title of the current experiment
        """
        return f"{self._measurement_details['sample']} – {self._measurement_details['experiment']}"

    def start_gui(self) -> None:
        """
        Public method to open the GUI window.
        Blocks the main thread – after execution of this function, it can only be terminated from other threads.
        """
        _ = animation.FuncAnimation(self._figure, lambda x: None, interval=self._refresh_time)
        self._check_for_termination()
        self._gui.mainloop()

    def _check_for_termination(self) -> None:
        """
        Loop to be run iteratively. Destroys the root if the _terminate attribute has been set to True.
        """
        if self._terminate:
            self._gui.destroy()
            return

        self._gui.after(self._refresh_time, self._check_for_termination)

    def stop_gui(self) -> None:
        """
        Public method to stop the running GUI from an external thread.
        """
        self._terminate = True

    def _log_message(self, message: str) -> None:
        """
        Creates a log entry by printing the formatted message into the log_window of the tkinter GUI.

        Args:
            message: Formatted message, as passed by the Logger.
        """
        self._gui_details["log_record"].insert("end", f"{message} \n")
        self._gui_details["log_record"].see("end")

    def start_plotting(self, experiment_name: str, x_axis_label: str, y_axis_label: str) -> None:
        """
        Public method to set up a new plot for a new measurement.

        Args:
            experiment_name: Name of the experiment
            x_axis_label: Label for the x axis of the plot
            y_axis_label: Label for the y axis of the plot
        """
        self.experiment_name = experiment_name
        self._figure_details["x_axis_title"] = x_axis_label
        self._figure_details["y_axis_title"] = y_axis_label

    def update_plot(self, x_values, y_values) -> None:
        """
        Public method to update the data that is plotted in the plotting frame.

        Args:
            x_values: 1D Numpy array of x values to plot
            y_values: 1D Numpy array of y values to plot
        """
        try:
            self._figure_details["plot"].clear()
            self._figure_details["plot"].set_xlabel(self._figure_details["x_axis_title"], fontname="Arial", fontweight="bold")
            self._figure_details["plot"].set_ylabel(self._figure_details["y_axis_title"], fontname="Arial", fontweight="bold")
            self._figure_details["plot"].plot(x_values, y_values, color=GREEN, linewidth=2)
            self._figure.tight_layout()
        except IndexError:
            pass
