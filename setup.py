from setuptools import setup, find_packages

setup(
    name="zdem-plot-damage-evolution",
    version="1.1.0",
    description="ZDEM 岩石渐进破裂与损伤阈值分析系统 / Progressive Failure & Damage Threshold Analysis for ZDEM Rock Simulations",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering",
    ],
)
