from setuptools import setup, find_packages

version = '2.0.0'
install_requires = ['aioes', 'aiohttp']
tests_require = install_requires + ['pytest']


setup(name='castlehps',
      version=version,
      description="",
      long_description="",
      classifiers=[],
      keywords='',
      author='Nathan Van Gheem',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      castlehps = castlehps:run
      """,
      )
