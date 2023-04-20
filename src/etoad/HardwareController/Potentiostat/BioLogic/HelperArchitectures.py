#import kbio_types as KBIO
from .kbio_types import *

# TODO: Refactor and properly implement

def pp_plural(nb, label, num=True, nothing=''):
    """Return a user friendly version of an ordinal and a label.

       num is used to force a number version,
       nothing is what to say if there is nothing
    """
    if nb == 0:
        if nothing:
            en_clair = f"{nothing}"
        else:
            en_clair = f"{0 if num else 'no'} {label}"
    elif nb == 1:
        en_clair = f"{1 if num else 'one'} {label}"
    else:
        en_clair = f"{nb} {label}s"
    return en_clair


class LPDeviceInfo(DeviceInfo):  # TODO: Needs to be re-named properly
    """
    Object Infrastructure that the DLL interface needs for writing device information.
    """
    @property
    def model(self) -> str:
        """
        Getter for the instrument name.

        Returns:
            device.name: Name of the instrument.
        """
        device = DEVICE(self.DeviceCode)
        return device.name


class ChannelInfo(ChannelInfo):
    """
    Object infrastructure that the DLL interface needs for writing channel information.

    TODO: Currently just adapted from the original API documentation.
    TODO: Requires proper implementation
    """
    @property
    def firmware(self):
        firmware = FIRMWARE(self.FirmwareCode)
        return firmware.name

    @property
    def has_no_firmware(self):
        firmware = FIRMWARE(self.FirmwareCode)
        has_no_firmware = (firmware.value == 0)
        return has_no_firmware

    @property
    def is_kernel_loaded(self):
        firmware = FIRMWARE(self.FirmwareCode)
        return (firmware.name == "KERNEL")

    @property
    def board(self):
        board = CHANNEL_BOARD(self.BoardVersion)
        return board.name

    @property
    def state(self):
        state = PROG_STATE(self.State)
        return state.name

    @property
    def amplifier(self):
        amplifier = AMPLIFIER(self.AmpCode)
        return amplifier.name

    @property
    def min_IRange(self):
        min_IRange = I_RANGE(self.MinIRange)
        return min_IRange.name

    @property
    def max_IRange(self):
        max_IRange = I_RANGE(self.MaxIRange)
        return max_IRange.name

    def __str__(self):

        fragments = list()

        if self.has_no_firmware:

            fragments.append(f"{self.board} board, no firmware")

        elif self.is_kernel_loaded:

            fragments.append(f"Channel: {self.Channel + 1}")
            fragments.append(f"{self.board} board, S/N {self.BoardSerialNumber}")
            fragments.append(f"{'has a' if self.Lcboard else 'no'} LC head")
            fragments.append(f"{'with' if self.Zboard else 'no'} EIS capabilities")
            fragments.append(pp_plural(self.NbOfTechniques, "technique"))
            fragments.append(f"State: {self.state}")

            if self.NbAmps:
                fragments.append(f"{self.amplifier} amplifier (x{self.NbAmps})")
            else:
                fragments.append(f"no amplifiers")

            fragments.append(f"IRange: [{self.min_IRange}, {self.max_IRange}]")
            fragments.append(f"MaxBandwidth: {self.MaxBandwidth}")

            memsize = self.MemSize
            if memsize:
                fragments.append(
                    f"Memory: {self.MemSize / 1024:.1f}KB"
                    f" ({(self.MemFilled / self.MemSize * 100.):.2f}% filled)"
                )
            else:
                fragments.append("Memory: 0KB")

            version = self.FirmwareVersion / 1000
            vstr = f"{version * 10:.2f}" if version < 1. else f"{version:.3f}"

            fragments.append(
                f"{self.firmware} (v{vstr}), "
                f"FPGA ({self.XilinxVersion:04X})"
            )

        else:

            version = self.FirmwareVersion / 100
            vstr = f"{version * 10:.2f}" if version < 1. else f"{version:.3f}"
            fragments.append(
                f"{self.firmware} (v{vstr}), "
                f"FPGA ({self.XilinxVersion:04X})"
            )

        en_clair = ', '.join(fragments)
        return en_clair



