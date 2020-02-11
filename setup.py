import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='gkeep-sync',
    version='0.0.1-beta',
    author='Kamen Kanev',
    author_email='kamen.e.kanev@gmail.com',
    license='MIT',
    description='A Service that syncs your Google Keep notes with your local file system',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/kanevk/gkeep-files-sync',
    packages=setuptools.find_packages(),
    scripts=['bin/gkeep_sync', 'bin/gkeep_update_config'],
    keywords=['google keep', 'keep', 'notes'],
    install_requires=[
        'watchdog',
        'gkeepapi'
    ],
    download_url='https://github.com/kanevk/gkeep-files-sync/archive/0.0.1-alpha.tar.gz',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
    python_requires='>=3.6',
)
