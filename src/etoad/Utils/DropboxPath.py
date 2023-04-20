from pathlib import Path


# ATTN: This is very specific to our group's setup and shouldn't be part of the public version
def get_dropbox_path() -> Path:
    for directory in Path(__file__).parents:
        if "Dropbox" in directory.name:
            return directory
