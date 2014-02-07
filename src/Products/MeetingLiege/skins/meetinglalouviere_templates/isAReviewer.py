## Script (Python) "isAReviewer"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Check if current user is a reviewer, aka able to validate one of the validation steps
##

member = context.portal_membership.getAuthenticatedMember()
groups = context.portal_groups.getGroupsForPrincipal(member)

#check if the user is at least in one of the following sub group

reviewSuffixes = ('_reviewers', '_directors', '_divisionheads', '_officemanagers', '_serviceheads', )

strgroups = str(groups)

isReviewer = False
for reviewSuffix in reviewSuffixes:
    if reviewSuffix in strgroups:
        isReviewer = True
        break
return isReviewer

