# -*- coding: utf-8 -*-

################################################################
# xmldirector.facebook
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import furl
import string
import datetime 
import urlparse
import random

from twython import Twython
from twython import TwythonError
from twython import TwythonAuthError

from zope.component import getUtility
from Products.Five.browser import BrowserView
from plone.registry.interfaces import IRegistry
from zope.annotation import IAnnotations

from xmldirector.facebook.interfaces import IFacebookSettings
from xmldirector.facebook.i18n import MessageFactory as _


FB_ACCESS_TOKEN = 'xmldirector.facebook.token'
FB_LAST_UPDATED = 'xmldirector.facebook.last_update'


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class FacebookAuthentication(BrowserView):

    def authorize(self):
        """ Authorize Facebook access """
        annotation = IAnnotations(self.context)
        annotation[FB_ACCESS_TOKEN] = self.request['#access_token']
        self.context.plone_utils.addPortalMessage(_(u'Facebook access authorized'))
        self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')

    def authorize2(self):
        qs = self.request['qs']
        parts = urlparse.parse_qs(qs)
        access_token = parts['access_token'][0]
        annotation = IAnnotations(self.context)
        annotation[FB_ACCESS_TOKEN] = access_token
        annotation[FB_LAST_UPDATED] = datetime.datetime.utcnow()
        self.context.plone_utils.addPortalMessage(_(u'Facebook access authorized'))
        self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')

    def deauthorize(self):
        """ Deauthorize Facebook access """
        annotation = IAnnotations(self.context)
        for key in (FB_ACCESS_TOKEN, FB_LAST_UPDATED):
            try:
                del annotation[key]
            except KeyError:
                pass
        self.context.plone_utils.addPortalMessage(_(u'Facebook access deauthorized'))
        self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')

    def facebook_info(self, force=False):
        """ Return Facebook information associated with the current token """

        annotation = IAnnotations(self.context)
        data = annotation.get(TWITTER_DATA)
        if data and not force:
            last_accessed = annotation[TWITTER_DATA_LAST_UPDATED]
            if (datetime.datetime.utcnow() - last_accessed).seconds < 15 * 60: # 15 minutes
                return data

        session = self.facebook_session
        try:
            data = session.verify_credentials()
        except TwythonAuthError:
            data = None

        annotation[TWITTER_DATA] = data
        annotation[TWITTER_DATA_LAST_UPDATED] = datetime.datetime.utcnow()
        return data

    @property
    def facebook_settings(self):
        registry = getUtility(IRegistry)
        return registry.forInterface(IFacebookSettings)

    @property
    def facebook_session(self):
        settings = self.facebook_settings
        annotation = IAnnotations(self.context)
        return Twython(
                settings.facebook_app_key, 
                settings.facebook_app_secret, 
                annotation[TWITTER_TOKEN],
                annotation[TWITTER_TOKEN_SECRET])

    def get_oauth_token(self):
        annotation = IAnnotations(self.context)
        return annotation.get(FB_ACCESS_TOKEN)

    def get_oauth_url(self):

        settings = self.facebook_settings
        redirect_uri = '{}/authorize-facebook-action/'.format(self.context.absolute_url())
        fb_url = 'https://graph.facebook.com/oauth/authorize'
        data = dict(
           type='user_agent',
           client_id=settings.facebook_app_key,
           redirect_uri=redirect_uri,
           scope='publish_pages,email',
           response_type='code',
           state=id_generator(128)
        )
        f = furl.furl(fb_url)
        f.args = data
        return str(f)

    def post_to_facebook(self, text):

        facebook = self.facebook_session
        try:
            facebook.update_status(status=text)
            self.context.plone_utils.addPortalMessage(_(u'Post to Facebook successful'))
            self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')
        except TwythonError as e:
            self.context.plone_utils.addPortalMessage(_(u'Post to Facebook failed - ' + str(e)), 'error')
            self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook?text={}'.format(text))

