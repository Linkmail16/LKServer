from setuptools import setup, find_packages
import os

long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

requirements = ["websockets>=12.0"]
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lkserver",
    version="1.0.1",
    author="Linkmail16",
    description="Expose your local Python servers to the internet instantly",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Linkmail16/lkserver",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    keywords="server tunnel http websocket ngrok localtunnel expose localhost",
    project_urls={
        "Bug Reports": "https://github.com/Linkmail16/lkserver/issues",
        "Source": "https://github.com/Linkmail16/lkserver",
    },
)
