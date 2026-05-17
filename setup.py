from setuptools import find_packages, setup


setup(
    name="ap-skill-generator",
    version="0.1.0",
    description="Skill-based AP-style content generation engine",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pydantic>=2.7.0",
        "fastapi>=0.111.0",
        "uvicorn>=0.30.0",
        "httpx>=0.27.0",
        "sqlalchemy>=2.0.30",
        "streamlit>=1.35.0",
    ],
    extras_require={"dev": ["pytest>=8.2.0", "pytest-cov>=5.0.0"]},
)
