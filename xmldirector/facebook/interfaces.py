# -*- coding: utf-8 -*-

################################################################
# xmldirector.facebook
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


from zope.interface import Interface
from zope import schema
from xmldirector.facebook.i18n import MessageFactory as _


class IBrowserLayer(Interface):
    """A brower layer specific to my product """


class IFacebookSettings(Interface):
    """ Facebook settings """

    facebook_app_key = schema.TextLine(
        title=_(u'Facebook client/app key'),
        required=True
    )

    facebook_app_secret = schema.TextLine(
        title=_(u'Facebook client/app secret'),
        required=True
    )
