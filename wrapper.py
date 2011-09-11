#!/usr/bin/env python

import json
import urllib
import urllib2
import copy


class APIGateway:

    def __init__( self, access_token, client_id, client_secret ):

        #
        # access credentials
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret

        #
        # URL...
        scheme = 'https://'
        netloc = 'api.foursquare.com'
        path_prefix = '/v2'
        self.api_base_url = scheme + netloc + path_prefix 

    def query( self, path_suffix, get_params, userless ):

        #
        # Params sanitising -- erase any tokens and client creds...
        params = copy.copy( get_params )
        for fld in ['oauth_token','client_id','client_secret']:
            if fld in params:
                del params[fld]

        if userless:
            params['client_id'] = self.client_id
            params['client_secret'] = self.client_secret
        else:
            params['oauth_token'] = self.access_token

        path_suffix = path_suffix.lstrip( '/' )
        
        url = self.api_base_url + '/' + path_suffix + "?" + urllib.urlencode( params )

        try:
            response = urllib2.urlopen( url )
        except urllib2.HTTPError, e:
            raise e
        except urllib2.URLError, e:
            raise e
        
        raw_data = response.read()
        py_data = json.loads( raw_data )

        # Request error handling...
        response_code = int( py_data['meta']['code'] )
        if response_code != 200:
            error_type = py_data['meta']['errorType'][0]
            error_detail = py_data['meta']['errorDetail'][0]
            if error_type == 'rate_limit_exceeded':
                raise RateLimitExceededError( response_code, error_type, 
                    error_detail )
            
            raise FoursquareRequestError( response_code, error_type, 
                error_detail )
        
        #
        # Fin
        return py_data['response']

    def query_resource( self, resource_type, id, aspect=None, get_params={}, userless=False ):

        path_suffix = "/%s" % resource_type
        path_suffix += "/%s" % id
        if aspect:
            path_suffix += "/%s" % aspect
        
        return self.query( path_suffix, get_params, userless )

    def query_routine( self, resource_type, routine, get_params={}, userless=False ):

        path_suffix = "/%s" % resource_type
        path_suffix += "/%s" % routine
        
        return self.query( path_suffix, get_params, userless )

class FoursquareRequestError( RuntimeError ):
    def __init__( self, response_code, error_type, error_detail ):
        self.response_code = response_code
        self.error_type = error_type
        self.error_detail = error_detail 
        
    def __str__( self ):
        return "%s:%s" % ( self.response_code, self.error_type )


class RateLimitExceededError( FoursquareRequestError ):
    pass