from setuptools import setup, find_packages

setup(name='pyalice',
      version='0.2.3',
      description='Yandex.Dialogs non-official package.',
      long_description='Processing requests and sending responses for Yandex.Dialogs API.',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='yandex dialogs alice skills',
      url='https://github.com/Jornau/alice',
      author='Alexander Surkov',
      author_email='jornau@yandex.ru',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'requests',
          'pytz',
          'datedelta'
      ],
      zip_safe=False)