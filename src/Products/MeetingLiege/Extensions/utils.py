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
        if row['observers']:
            groups.append(grouptitle + '_observers')
        if row['creators']:
            groups.append(grouptitle + '_creators')
        if row['reviewers']:
            groups.append(grouptitle + '_reviewers')
        if row['advisers']:
            groups.append(grouptitle + '_advisers')
        if row['administrativereviewers']:
            groups.append(grouptitle + '_administrativereviewers')
        if row['internatlreviewers']:
            groups.append(grouptitle + '_internatlreviewers')                        
        for groupid in groups:
            pgr.addPrincipalToGroup(row_id, groupid)
            out.append("    -> Added in group '%s'"%groupid)

    file.close()

    return '\n'.join(out)

def import_meetingsCategories_from_csv(self, meeting_config = '', isClassifier=False, fname=None):
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

    meetingConfig = getattr(pm, meeting_config)
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

                cat = getattr(catFolder,row_id)
                if cat :
                    cat.setCategoryId(row['categoryId'])
                out.append("Category (or Classifier) %s added" % row_id)
            except Exception, message:
                out.append('error with %s - %s : %s'%(row_id,row['title'],message))
        else:
            out.append("Category (or Classifier) %s already exists" % row_id)

    file.close()

    return '\n'.join(out)    
