# Import Built-Ins
import logging
import unittest
from unittest import TestCase, mock
import time
import warnings
import json
import os
import hmac
import hashlib
import base64
import urllib

# Import Third-Party
import requests
import jwt


# Import Homebrew
from bitex.api.base import BaseAPI
from bitex.api.REST import RESTAPI
from bitex.api.REST import BitstampREST, BitfinexREST, BittrexREST
from bitex.api.REST import HitBTCREST, CCEXREST, CoincheckREST, CryptopiaREST
from bitex.api.REST import ITbitREST, GDAXREST, GeminiREST,  KrakenREST, OKCoinREST
from bitex.api.REST import PoloniexREST, QuoineREST, QuadrigaCXREST, RockTradingREST
from bitex.api.REST import VaultoroREST
from bitex.exceptions import IncompleteCredentialsWarning
from bitex.exceptions import IncompleteCredentialsError
from bitex.exceptions import IncompleteAPIConfigurationWarning
from bitex.exceptions import IncompleteCredentialConfigurationWarning

# Init Logging Facilities
log = logging.getLogger(__name__)

try:
    tests_folder_dir = os.environ['TRAVIS_BUILD_DIR'] + '/tests/'
except KeyError:
    tests_folder_dir = os.path.split(os.path.realpath(__file__))[0]


