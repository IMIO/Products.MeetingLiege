# -*- coding: utf-8 -*-

from plone.memoize import forever
from Products.MeetingLiege.config import BOURGMESTRE_GROUP_ID
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import GENERAL_MANAGER_GROUP_ID
from Products.MeetingLiege.config import TREASURY_GROUP_ID
from Products.PloneMeeting.utils import org_id_to_uid


@forever.memoize
def bg_group_uid(raise_on_error=False):
    """ """
    return org_id_to_uid(BOURGMESTRE_GROUP_ID, raise_on_error=raise_on_error)


@forever.memoize
def gm_group_uid(raise_on_error=False):
    """ """
    return org_id_to_uid(GENERAL_MANAGER_GROUP_ID, raise_on_error=raise_on_error)


@forever.memoize
def treasury_group_cec_uid(raise_on_error=False):
    """ """
    return org_id_to_uid(TREASURY_GROUP_ID, raise_on_error=raise_on_error)


@forever.memoize
def finance_group_uids(raise_on_error=False):
    """ """
    return [org_id_to_uid(fin_grp_id, raise_on_error=raise_on_error)
            for fin_grp_id in FINANCE_GROUP_IDS]