import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gear-bot-core",
    version="0.0.2",
    author="vanchpuck",
    author_email="vanchpuck@mail.ru",
    description="Core bot components for the GearScanner project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vanchpuck/gear-bot-core",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.6',
)