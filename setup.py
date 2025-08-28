from setuptools import find_packages
from setuptools import setup

version = '4.2.14'

setup(
    name='Products.MeetingLiege',
    version=version,
    description="PloneMeeting profile for city of Liege",
    long_description=open("README.rst").read() + "\n" +
    open("CHANGES.rst").read(),
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Office/Business",
    ],
    keywords='plone official meetings management egov communesplone imio plonegov',
    author='Gauthier Bastien',
    author_email='gauthier@imio.be',
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
