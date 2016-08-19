# -*- coding: utf-8 -*-

################################################################
# xmldirector.facebook
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import requests
import furl
import datetime 

import facebook


from zope.component import getUtility
from zope.interface import alsoProvides
from zope.annotation import IAnnotations
from Products.Five.browser import BrowserView
from plone.registry.interfaces import IRegistry
from plone.protect.interfaces import IDisableCSRFProtection
from plone.protect.interfaces import IDisableCSRFProtection

from xmldirector.facebook.interfaces import IFacebookSettings
from xmldirector.facebook.i18n import MessageFactory as _


FB_ACCESS_TOKEN = 'xmldirector.facebook.token'
FB_LAST_UPDATED = 'xmldirector.facebook.last_update'


class FacebookAuthentication(BrowserView):

    def __init__(self, context, request):
        # fuck all Plone protection shit!
        alsoProvides(request, IDisableCSRFProtection)
        super(FacebookAuthentication, self).__init__(context, request)

    def get_oauth_url(self):

        settings = self.facebook_settings
        redirect_uri = '{}/authorize-facebook-action/'.format(self.context.absolute_url())
        fb_url = 'https://www.facebook.com/dialog/oauth'
        data = dict(
           client_id=settings.facebook_app_key,
           redirect_uri=redirect_uri,
           scope='publish_pages,email,publish_actions',
        )
        f = furl.furl(fb_url)
        f.args = data
        return str(f)

    def get_oauth_token(self):
        annotation = IAnnotations(self.context)
        return annotation.get(FB_ACCESS_TOKEN)

    def authorize(self, code=None):
        """ Exchange code against access_token """
        settings = self.facebook_settings
        annotation = IAnnotations(self.context)
        redirect_uri = '{}/authorize-facebook-action/'.format(self.context.absolute_url())
        fb_url = 'https://graph.facebook.com/v2.3/oauth/access_token'
        data = dict(
           code=code,
           client_id=settings.facebook_app_key,
           client_secret=settings.facebook_app_secret,
           redirect_uri=redirect_uri,
           response_type='code token'
        )
        result = requests.get(fb_url, params=data)
        if result.status_code != 200:
            raise RuntimeError('Phase 2 authentication with Facebook failed')
        credentials = result.json()
        annotation[FB_ACCESS_TOKEN] = credentials['access_token']
        annotation[FB_LAST_UPDATED] = datetime.datetime.utcnow() 
        self.context.plone_utils.addPortalMessage(_(u'Facebook access authorized'))
        self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')

    def deauthorize(self):
        """ Deauthorize Facebook access """
        alsoProvides(self.request, IDisableCSRFProtection)
        annotation = IAnnotations(self.context)
        for key in (FB_ACCESS_TOKEN, FB_LAST_UPDATED):
            try:
                del annotation[key]
            except KeyError:
                pass
        self.context.plone_utils.addPortalMessage(_(u'Facebook access deauthorized'))
        self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')

    @property
    def facebook_settings(self):
        registry = getUtility(IRegistry)
        return registry.forInterface(IFacebookSettings)

    def post_to_facebook(self, text):
        graph = facebook.GraphAPI(self.get_oauth_token())
        profile = graph.get_object("me")
        graph.put_object(parent_object="me", connection_name="feed", message=text)
        self.context.plone_utils.addPortalMessage(_(u'Post to Facebook successful'))
        self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')
