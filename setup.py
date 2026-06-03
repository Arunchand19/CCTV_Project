from setuptools import setup, find_packages

setup(
    name="cctv-analytics",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask==3.0.0",
        "opencv-python-headless==4.10.0.84",
        "numpy>=1.24.0,<2.0.0",
        "werkzeug==3.0.1",
        "gunicorn==21.2.0",
    ],
)
