from setuptools import setup, find_namespace_packages

with open("README.md", 'r') as fh:
    long_description = fh.read()

setup(
    name="galen-view",
    version="0.0.2",
    author="Travis Bauer",
    author_email="tlbauer@sandia.gov",
    license='MIT',
    description="A utility for viewing and exploring the cord-19 dataset",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sandialabs/galen-view",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "holoviews[recommended]",
        "whoosh",
        "cord-19-tools",
        "scikit-learn",
	"requests" # needed by cord-19-tools, not in setup.py as of 4/17/20
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
    
