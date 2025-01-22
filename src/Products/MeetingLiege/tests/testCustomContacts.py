# -*- coding: utf-8 -*-

from collective.contact.plonegroup.utils import get_plone_groups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomContacts(MeetingLiegeTestCase):
    ''' '''

    def test_ExtraSuffixesForFinanceOrgs(self):
        """Finances related organizations get extra suffixes."""
        self.changeUser('admin')
        self._createFinanceGroups()
        vendorsPloneGroupIds = get_plone_groups(self.vendors_uid, ids_only=True)
        vendorsPloneGroupIds.sort()
        self.assertEqual(vendorsPloneGroupIds,
                         ['{0}_administrativereviewers'.format(self.vendors_uid),
                          '{0}_advisers'.format(self.vendors_uid),
                          '{0}_creators'.format(self.vendors_uid),
                          '{0}_incopy'.format(self.vendors_uid),
                          '{0}_internalreviewers'.format(self.vendors_uid),
                          '{0}_observers'.format(self.vendors_uid),
                          '{0}_prereviewers'.format(self.vendors_uid),
                          '{0}_reviewers'.format(self.vendors_uid)])
        financial_group_uids = self.tool.finance_group_uids()
        financeGroupUID = financial_group_uids[0]
        financePloneGroupIds = get_plone_groups(financeGroupUID, ids_only=True)
        financePloneGroupIds.sort()
        self.assertEqual(financePloneGroupIds,
                         ['{0}_administrativereviewers'.format(financeGroupUID),
                          '{0}_advisers'.format(financeGroupUID),
                          '{0}_creators'.format(financeGroupUID),
                          '{0}_financialcontrollers'.format(financeGroupUID),
                          '{0}_financialmanagers'.format(financeGroupUID),
                          '{0}_financialreviewers'.format(financeGroupUID),
                          '{0}_incopy'.format(financeGroupUID),
                          '{0}_internalreviewers'.format(financeGroupUID),
                          '{0}_observers'.format(financeGroupUID),
                          '{0}_prereviewers'.format(financeGroupUID),
                          '{0}_reviewers'.format(financeGroupUID)])
