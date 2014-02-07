from setuptools import setup, find_packages
import os

version = '3.2.0dev'

setup(name='Products.MeetingLiege',
      version=version,
      description="PloneMeeting profile for city of Liege",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
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
            test=['unittest2',
                  'zope.testing',
                  'plone.testing',
                  'plone.app.testing',
                  'communesplone.iconified_document_actions',
                  'Products.CMFPlacefulWorkflow',
                  'zope.testing',
                  'Products.MeetingCommunes',
                  'collective.ckeditor',
                  'plonetheme.imioapps'],
            templates=['Genshi',
                  ]),
      install_requires=[
          'setuptools',
          'appy',
          'Products.CMFPlone',
          'Pillow',
          'communesplone.iconified_document_actions',
          'Products.PloneMeeting',
          'collective.ckeditor',
          'plonetheme.imioapps'],
      entry_points={},
      )