class BitstampRESTTests(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = BitstampREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://www.bitstamp.net/api')
        self.assertEqual(api.version, 'v2')
        self.assertIs(api.config_file, None)
        # Assert that a Warning is raised if user_id is None, and BaseAPI's
        # check mechanism is extended properly
        api = BitstampREST(addr='Bangarang', user_id=None, key='SomeKey', secret='SomeSecret',
                           config=None, version=None)
        with mock.patch('warnings.warn') as mock_warn:
            api.load_config('%s/configs/config.ini' % tests_folder_dir)
            mock_warn.assert_called_with("'user_id' not found in config!",
                                         IncompleteCredentialConfigurationWarning)

        # make sure an exception is raised if user_id is passed as ''
        with self.assertRaises(ValueError):
            BitstampREST(addr='Bangarang', user_id='', key='SomeKey', secret='SomeSecret',
                         config=None, version=None)

        # make sure user_id is assigned properly
        api = BitstampREST(addr='Bangarang', user_id='woloho')
        self.assertEqual(api.user_id, 'woloho')

        # Check that a IncompleteCredentialConfigurationWarning is issued if
        # user_id isn't available in config, and no user_id was given.
        with self.assertWarns(IncompleteCredentialConfigurationWarning):
            api = BitstampREST(addr='Bangarang', user_id=None,
                               config='%s/configs/config.ini' %
                               tests_folder_dir)

        # check that user_id is loaded correctly, and no
        # IncompleteCredentialsWarning is issued, if we dont pass a user_id
        # kwarg but it is avaialable in the config file
        config_path = '%s/auth/bitstamp.ini' % tests_folder_dir
        with self.assertRaises(AssertionError):
            with self.assertWarns(IncompleteCredentialConfigurationWarning):
                api = BitstampREST(config=config_path)
        self.assertTrue(api.config_file == config_path)
        self.assertEqual(api.user_id, '267705')

    def test_check_auth_requirements_fires_as_expected_on_empty_user_id(self):
        # config.ini is missing the key 'user_id' and hence should raise
        # an error on checking for authentication credentials when calling check_auth_requirements()
        config_path = '%s/configs/config.ini' % tests_folder_dir
        api = BitstampREST(config=config_path)
        with self.assertRaises(IncompleteCredentialsError):
            api.check_auth_requirements()

    def test_sign_request_kwargs_method_and_signature(self):
        """Test signature generation.


        Example as seen on https://www.bitstamp.net/api/
        ```
        import hmac
        import hashlib

        message = nonce + customer_id + api_key
        signature = hmac.new(API_SECRET, msg=message, digestmod=hashlib.sha256).hexdigest().upper()
        ```
        """
        # Test that the sign_request_kwargs generate appropriate kwargs:

        # Check signatured request kwargs
        key, secret, user = 'panda', 'shadow', 'leeroy'
        with mock.patch.object(RESTAPI, 'nonce', return_value=str(10000)) as mock_rest:
            api = BitstampREST(key=key, secret=secret, user_id=user)
            ret_values = api.sign_request_kwargs('testing/signature', param_1='a', param_2=1)
            expected_signature = hmac.new(secret.encode('utf-8'),
                                          (str(10000) + user + key).encode('utf-8'),
                                          hashlib.sha256).hexdigest().upper()
            self.assertIn('key', ret_values['data'])
            self.assertEqual(ret_values['data']['key'], key)
            self.assertIn('signature', ret_values['data'])
            self.assertEqual(ret_values['data']['signature'], expected_signature)
            self.assertIn('nonce', ret_values['data'])
            self.assertEqual(ret_values['data']['nonce'], str(10000))


class BitfinexRESTTests(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = BitfinexREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.bitfinex.com')
        self.assertEqual(api.version, 'v1')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'

        """
        Test API Version 1 Signature
        """
        with mock.patch.object(RESTAPI, 'nonce', return_value=str(100)):
            api = BitfinexREST(key=key, secret=secret)
            self.assertEqual(api.nonce(), str(100))
            self.assertEqual(api.version, 'v1')
            self.assertEqual(api.generate_uri('testing/signature'), '/v1/testing/signature')
            ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'})
            possible_json_dumps = ['{"param_1": "abc", "nonce": "100", "request": "/v1/testing/signature"}',
                                   '{"param_1": "abc", "request": "/v1/testing/signature", "nonce": "100"}',
                                   '{"nonce": "100", "param_1": "abc", "request": "/v1/testing/signature"}',
                                   '{"nonce": "100", "request": "/v1/testing/signature", "param_1": "abc"}',
                                   '{"request": "/v1/testing/signature", "param_1": "abc", "nonce": "100"}',
                                   '{"request": "/v1/testing/signature", "nonce": "100", "param_1": "abc"}']
            data = [base64.standard_b64encode(pl.encode('utf8'))
                    for pl in possible_json_dumps]
            signatures = [hmac.new(secret.encode('utf-8'), d, hashlib.sha384).hexdigest()
                          for d in data]

            self.assertIn('X-BFX-APIKEY', ret_values['headers'])
            self.assertEqual(ret_values['headers']['X-BFX-APIKEY'], key)
            self.assertIn('X-BFX-PAYLOAD', ret_values['headers'])
            self.assertIn(ret_values['headers']['X-BFX-PAYLOAD'], data)
            self.assertIn('X-BFX-SIGNATURE', ret_values['headers'])
            self.assertIn(ret_values['headers']['X-BFX-SIGNATURE'], signatures)

        """
        Test API Version 2 Signature
        """
        with mock.patch.object(RESTAPI, 'nonce', return_value=str(100)):
            api = BitfinexREST(key=key, secret=secret, version='v2')
            self.assertEqual(api.nonce(), str(100))
            self.assertEqual(api.version, 'v2')
            self.assertEqual(api.generate_uri('testing/signature'), '/v2/testing/signature')
            ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'})

            data = ('/api' + '/v2/testing/signature' + '100' + '{"param_1": "abc"}').encode('utf-8')
            signatures = hmac.new(secret.encode('utf8'), data, hashlib.sha384).hexdigest()

            self.assertIn('bfx-apikey', ret_values['headers'])
            self.assertEqual(ret_values['headers']['bfx-apikey'], key)
            self.assertIn('bfx-signature', ret_values['headers'])
            self.assertIn(ret_values['headers']['bfx-signature'], signatures)
            self.assertIn('bfx-nonce', ret_values['headers'])
            self.assertEqual(ret_values['headers']['bfx-nonce'], '100')
            self.assertIn('content-type', ret_values['headers'])
            self.assertEqual(ret_values['headers']['content-type'], 'application/json')


class BittrexRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = BittrexREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://bittrex.com/api')
        self.assertEqual(api.version, 'v1.1')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret, user = 'panda', 'shadow', 'leeroy'
        with mock.patch.object(RESTAPI, 'nonce', return_value=str(100)) as mock_rest:
            api = BittrexREST(key=key, secret=secret, version='v1.1')
            self.assertEqual(api.generate_uri('testing/signature'), '/v1.1/testing/signature')
            ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'})
            url = 'https://bittrex.com/api/v1.1/testing/signature?apikey=panda&nonce=100&param_1=abc'
            sig = hmac.new(secret.encode('utf8'), url.encode('utf8'), hashlib.sha512).hexdigest()
            self.assertEqual(ret_values['url'], url)
            self.assertIn('apisign', ret_values['headers'])
            self.assertEqual(ret_values['headers']['apisign'], sig)


class CoinCheckRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = CoincheckREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://coincheck.com')
        self.assertEqual(api.version, 'api')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret, user = 'panda', 'shadow', 'leeroy'
        with mock.patch.object(RESTAPI, 'nonce', return_value=str(100)) as mock_rest:
            api = CoincheckREST(key=key, secret=secret, version='v1')
            self.assertEqual(api.generate_uri('testing/signature'), '/v1/testing/signature')
            ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'})
            msg = '100https://coincheck.com/v1/testing/signature?param_1=abc'
            sig = hmac.new(secret.encode('utf8'), msg.encode('utf8'), hashlib.sha256).hexdigest()
            self.assertIn('ACCESS-NONCE', ret_values['headers'])
            self.assertEqual(ret_values['headers']['ACCESS-NONCE'], "100")
            self.assertIn('ACCESS-KEY', ret_values['headers'])
            self.assertEqual(ret_values['headers']['ACCESS-KEY'], key)
            self.assertIn('ACCESS-SIGNATURE', ret_values['headers'])
            self.assertEqual(ret_values['headers']['ACCESS-SIGNATURE'], sig)


class GDAXRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = GDAXREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertIs(api.passphrase, None)
        self.assertEqual(api.addr, 'https://api.gdax.com')
        self.assertIs(api.version, None)
        self.assertIs(api.config_file, None)
        # Assert that a Warning is raised if passphrase is None, and BaseAPI's
        # check mechanism is extended properly
        with self.assertWarns(IncompleteCredentialsWarning):
            api = GDAXREST(addr='Bangarang', passphrase=None, key='SomeKey',
                           secret='SomeSecret', config=None, version=None)

        # make sure an exception is raised if passphrase is passed as ''
        with self.assertRaises(ValueError):
            api = GDAXREST(addr='Bangarang', passphrase='', key='SomeKey',
                           secret='SomeSecret', config=None, version=None)

        # make sure user_id is assigned properly
        api = GDAXREST(addr='Bangarang', passphrase='woloho')
        self.assertIs(api.passphrase, 'woloho')

        # Check that a IncompleteCredentialConfigurationWarning is issued if
        # user_id isn't available in config, and no user_id was given.
        with self.assertWarns(IncompleteCredentialConfigurationWarning):
            api = GDAXREST(addr='Bangarang', passphrase=None,
                           config='%s/configs/config.ini' % tests_folder_dir)

        # check that passphrase is loaded correctly, and no
        # IncompleteCredentialsWarning is issued, if we dont pass a passphrase
        # kwarg but it is avaialable in the config file
        config_path = '%s/auth/gdax.ini' % tests_folder_dir
        with self.assertRaises(AssertionError):
            with self.assertWarns(IncompleteCredentialConfigurationWarning):
                api = GDAXREST(config=config_path)
        self.assertTrue(api.config_file == config_path)
        self.assertEqual(api.passphrase, 'shadow_panda')

    def test_sign_request_kwargs_method_and_signature(self):
        # Implement using the Python documentation as reference.
        # https://docs.gdax.com/#signing-a-message
        # Check signatured request kwargs
        pass


class KrakenRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = KrakenREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.kraken.com')
        self.assertEqual(api.version, '0')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key = 'panda'
        secret = '11LX0lqM9aExe63oe975Fjms5I9plFAPDxj0puwFBKGct79CP9GESjl5IRTDP8bqNaMYWXxEO8UbM0e4kacRtw=='
        with mock.patch.object(RESTAPI, 'nonce', return_value=str(100)) as mock_rest:
            api = KrakenREST(key=key, secret=secret, version='api')
            self.assertEqual(api.generate_uri('testing/signature'), '/api/testing/signature')
            ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'})
            encoded_payloads = ('nonce=100&param_1=abc', 'param_1=abc&nonce=100')
            expected_payload = {'nonce': '100', 'param_1': 'abc'}
            sigs = []
            for pl in encoded_payloads:
                encoded = ('100' + pl).encode()
                msg = '/api/testing/signature'.encode('utf-8') + hashlib.sha256(encoded).digest()
                signature = hmac.new(base64.b64decode(secret), msg, hashlib.sha512)
                sigdigest = base64.b64encode(signature.digest())
                sigs.append(sigdigest.decode('utf-8'))
            self.assertIn('API-Key', ret_values['headers'])
            self.assertEqual(ret_values['headers']['API-Key'], key)
            self.assertIn('API-Sign', ret_values['headers'])
            self.assertIn(ret_values['headers']['API-Sign'], sigs)
            self.assertEqual(ret_values['data'], expected_payload)


class ITBitRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = ITbitREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.itbit.com')
        self.assertEqual(api.version, 'v1')
        self.assertIs(api.config_file, None)
        # Assert that a Warning is raised if user_id is None, and BaseAPI's
        # check mechanism is extended properly
        with self.assertWarns(IncompleteCredentialsWarning):
            api = ITbitREST(addr='Bangarang', user_id=None, key='SomeKey',
                            secret='SomeSecret', config=None, version=None)

        # make sure an exception is raised if user_id is passed as ''
        with self.assertRaises(ValueError):
            api = ITbitREST(addr='Bangarang', user_id='', key='SomeKey',
                            secret='SomeSecret', config=None, version=None)

        # make sure user_id is assigned properly
        api = ITbitREST(addr='Bangarang', user_id='woloho')
        self.assertIs(api.user_id, 'woloho')

        # Check that a IncompleteCredentialConfigurationWarning is issued if
        # user_id isn't available in config, and no user_id was given.
        with self.assertWarns(IncompleteCredentialConfigurationWarning):
            api = ITbitREST(addr='Bangarang', user_id=None,
                            config='%s/configs/config.ini' % tests_folder_dir)

        # check that passphrase is loaded correctly, and no
        # IncompleteCredentialsWarning is issued, if we dont pass a user_id
        # kwarg but it is avaialable in the config file
        config_path = '%s/auth/itbit.ini' % tests_folder_dir
        with self.assertRaises(AssertionError):
            with self.assertWarns(IncompleteCredentialConfigurationWarning):
                api = ITbitREST(config=config_path)
        self.assertTrue(api.config_file == config_path)
        self.assertEqual(api.user_id, 'dummy')

    def test_sign_request_kwargs_method_and_signature(self):
        """Test itBit signature methoc.

        ItBit requires both a Nonce value AND a timestamp value. Assert that both methods work
        correctly:
            nnoce() : returns an ever increasing int, starting at 1
            timestamp() : returns a unix timestamp in milliseconds
        """
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret, user = 'panda', 'shadow', 'leeroy'
        with mock.patch.object(ITbitREST, 'timestamp', return_value=str(1000)) as mock_rest:
            api = ITbitREST(key=key, secret=secret, version='v1', user_id=user)
            self.assertEqual(api.generate_uri('testing/signature'), '/v1/testing/signature')
            
            """
            Assert PUT/POST requests are signed correctly. These are the only edge cases as their
            body (i.e. parameters) need to be passed in the header's 'Authorization' parameter,
            instead of passing it to requests.request()'s ``data`` parameter.
            """
            req_url = 'https://api.itbit.com/v1/testing/signature'
            json_bodies = ['{"param_1": "abc"}']
            req_strings = [['POST', 'https://api.itbit.com/v1/testing/signature',
                           '{"param_1": "abc"}', '1', '1000'],
                           ['PUT', 'https://api.itbit.com/v1/testing/signature',
                            '{"param_1": "abc"}', '2', '1000'],
                           ['GET', 'https://api.itbit.com/v1/testing/signature', '', '3', '1000']]
            signatures = []
            for i, req_string in enumerate(req_strings):
                message = json.dumps(req_string, separators=(',', ':'))
                nonced = str(i+1) + message
                hasher = hashlib.sha256()
                hasher.update(nonced.encode('utf-8'))
                hash_digest = hasher.digest()
                hmac_digest = hmac.new(secret.encode('utf-8'),
                                       req_url.encode('utf-8') + hash_digest,
                                       hashlib.sha512).digest()
                signatures.append(user + ':' + base64.b64encode(hmac_digest).decode('utf-8'))
            post_ret_values = api.sign_request_kwargs('testing/signature', 
                                                      params={'param_1': 'abc'}, method='POST')
            put_ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'},
                                                     method='PUT')
            
            self.assertIn('Authorization', post_ret_values['headers'])
            self.assertIn(post_ret_values['headers']['Authorization'], signatures[0])
            self.assertIn('X-Auth-Timestamp', post_ret_values['headers'])
            self.assertEqual(post_ret_values['headers']['X-Auth-Timestamp'], '1000')
            self.assertIn('X-Auth-Nonce', post_ret_values['headers'])
            self.assertEqual(post_ret_values['headers']['X-Auth-Nonce'], '1')
            self.assertIn('Content-Type', post_ret_values['headers'])
            self.assertEqual(post_ret_values['headers']['Content-Type'], 'application/json')
            self.assertIn(post_ret_values['data'], json_bodies)

            self.assertIn('Authorization', put_ret_values['headers'])
            self.assertIn(put_ret_values['headers']['Authorization'], signatures[1])
            self.assertIn('X-Auth-Timestamp', put_ret_values['headers'])
            self.assertEqual(put_ret_values['headers']['X-Auth-Timestamp'], '1000')
            self.assertIn('X-Auth-Nonce', put_ret_values['headers'])
            self.assertEqual(put_ret_values['headers']['X-Auth-Nonce'], '2')
            self.assertIn('Content-Type', put_ret_values['headers'])
            self.assertEqual(put_ret_values['headers']['Content-Type'], 'application/json')
            self.assertIn(put_ret_values['data'], json_bodies)

            """
            Assert Non-PUT/POST requests are signed correctly. Since DELETE and GET methods for itBit
            have the parameters present right in the endpoint, json_body needs to be an emptry 
            string.
            """

            get_ret_values = api.sign_request_kwargs('testing/signature', 
                                                      params={}, method='GET')
            self.assertIn('Authorization', get_ret_values['headers'])
            self.assertEqual(get_ret_values['headers']['Authorization'], signatures[2])
            self.assertIn('X-Auth-Timestamp', get_ret_values['headers'])
            self.assertEqual(get_ret_values['headers']['X-Auth-Timestamp'], '1000')
            self.assertIn('X-Auth-Nonce', get_ret_values['headers'])
            self.assertEqual(get_ret_values['headers']['X-Auth-Nonce'], '3')
            self.assertIn('Content-Type', get_ret_values['headers'])
            self.assertEqual(get_ret_values['headers']['Content-Type'], 'application/json')
            self.assertEqual(get_ret_values['data'], '')


class OKCoinRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = OKCoinREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://www.okcoin.com/api')
        self.assertEqual(api.version, 'v1')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'

        api = OKCoinREST(key=key, secret=secret, version='v1')
        self.assertEqual(api.generate_uri('testing/signature'), '/v1/testing/signature')
        ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'},
                                                                          method='POST')
        expected_params = {'api_key': key, 'param_1': 'abc'}
        sign = '&'.join([k + '=' + expected_params[k] for k in sorted(expected_params.keys())])
        sign += '&secret_key=' + secret
        signature = hashlib.md5(sign.encode('utf-8')).hexdigest().upper()
        url = 'https://www.okcoin.com/api/v1/testing/signature'
        self.assertEqual(ret_values['url'], url)
        self.assertIn('api_key=' + key, ret_values['data'])
        self.assertIn('param_1=abc', ret_values['data'])
        self.assertIn('sign=' + signature, ret_values['data'])
        self.assertIn('Content-Type', ret_values['headers'])
        self.assertIn(ret_values['headers']['Content-Type'], 'application/x-www-form-urlencoded')

        url = 'https://www.okcoin.com/api/v1/testing/signature'
        ret_values = api.sign_request_kwargs('testing/signature', params={'param_1': 'abc'},
                                             method='GET')
        self.assertEqual(ret_values['url'], url)
        self.assertEqual(ret_values['data']['api_key'], key)
        self.assertEqual(ret_values['data']['sign'], signature)
        self.assertIn('param_1', ret_values['data'])
        self.assertEqual(ret_values['data']['param_1'], 'abc')


class CCEXRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = CCEXREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://c-cex.com/t')
        self.assertIs(api.version, None)
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            api = CCEXREST(key=key, secret=secret, version='v1')
            ret_values = api.sign_request_kwargs('test_signature', params={'param_1': 'abc'},
                                                 method='GET')
            expected_params = {'api_key': key, 'param_1': 'abc', 'nonce': '100',
                               'a': 'test_signature'}
            sign = '&'.join([k + '=' + expected_params[k] for k in sorted(expected_params.keys())])
            sign += '&secret_key=' + secret
            url = 'https://c-cex.com/t/api.html?a=test_signature&apikey=%s&nonce=100&param_1=abc' % key
            signature = hmac.new(secret.encode('utf-8'), url.encode('utf-8'), hashlib.sha512).hexdigest()
            self.assertEqual(ret_values['url'], url)
            self.assertIn('apisign', ret_values['headers'])
            self.assertEqual(ret_values['headers']['apisign'], signature)

def decode_base64(data):
    """Decode base64， padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += b'=' * missing_padding
    return base64.decodebytes(data)


class CryptopiaRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = CryptopiaREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://www.cryptopia.co.nz/api')
        self.assertIs(api.version, None)
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        """Test Cryptopia signature method.

        Reference:
            https://github.com/Coac/cryptopia.js/blob/3b653c4530e730d1d14052cf2c606de88aec0962/index.js#L56
        """
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            api = CryptopiaREST(key=key, secret=secret, version='v1')
            ret_values = api.sign_request_kwargs('test_signature', params={'param_1': 'abc'})

            expected_params = {'param_1': 'abc'}
            post_data = json.dumps(expected_params)
            url = 'https://www.cryptopia.co.nz/Api/test_signature'
            parsed_url = urllib.parse.quote_plus(url).lower()

            md5 = hashlib.md5()
            md5.update(post_data.encode('utf-8'))
            request_content_b64_string = base64.b64encode(md5.digest()).decode('utf-8')
            sig = (key + 'POST' + parsed_url + '100' + request_content_b64_string)

            sec = decode_base64(secret.encode('utf-8'))
            hmac_sig = base64.b64encode(hmac.new(sec,
                                                 sig.encode('utf-8'),
                                                 hashlib.sha256).digest())
            signature = 'amx ' + key + ':' + hmac_sig.decode('utf-8') + ':' + '100'
            self.assertEqual(ret_values['data'], json.dumps(expected_params))
            self.assertIn('Authorization', ret_values['headers'])
            self.assertEqual(ret_values['headers']['Authorization'], signature)


class GeminiRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = GeminiREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.gemini.com')
        self.assertEqual(api.version, 'v1')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        api = GeminiREST(key, secret)

        # Check signatured request kwargs
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            r = api.sign_request_kwargs('products', params={'param_1': 'abc'})
            legit_loads = ['{"request": "/v1/products", "nonce": "100", "param_1": "abc"}',
                           '{"request": "/v1/products", "param_1": "abc", "nonce": "100"}',
                           '{"nonce": "100", "param_1": "abc", "request": "/v1/products"}',
                           '{"nonce": "100", "request": "/v1/products", "param_1": "abc"}',
                           '{"param_1": "abc", "nonce": "100", "request": "/v1/products"}',
                           '{"param_1": "abc", "request": "/v1/products", "nonce": "100"}']
            legit_payloads = [base64.standard_b64encode(p.encode('utf8')) for p in legit_loads]
            legit_signatures = [hmac.new(secret.encode('utf8'), sig, hashlib.sha384).hexdigest()
                                for sig in legit_payloads]

            self.assertIn('X-GEMINI-APIKEY', r['headers'])
            self.assertEqual(r['headers']['X-GEMINI-APIKEY'], key)
            self.assertIn('X-GEMINI-PAYLOAD', r['headers'])
            self.assertIn(r['headers']['X-GEMINI-PAYLOAD'], [p.decode('utf8') for p in legit_payloads])
            self.assertIn('X-GEMINI-SIGNATURE', r['headers'])
            self.assertIn(r['headers']['X-GEMINI-SIGNATURE'], legit_signatures)
            self.assertEqual(r['url'], 'https://api.gemini.com/v1/products')


class RockTradingRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = RockTradingREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.therocktrading.com')
        self.assertEqual(api.version, 'v1')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        api = RockTradingREST(key, secret)

        # Check signatured request kwargs
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            r = api.sign_request_kwargs('products', params={'param_1': 'abc'})
            raw_sig = '100https://api.therocktrading.com/v1/products?param_1=abc'
            expected_signature = hmac.new(secret.encode('utf8'), raw_sig.encode('utf8'),
                                          hashlib.sha512).hexdigest()
            self.assertIn('X-TRT-KEY', r['headers'])
            self.assertEqual(r['headers']['X-TRT-KEY'], key)
            self.assertIn('X-TRT-NONCE', r['headers'])
            self.assertEqual(r['headers']['X-TRT-NONCE'], 100)
            self.assertIn('X-TRT-SIGN', r['headers'])
            self.assertEqual(r['headers']['X-TRT-SIGN'], expected_signature)


class PoloniexRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = PoloniexREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://poloniex.com')
        self.assertIs(api.version, None)
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        api = PoloniexREST(key=key, secret=secret)

        # Check signatured request kwargs
        with mock.patch.object(api, 'nonce', return_value='100'):
            ret_value = api.sign_request_kwargs('test_signature',
                                                params={'param_1': 'abc'})
            request_string = 'param_1=abc&nonce=100&command=test_signature'
            # Construct expected result

            signature = hmac.new(secret.encode('utf8'),
                                 request_string.encode('utf8'),
                                 hashlib.sha512).hexdigest()
            self.assertIn('headers', ret_value)
            self.assertIn('Sign', ret_value['headers'])
            self.assertEqual(ret_value['headers']['Sign'], signature)
            self.assertIn('Key', ret_value['headers'])
            self.assertEqual(ret_value['headers']['Key'], key)


class QuoineRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = QuoineREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.quoine.com/')
        self.assertIs(api.version, '2')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        api = QuoineREST(key, secret)

        # Check signatured request kwargs
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            r = api.sign_request_kwargs('products', params={'param_1': 'abc'},
                                        method="GET")

            url = 'https://api.quoine.com'
            path = '/products?param_1=abc'
            expected_signature = jwt.encode(
                {'path': path, 'nonce': '100', 'token_id': key},
                secret, algorithm='HS256')
            self.assertIn('X-Quoine-Auth', r['headers'])
            self.assertEqual(r['headers']['X-Quoine-Auth'], expected_signature)
            self.assertIn('X-Quoine-API-Version', r['headers'])
            self.assertEqual(r['headers']['X-Quoine-API-Version'], '2')
            self.assertEqual(r['url'], url + '/products')


class QuadrigaCXRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = QuadrigaCXREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.quadrigacx.com')
        self.assertEqual(api.version, 'v2')
        self.assertIs(api.config_file, None)
        # Assert that a Warning is raised if client_id is None, and BaseAPI's
        # check mechanism is extended properly
        with self.assertWarns(IncompleteCredentialsWarning):
            api = QuadrigaCXREST(addr='Bangarang', client_id=None, key='SomeKey',
                            secret='SomeSecret', config=None, version=None)

        # make sure an exception is raised if client_id is passed as ''
        with self.assertRaises(ValueError):
            api = QuadrigaCXREST(addr='Bangarang', client_id='', key='SomeKey',
                            secret='SomeSecret', config=None, version=None)

        # make sure client_id is assigned properly
        api = QuadrigaCXREST(addr='Bangarang', client_id='woloho')
        self.assertIs(api.client_id, 'woloho')

        # Check that a IncompleteCredentialConfigurationWarning is issued if
        # client_id isn't available in config, and no client_id was given.
        with self.assertWarns(IncompleteCredentialConfigurationWarning):
            api = QuadrigaCXREST(addr='Bangarang', client_id=None,
                            config='%s/configs/config.ini' % tests_folder_dir)

        # check that passphrase is loaded correctly, and no
        # IncompleteCredentialsWarning is issued, if we dont pass a client_id
        # kwarg but it is avaialable in the config file
        config_path = '%s/auth/quadrigacx.ini' % tests_folder_dir
        with self.assertRaises(AssertionError):
            with self.assertWarns(IncompleteCredentialConfigurationWarning):
                api = QuadrigaCXREST(config=config_path)
        self.assertTrue(api.config_file == config_path)
        self.assertEqual(api.client_id, '2110184')

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        client_id = '12345'
        api = QuadrigaCXREST(key=key, secret=secret, client_id='12345')

        # Check signatured request kwargs
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            ret_values = api.sign_request_kwargs('test_signature', params={'param_1': 'abc'})

            nonce = '100'

            msg = nonce + client_id + key
            url = 'https://api.quadrigacx.com/v2/test_signature'
            signature = hmac.new(secret.encode('utf8'), msg.encode('utf8'),
                                 hashlib.sha256).hexdigest()
            payload = {'param_1': 'abc', 'nonce': '100', 'key': key, 'signature': signature}
            self.assertIn('json', ret_values)
            self.assertEqual(ret_values['json'], payload)
            self.assertEqual(ret_values['url'], url)


class HitBTCRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = HitBTCREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.hitbtc.com/api')
        self.assertEqual(api.version, '2')
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        api = HitBTCREST(key=key, secret=secret)

        # Check signatured request kwargs
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            ret_values = api.sign_request_kwargs('test_signature', params={'param_1': 'abc'})
            self.assertIn('auth', ret_values)
            self.assertEqual(ret_values['auth'], (key, secret))


class VaultoroRESTTest(TestCase):
    def test_initialization(self):
        # test that all default values are assigned correctly if No kwargs are
        # given
        api = VaultoroREST()
        self.assertIs(api.secret, None)
        self.assertIs(api.key, None)
        self.assertEqual(api.addr, 'https://api.vaultoro.com')
        self.assertIs(api.version, None)
        self.assertIs(api.config_file, None)

    def test_sign_request_kwargs_method_and_signature(self):
        # Test that the sign_request_kwargs generate appropriate kwargs:
        key, secret = 'panda', 'shadow'
        api = VaultoroREST(key=key, secret=secret)

        # Check signatured request kwargs
        with mock.patch.object(RESTAPI, 'nonce', return_value='100'):
            ret_values = api.sign_request_kwargs('test_signature', params={'param_1': 'abc'})

            nonce = '100'

            url = 'https://api.vaultoro.com/1/test_signature?apikey=%s&nonce=%s&param_1=abc' % (key, nonce)

            signature = hmac.new(secret.encode('utf8'), url.encode('utf8'), hashlib.sha256).hexdigest()

            self.assertIn('X-Signature', ret_values['headers'])
            self.assertEqual(ret_values['headers']['X-Signature'], signature)
            self.assertEqual(ret_values['url'], url)


if __name__ == '__main__':
    unittest.main(verbosity=2)
