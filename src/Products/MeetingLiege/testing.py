# -*- coding: utf-8 -*-
from plone.testing import z2, zca
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import FunctionalTesting
from Products.PloneMeeting.testing import PloneMeetingLayer
import Products.MeetingLiege


ML_ZCML = zca.ZCMLSandbox(filename="testing.zcml",
                          package=Products.MeetingLiege,
                          name='ML_ZCML')

ML_Z2 = z2.IntegrationTesting(bases=(z2.STARTUP, ML_ZCML),
                              name='ML_Z2')


class MeetingLiegeLayer(PloneMeetingLayer):
    """Setup our own layer so we can load overrides.zcml."""

    defaultBases = (PLONE_FIXTURE,)

    def setUpZCMLFiles(self):
        """ """
        super(MeetingLiegeLayer, self).setUpZCMLFiles()
        self.loadZCML('overrides.zcml', package=Products.MeetingLiege)


ML_TESTING_PROFILE = MeetingLiegeLayer(
    zcml_filename="testing.zcml",
    zcml_package=Products.MeetingLiege,
    additional_z2_products=('Products.MeetingLiege',
                            'Products.PloneMeeting',
                            'Products.CMFPlacefulWorkflow'),
    gs_profile_id='Products.MeetingLiege:testing',
    name="ML_TESTING_PROFILE")

ML_TESTING_PROFILE_FUNCTIONAL = FunctionalTesting(
    bases=(ML_TESTING_PROFILE,), name="ML_TESTING_PROFILE_FUNCTIONAL")
