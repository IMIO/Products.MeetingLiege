files="PloneMeeting plone imio.actionspanel imio.history datagridfield collective.eeafaceted.z3ctable"
languages="en fr"

for file in $files; do
    for language in $languages; do
        i18ndude sync --pot $file.pot $language/LC_MESSAGES/$file.po
        msgfmt -o $language/LC_MESSAGES/$file.mo $language/LC_MESSAGES/$file.po
    done
done
