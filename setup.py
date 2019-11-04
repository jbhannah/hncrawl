from setuptools import find_packages, setup

setup(name="hncrawl",
      version="0.1.0",
      description="A simple Hacker News cralwer",
      author="Jesse B. Hannah",
      author_email="jesse@jbhannah.net",
      packages=find_packages("."),
      url="https://github.com/jbhannah/hncrawl",
      license="MIT",
      entry_points={"console_scripts": "hncrawl = hncrawl:main"})
