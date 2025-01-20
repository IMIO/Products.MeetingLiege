from AccessControl import Unauthorized
from Acquisition import aq_base
from plone import api
from plone.i18n.normalizer.interfaces import IFileNameNormalizer
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import os


def export_meetinggroups(self):
    """
      Export the existing MeetingGroups informations as a dictionnary
    """
    member = self.portal_membership.getAuthenticatedMember()
    if not member.has_role('Manager'):
        raise Unauthorized, 'You must be a Manager to access this script !'

    if not hasattr(self, 'portal_plonemeeting'):
        return "PloneMeeting must be installed to run this script !"

    pm = self.portal_plonemeeting

    dict = {}
    for mgr in pm.objectValues('MeetingGroup'):
        dict[mgr.getId()] = (mgr.Title(), mgr.Description(), mgr.getAcronym(), mgr.getGivesMandatoryAdviceOn())
    return dict


def export_allItemTemplates(self, context=''):
    member = self.portal_membership.getAuthenticatedMember()
    if not member.has_role('Manager'):
        raise Unauthorized, 'You must be a Manager to access this script !'

    if not hasattr(self, 'portal_plonemeeting'):
        return "PloneMeeting must be installed to run this script !"

    tool = getToolByName(self, 'portal_plonemeeting')
    meetingConfig = tool.getMeetingConfig(self)
    podTemplatesFolder = getattr(meetingConfig, 'podtemplates')
    template = getattr(podTemplatesFolder, 'catalogue-actes')
    normalizer = getUtility(IFileNameNormalizer)

    if context == '':
        context = self
    for itemId in context:
        item = getattr(context, itemId)
        trueItem = item
        portalType = item.getPortalTypeName()

        if portalType == 'Folder':
            itemTitle = item.Title()
            itemTitle = itemTitle.replace('.', '')
            itemTitle = itemTitle.replace('/', '-')
            constructedPath = '/{0}'.format(itemTitle)
        elif portalType in ('MeetingItemTemplateCouncil', 'MeetingItemTemplateCollege'):
            constructedPath = ''

        while item.getParentNode().getId() != 'itemtemplates':
            item = item.getParentNode()
            itemTitle = item.Title()
            itemTitle = itemTitle.replace('.', '')
            itemTitle = itemTitle.replace('/', '-')
            constructedPath = '/{0}{1}'.format(itemTitle, constructedPath)
        path = '/tmp/export{0}'.format(constructedPath)

        if 'export' not in os.listdir('/tmp'):
            os.mkdir('/tmp/export')
        if portalType == 'Folder':
            os.mkdir(path)
            export_allItemTemplates(self, context=trueItem)
        elif portalType in ('MeetingItemTemplateCouncil', 'MeetingItemTemplateCollege'):
            fileId = trueItem.Title()
            fileId = fileId[:124]
            fileId = fileId.replace('/', '-')
            fileId = fileId.replace('.', '')
            fileId = fileId + '.pdf'
            res = template.generateDocument(trueItem, forBrowser=False)
            os.chdir(path)
            f = open(fileId, 'w')
            f.write(res)
            f.close()


def import_meetinggroups(self, dict=None):
    """
      Import the MeetingGroups from the 'dict' dictionnaty received as parameter
    """
    member = self.portal_membership.getAuthenticatedMember()
    if not member.has_role('Manager'):
        raise Unauthorized, 'You must be a Manager to access this script !'

    if not dict:
        return "This script needs a 'dict' parameter"
    if not hasattr(self, 'portal_plonemeeting'):
        return "PloneMeeting must be installed to run this script !"

    pm = self.portal_plonemeeting
    out = []
    data = eval(dict)
    for elt in data:
        if not hasattr(pm, elt):
            groupId = pm.invokeFactory(type_name="MeetingGroup", id=elt, title=data[elt][0], description=data[elt][2],
                                       acronym=data[elt][1], givesMandatoryAdviceOn=data[elt][3])
            group = getattr(pm, groupId)
            group.processForm()
            out.append("MeetingGroup %s added" % elt)
        else:
            out.append("MeetingGroup %s already exists" % elt)
    return '\n'.join(out)


