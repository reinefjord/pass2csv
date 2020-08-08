import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pass2csv",
    version="0.1.3",
    author="Rupus Reinefjord",
    author_email="rupus@reinefjord.net",
    description='Export pass(1), "the standard unix password manager", to CSV',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["python-gnupg"],
    scripts=["pass2csv"],
    url="https://github.com/reinefjord/pass2csv",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    python_requires='>=3.6'
)
