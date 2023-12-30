import subprocess
import setuptools

try:
    ret = subprocess.check_output(
        "git describe --tags --abbrev=0",
        shell=True,
    )
    version = ret.decode("utf-8").strip()
except:
    version = "main"

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

setuptools.setup(
    name="sphinxext-rediraffe",
    version=version,
    author="Vasista Vovveti",
    author_email="vasistavovveti@gmail.com",
    description="Sphinx Extension that redirects non-existent pages to working pages.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wpilibsuite/sphinxext-rediraffe",
    packages=["sphinxext"],
    install_requires=["sphinx>=4.0"],
    classifiers=[
        "Environment :: Plugins",
        "Environment :: Web Environment",
        "Framework :: Sphinx :: Extension",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    include_package_data=True,
)
