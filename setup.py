import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pass2csv",
    version="0.1.0",
    author="Rupus Reinefjord",
    author_email="rupus@reinefjord.net",
    description='Export pass(1), "the standard unix password manager", to CSV',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["python-gnupg"],
    scripts=["pass2csv"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
    ]
)
