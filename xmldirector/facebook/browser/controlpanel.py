# -*- coding: utf-8 -*-


################################################################
# xmldirector.facebook
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

from plone.app.registry.browser import controlpanel

from xmldirector.facebook.interfaces import IFacebookSettings
from xmldirector.facebook.i18n import MessageFactory as _


class FacebookSettingsEditForm(controlpanel.RegistryEditForm):

    schema = IFacebookSettings
    label = _(u'XML Director - Facebook settings')
    description = _(u'')

    def updateFields(self):
        super(FacebookSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(FacebookSettingsEditForm, self).updateWidgets()


class FacebookSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = FacebookSettingsEditForm
