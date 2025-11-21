# setup.py
from setuptools import setup, find_packages

setup(
    name='WWMogi',
    version='1.0.0',
    description='A PyQt6 leaderboard application for a GraphQL API endpoint.',
    author='Landon Yates',
    url='https://github.com/LandonYates1/WWMogi',

    # This now correctly finds the 'wwmogi' folder inside 'src'
    package_dir={'': 'src'},
    packages=find_packages(where='src'),

    # Update paths to include resources inside the package directory
    package_data={
        'wwmogi': [ # Specify the package name here
            'resources/*.png',
            'resources/*.qss'
        ]
    },
    include_package_data=True,

    install_requires=[
        'PyQt6',
        'requests',
        'pandas',
    ],

    entry_points={
        'console_scripts': [
            # FIX 1: Corrected typo (main_gui instead of gui_wwmogi)
            # FIX 2: Added package prefix (wwmogi.main_gui:main)
            'wwmogi-app = wwmogi.main_gui:main',
        ],
    },
    python_requires='>=3.8',
)
