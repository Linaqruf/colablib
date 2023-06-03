from setuptools import setup, find_packages

setup(
    name='colablib',
    version='0.1.7',
    packages=find_packages(),
    install_requires=[
        'safetensors==0.2.6',
        'requests==2.28.2',
        'tqdm==4.65.0',
    ],
    author='Furqanil Taqwa',
    author_email='furqanil.taqwa@gmail.com',
    description='A utility library for Google Colab',
    url='https://github.com/Linaqruf/colablib',
)
