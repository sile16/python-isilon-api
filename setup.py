from distutils.core import setup

setup(
    name='isilon',
    description='Python library for using the Isilon API',
    version='0.1',
    author='Matt Robertson',
    author_email='sile16@gmail.com',
    packages=['isilon'],
    requires=['requests'],
    license='MIT',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'

    ))