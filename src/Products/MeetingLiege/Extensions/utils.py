from AccessControl import Unauthorized

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
            groupId = pm.invokeFactory(type_name="MeetingGroup", id=elt, title=data[elt][0], description=data[elt][2], acronym=data[elt][1], givesMandatoryAdviceOn=data[elt][3])
            group = getattr(pm, groupId)
            group.processForm()
            out.append("MeetingGroup %s added" % elt)
        else:
            out.append("MeetingGroup %s already exists" % elt)
    return '\n'.join(out)

def import_meetingsGroups_from_csv(self, fname=None):
    """
      Import the MeetingGroups from the 'csv file' (fname received as parameter)
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
        file = open(fname,"rb")
        reader = csv.DictReader(file)
    except Exception, msg:
        file.close()
        return "Error with file : %s"%msg.value

    out = []
 
    pm = self.portal_plonemeeting
    from Products.CMFPlone.utils import normalizeString

    for row in reader:
        row_id = normalizeString(row['title'],self)
        if not hasattr(pm, row_id):
            deleg = row['delegation'].replace('#','\n')
            groupId = pm.invokeFactory(type_name="MeetingGroup", id=row_id, title=row['title'], description=row['description'], acronym=row['acronym'], givesMandatoryAdviceOn=row['givesMandatoryAdviceOn'], signatures=deleg)
            group = getattr(pm, groupId)
            group.processForm()
            out.append("MeetingGroup %s added" % row_id)
        else:
            out.append("MeetingGroup %s already exists" % row_id)

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
        file = open(fname,"rb")
        reader = csv.DictReader(file)
    except Exception, msg:
        file.close()
        return "Error with file : %s"%msg.value

    out = []
 
    from Products.CMFPlone.utils import normalizeString

    acl = self.acl_users
    pms = self.portal_membership
    pgr = self.portal_groups
    for row in reader:
        row_id = normalizeString(row['username'],self)
        #add users if not exist
        if row_id not in [ud['userid'] for ud in acl.searchUsers()]:
            newuser = pms.addMember(row_id, row['password'], ('Member',), [])
            member = pms.getMemberById(row_id)
            member.setMemberProperties({'fullname': row['fullname'], 'email': row['email'], 'description': row['biography']}) 
            out.append("User '%s' is added"%row_id)
        else:
            out.append("User %s already exists" % row_id)
        #attribute roles
        grouptitle =  normalizeString(row['grouptitle'],self)
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
            out.append("    -> Added in group '%s'"%groupid)

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
        file = open(fname,"rb")
        reader = csv.DictReader(file)
    except Exception, msg:
        file.close()
        return "Error with file : %s"%msg.value

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
        row_id = normalizeString(row['title'],self)
        if row_id == '':
            continue      
        if not hasattr(catFolder, row_id):
            try:
                catDescr  = CategoryDescriptor(row_id, title=row['title'], description=row['description'], active=row['actif'])
                meetingConfig.addCategory(catDescr, classifier = isClassifier)

                cat = getattr(catFolder,row_id, None)
                if cat :
                    cat.setCategoryId(row['categoryId'])
                    groupId = normalizeString(row['service'], self)
                    if getattr(pm, groupId, None):
                        cat.setUsingGroups((groupId,))
                    elif groupId:
                        out.append("Restricted group %s not found" % groupId)
                out.append("Category (or Classifier) %s added" % row_id)
            except Exception, message:
                out.append('error with %s - %s : %s'%(row_id,row['title'],message))
        else:
            out.append("Category (or Classifier) %s already exists" % row_id)

    file.close()

    return '\n'.join(out)

def importRefArchive(self, meeting_config='', fname=None):
    """
      Create a dico with csv file and import the refArchive file (fname received as parameter)
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
        file = open(fname,"rb")
        reader = csv.DictReader(file)
    except Exception, msg:
        file.close()
        return "Error with file : %s"%msg.value

    out = []
    refA_lst = []

    pm = self.portal_plonemeeting
    meetingConfig = getattr(pm, meeting_config, None)
    from Products.CMFPlone.utils import normalizeString

    for row in reader:
        row_id = normalizeString(row['label'],self)
        if row_id == '':
            continue
        refA_dico = {}
        refA_dico['row_id'] = row_id
        refA_dico['code'] = row['code']
        refA_dico['label'] = row['label']
        if row['active']:
            actif = '1'
        else:
            actif = '0'
        refA_dico['active'] = actif
        refA_dico['finance_advice'] = normalizeString(row['finance_advice'])
        groupId = _getProposingGroupsBaseOnAcronym(pm, row['acronym'])
        if groupId:
            refA_dico['restrict_to_groups'] = groupId
        else:
            refA_dico['restrict_to_groups'] = []
            out.append("Restricted group not found for this acronym %s" % row['acronym'])
        refA_lst.append(refA_dico)
    meetingConfig.setArchivingRefs(refA_lst)
    file.close()

    return '\n'.join(out)

def _getProposingGroupsBaseOnAcronym(pm, acronym):
    """
      return all proposing groups with this acronym
    """
    res = []

    if not acronym:
        return res

    groups = pm.getMeetingGroups(onlyActive = False)
    for group in groups:
        if group.getAcronym() == acronym:
            res.append(group.id)

    return res