def import_meetingsGroups_from_csv(self, fname=None):
    """
      Import the MeetingGroups from the 'csv file' (fname received as parameter)
      If Meeting group exists, update Acronym and description
    """
    member = self.portal_membership.getAuthenticatedMember()
    if not member.has_role('Manager'):
        raise Unauthorized, 'You must be a Manager to access this script !'

    if not fname:
        return "This script needs a 'fname' parameter"
    if not hasattr(self, 'portal_plonemeeting'):
        return "PloneMeeting must be installed to run this script !"

    import csv
    try:
        file = open(fname, "rb")
        reader = csv.DictReader(file)
    except Exception, msg:
        file.close()
        return "Error with file : %s" % msg.value

    out = []

    pm = self.portal_plonemeeting
    from Products.CMFPlone.utils import normalizeString

    for row in reader:
        row_id = normalizeString(row['title'], self)
        if not hasattr(pm, row_id):
            deleg = row['delegation'].replace('#', '\n')
            groupId = pm.invokeFactory(type_name="MeetingGroup", id=row_id,
                                       title=row['title'], description=row['description'],
                                       acronym=row['acronym'], givesMandatoryAdviceOn=row['givesMandatoryAdviceOn'],
                                       signatures=deleg)
            group = getattr(pm, groupId)
            group.processForm()
            out.append("MeetingGroup %s added" % row_id)
        else:
            group = getattr(pm, row_id)
            group.setDescription(row['description'])
            group.setAcronym(row['acronym'])
            group.processForm()
            out.append("MeetingGroup %s already exists - update description and acronym" % row_id)

    file.close()

    return '\n'.join(out)


def import_meetingsUsersAndRoles_from_csv(self, fname=None):
    """
      Import the users and attribute roles from the 'csv file' (fname received as parameter)
    """

    member = self.portal_membership.getAuthenticatedMember()
    if not member.has_role('Manager'):
        raise Unauthorized, 'You must be a Manager to access this script !'

    if not fname:
        return "This script needs a 'fname' parameter"
    if not hasattr(self, 'portal_plonemeeting'):
        return "PloneMeeting must be installed to run this script !"

    import csv
    try:
        file = open(fname, "rb")
        reader = csv.DictReader(file)
    except Exception, msg:
        file.close()
        return "Error with file : %s" % msg.value

    out = []

    from Products.CMFPlone.utils import normalizeString

    acl = self.acl_users
    pms = self.portal_membership
    pgr = self.portal_groups
    for row in reader:
        row_id = normalizeString(row['username'], self)
        #add users if not exist
        if row_id not in [ud['userid'] for ud in acl.searchUsers()]:
            pms.addMember(row_id, row['password'], ('Member',), [])
            member = pms.getMemberById(row_id)
            member.setMemberProperties({'fullname': row['fullname'], 'email': row['email'],
                                        'description': row['biography']})
            out.append("User '%s' is added" % row_id)
        else:
            out.append("User %s already exists" % row_id)
        #attribute roles
        grouptitle = normalizeString(row['grouptitle'], self)
        groups = []
        if row.has_key('observers') and row['observers']:
            groups.append(grouptitle + '_observers')
        if row.has_key('creators') and row['creators']:
            groups.append(grouptitle + '_creators')
        if row.has_key('reviewers') and row['reviewers']:
            groups.append(grouptitle + '_reviewers')
        if row.has_key('advisers') and row['advisers']:
            groups.append(grouptitle + '_advisers')
        if row.has_key('administrativereviewers') and row['administrativereviewers']:
            groups.append(grouptitle + '_administrativereviewers')
        if row.has_key('internatlreviewers') and row['internatlreviewers']:
            groups.append(grouptitle + '_internatlreviewers')
        if row.has_key('controleur') and row['controleur']:
            groups.append(grouptitle + '_financialcontrollers')
        if row.has_key('dfvalidator') and row['dfvalidator']:
            groups.append(grouptitle + '_financialreviewers')
        if row.has_key('dfdirector') and row['dfdirector']:
            groups.append(grouptitle + '_financialmanagers')
        for groupid in groups:
            pgr.addPrincipalToGroup(row_id, groupid)
            out.append("    -> Added in group '%s'" % groupid)

    file.close()

    return '\n'.join(out)


