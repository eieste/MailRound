import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mailround",
    version="1.0.1",
    author="Stefan Eiermann",
    author_email="python-org@ultraapp.de",
    description="Simple tool to check the sending and receiving of e-mails.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eieste/MailRound",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Communications :: Email :: Mail Transport Agents",
        "Topic :: Communications :: Email :: Post-Office",
        "Topic :: Communications :: Email :: Post-Office :: IMAP",
        "Topic :: Communications :: Email :: Post-Office :: POP3",
        "Topic :: Communications :: Email",
        "Topic :: System :: Monitoring"
    ],
)

