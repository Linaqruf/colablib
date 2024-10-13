from setuptools import setup, find_packages

setup(
    name='colablib',
    version='0.1.8',
    packages=find_packages(),
    install_requires=[
        'safetensors',
        'requests',
        'tqdm',
        'PyYAML',
        'gdown',
        'toml',
        'rarfile',
        'xmltodict',
        'pydantic'
    ],
    author='Furqanil Taqwa',
    author_email='furqanil.taqwa@gmail.com',
    description='A utility library for Google Colab',
    url='https://github.com/Linaqruf/colablib',
)
