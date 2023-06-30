from setuptools import setup, find_packages

setup(
    name='colablib',
    version='0.1.8',
    packages=find_packages(),
    install_requires=[
        'safetensors==0.3.1',
        'requests==2.27.1',
        'tqdm==4.65.0',
        'PyYAML==6.0',
        'gdown==4.7.1',
        'toml==0.10.2',
        'rarfile==4.0',
        'xmltodict==0.13.0',
        'pydantic==1.10.9'
    ],
    author='Furqanil Taqwa',
    author_email='furqanil.taqwa@gmail.com',
    description='A utility library for Google Colab',
    url='https://github.com/Linaqruf/colablib',
)
