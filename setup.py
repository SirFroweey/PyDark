from setuptools import setup

setup(
        name='PyDark',
        description='''PyDark is a 2D and Online Multiplayer
                video game engine written on-top of Python
                of Python and PyGame.''',
        packages = ['PyDark'],
        install_requires = [
            'Twisted >= 14.0.2',
            'pygame >= 1.9.1release',
            'pillow >= 2.7.0',
        ],
        )
