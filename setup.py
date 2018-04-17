from setuptools import setup
setup(
  name = 'aiohttp-aiopylimit',
  packages = ['aiohttp_aiopylimit'],
  description = 'A utlity package to help with distributed rate limiting with aiohttp and redis',
  author='David Markey',
  author_email='david@dmarkey.com',
  use_scm_version=True,
  setup_requires=['setuptools_scm'],
  url='https://github.com/dmarkey/aiohttp-aiopylimit',
  install_requires=[
      'aiopylimit<=0.2.2',
  ],
  keywords=['rate limiting', 'throttle', 'redis', 'asyncio', 'aiohttp'],
  classifiers=[],
)
