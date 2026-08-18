from setuptools import setup, find_packages

setup(
    name='apparate',
    version='0.2.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "PyGithub",
        "playwright"
    ],
    entry_points='''
        [console_scripts]
        apparate=scripts.apparate:apparate
    ''',
)
