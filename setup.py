from setuptools import find_packages, setup
from marel_marine_scale_controller import VERSION

setup(
    name="marel_marine_scale_controller",
    version=VERSION,
    author="JeromeJGuay",
    author_email="jerome.guay@dfo-mpo.gc.ca",
    description="""Marel Marine Scale Controller App.""",
    long_description_content_type="text/markdown",
    url="https://github.com/iml-gddaiss/marel_marine_scale_controller",
    packages=find_packages(),
    package_data={"": ["*.json", "*.lua"]},
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
    python_requires="~=3.10",
)