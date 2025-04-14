from setuptools import setup, find_packages
from pathlib import Path

def read_requirements():
    req_path = Path(__file__).parent / "requirements.txt"
    with req_path.open("r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="depth_eval",  
    version="0.1.0",
    description="Monocular depth estimation evaluation tools",
    author="JiahaoZhang, Hongjie Zheng, Jining Yang",
    packages=find_packages(exclude=["automation","metric_depth","tests"]),
    install_requires=read_requirements(),
    extras_require={
        "dev": ["pytest"]
    },
    include_package_data=True,
    python_requires=">=3.9",
)