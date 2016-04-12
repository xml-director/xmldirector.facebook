# -*- coding: utf-8 -*-

################################################################
# xmldirector.facebook
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


import datetime 

from twython import Twython
from twython import TwythonError
from twython import TwythonAuthError

from zope.component import getUtility
from Products.Five.browser import BrowserView
from plone.registry.interfaces import IRegistry
from zope.annotation import IAnnotations

from xmldirector.facebook.interfaces import IFacebookSettings
from xmldirector.facebook.i18n import MessageFactory as _


TWITTER_TOKEN = 'xmldirector.facebook.token'
TWITTER_TOKEN_SECRET = 'xmldirector.facebook.token_secret'
TWITTER_DATA = 'xmldirector.facebook.data'
TWITTER_DATA_LAST_UPDATED = 'xmldirector.facebook.last_updated'


class FacebookAuthentication(BrowserView):

    def authorize(self, oauth_token):

        annotation = IAnnotations(self.context)
        settings = self.facebook_settings

        oauth_verifier = self.request['oauth_verifier']
        facebook = Twython(
                settings.facebook_app_key, 
                settings.facebook_app_secret,
                annotation[TWITTER_TOKEN],
                annotation[TWITTER_TOKEN_SECRET])
        final_step = facebook.get_authorized_tokens(oauth_verifier)
        annotation[TWITTER_TOKEN] = final_step['oauth_token']
        annotation[TWITTER_TOKEN_SECRET] = final_step['oauth_token_secret']
        self.context.plone_utils.addPortalMessage(_(u'Facebook access authorized'))
        self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')

    def deauthorize(self):
        """ Deauthorize Facebook access """
        annotation = IAnnotations(self.context)
        for key in (TWITTER_TOKEN, TWITTER_TOKEN_SECRET, TWITTER_DATA, TWITTER_DATA_LAST_UPDATED):
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
        return annotation.get(TWITTER_TOKEN)

    def get_oauth_url(self):

        settings = self.facebook_settings
        facebook = Twython(settings.facebook_app_key, settings.facebook_app_secret)
        callback_url = self.context.absolute_url() + '/authorize-facebook-action'
        auth = facebook.get_authentication_tokens(callback_url=callback_url)
        oauth_token = auth['oauth_token']
        oauth_token_secret = auth['oauth_token_secret']
        annotation = IAnnotations(self.context)
        annotation[TWITTER_TOKEN] = oauth_token
        annotation[TWITTER_TOKEN_SECRET] = oauth_token_secret
        return auth['auth_url']

    def post_to_facebook(self, text):

        facebook = self.facebook_session
        try:
            facebook.update_status(status=text)
            self.context.plone_utils.addPortalMessage(_(u'Post to Facebook successful'))
            self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook')
        except TwythonError as e:
            self.context.plone_utils.addPortalMessage(_(u'Post to Facebook failed - ' + str(e)), 'error')
            self.request.response.redirect(self.context.absolute_url() + '/authorize-facebook?text={}'.format(text))

