from setuptools import setup

with open("requirements.txt", "r") as req_file:
    requirements = req_file.readlines()

if __name__ == "__main__":
    setup(
        install_requires=requirements
    )
