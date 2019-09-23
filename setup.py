from setuptools import setup, find_packages
import os

version = '4.1rc4.dev0'

setup(
    name='Products.MeetingLiege',
    version=version,
    description="PloneMeeting profile for city of Liege",
    long_description=open("README.rst").read() + "\n" +
    open("CHANGES.rst").read(),
    classifiers=[
        "Programming Language :: Python",
        ],
    keywords='',
    author='',
    author_email='',
    url='http://www.imio.be/produits/gestion-des-deliberations',
    license='GPL',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=['Products.PloneMeeting[test]'],
        templates=['Genshi']),
    install_requires=[
        'setuptools',
        'appy',
        'Products.CMFPlone',
        'Pillow',
        'Products.PloneMeeting'],
    entry_points={},
    )
