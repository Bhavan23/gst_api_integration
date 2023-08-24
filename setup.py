from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in gst_api_integration/__init__.py
from gst_api_integration import __version__ as version

setup(
	name="gst_api_integration",
	version=version,
	description="GST API Setups",
	author="aerele",
	author_email="hello.aerele.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