def import_meetingsCategories_from_csv(self, meeting_config='', isClassifier=False, fname=None):
    """
      Import the MeetingCategories from the 'csv file' (meeting_config, isClassifier and fname received as parameter)
    """
    member = self.portal_membership.getAuthenticatedMember()
    if not member.has_role('Manager'):
        raise Unauthorized, 'You must be a Manager to access this script !'

    if not fname or not meeting_config:
        return "This script needs a 'meeting_config' and 'fname' parameters"
    if not hasattr(self, 'portal_plonemeeting'):
        return "PloneMeeting must be installed to run this script !"

    import csv
    try:
        file = open(fname, "rb")
        reader = csv.DictReader(file)
    except Exception, msg:
        file.close()
        return "Error with file : %s" % msg.value

    out = []

    pm = self.portal_plonemeeting
    from Products.CMFPlone.utils import normalizeString
    from Products.PloneMeeting.profiles import CategoryDescriptor

    meetingConfig = getattr(pm, meeting_config, None)
    if isClassifier:
        catFolder = meetingConfig.classifiers
    else:
        catFolder = meetingConfig.categories

    for row in reader:
        row_id = normalizeString(row['title'], self)
        if row_id == '':
            continue
        try:
            cat = getattr(aq_base(catFolder), row_id, None)
            if not cat:
                catDescr = CategoryDescriptor(row_id, title=row['title'], description=row['description'],
                                              active=row['actif'])
                cat = meetingConfig.addCategory(catDescr, classifier=isClassifier)
                out.append("Category (or Classifier) %s added" % row_id)
            else:  # cat exist, update description and active fields
                cat.setDescription(row['description'])
                state = self.portal_workflow.getInfoFor(cat, 'review_state')
                if not row['actif'] and state == 'active':
                    self.portal_workflow.doActionFor(cat, 'deactivate')
                elif row['actif'] and state != 'active':
                    self.portal_workflow.doActionFor(cat, 'activate')
                out.append("Category (or Classifier) %s updated" % row_id)
            # update other field
            cat.setCategoryId(row['categoryId'])
            groupIds = _getProposingGroupsBaseOnAcronym(pm, row['acronym'])
            if groupIds:
                cat.setUsingGroups(groupIds)
            else:
                cat.setUsingGroups([])
                if row['acronym']:
                    out.append("Acronym not found : %s " % row['acronym'])
            if row['link']:
                row_link = normalizeString(row['link'], self)
                otherCat = 'meeting-config-council.%s' % row_link
                cat.setCategoryMappingsWhenCloningToOtherMC((otherCat,))
            if row['new-title']:
                cat.setTitle(row['new-title'])
        except Exception, message:
            out.append('error with %s - %s : %s' % (row_id, row['title'], message))

    file.close()

    return '\n'.join(out)


def _getProposingGroupsBaseOnAcronym(pm, acronyms):
    """
      return all proposing groups with this acronym
    """
    res = []

    if not acronyms:
        return res

    for acronym in acronyms.split(','):
        groups = pm.getMeetingGroups(onlyActive=False)
        for group in groups:
            if group.getAcronym().startswith(acronym.strip()):
                res.append(group.id)

    return res

def swapUsersNameAndFirstname(self, isTest = True):
    member = self.portal_membership.getAuthenticatedMember()
    out = []
    test = {}
    if not member.has_role('Manager'):
        raise Unauthorized, 'You must be a Manager to access this script !'

    users = api.user.get_users()
    for user in users:
        fullname = user.getProperty('fullname')
        splitName = fullname.split()
        correctedName = ''
        upperName = ''
        if len(splitName) == 2:
            correctedName = splitName[1] + " " + splitName[0]
            if not isTest:
                user.setMemberProperties({'fullname': correctedName})
            else:
                test[fullname] = correctedName
        elif len(splitName) > 2:
            for part in splitName:
                if part.isupper() and part != '(ADMIN)':
                    if upperName:
                        upperName = upperName + " " + part
                    else:
                        upperName = part
                else:
                    if correctedName:
                        correctedName = correctedName + " " + part
                    else:
                        correctedName = part
            if not upperName:
                out.append(fullname)
            else:
                correctedName = upperName + " " + correctedName
                if not isTest:
                    user.setMemberProperties({'fullname': correctedName})
                else:
                    test[fullname] = correctedName
        else:
            out.append(fullname)
    if not isTest:
        return '\n'.join(out)
    else:
        return '\n'.join(test)
