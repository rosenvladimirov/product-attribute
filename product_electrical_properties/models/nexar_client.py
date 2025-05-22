import base64
import logging

import requests
import json

from werkzeug import urls
from datetime import datetime

from odoo import http, _, api, models, fields
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

TIMEOUT = 20

DEFAULT_NEXAR_GRAPH_ENDPOINT = "https://api.nexar.com/graphql"
DEFAULT_NEXAR_TOKEN_ENDPOINT = "https://identity.nexar.com/connect/token"

RESOURCE_NOT_FOUND_STATUSES = (204, 404, 400, 401)


def decodeJWT(token):
    return json.loads((base64.urlsafe_b64decode(token.split(".")[1] + "==")).decode("utf-8"))


class NexarClient(models.AbstractModel):
    _name = 'nexar.client.mixin'
    _description = 'Nexar Client'

    nexar_token = fields.Json('Token')
    nexar_exp = fields.Datetime('Expiration Date')
    nexar_client_id = fields.Char('Clein ID')
    nexar_client_secret = fields.Char('Client Secret')

    @api.model
    def _get_graph_endpoint(self):
        return self.env["ir.config_parameter"].sudo().get_param('nexar_account.graph_endpoint', DEFAULT_NEXAR_GRAPH_ENDPOINT)

    @api.model
    def _get_token_endpoint(self):
        return self.env["ir.config_parameter"].sudo().get_param('nexar_account.token_endpoint', DEFAULT_NEXAR_TOKEN_ENDPOINT)

    @api.model
    def generate_fresh_token(self):
        """
        Generates a fresh authentication token for the application by requesting a new
        token from Microsoft using client credentials.

        This method retrieves the `client_id` and `client_secret` of the application
        from the configuration parameters or from the fields in the record, then uses
        them to request a new token from the authorization server. The response from
        the endpoint is parsed and returned as a dictionary.

        :raises UserError: If any issues occur during the token generation process,
                           such as invalid or expired credentials or failure to
                           connect to the endpoint.

        :return: A dictionary containing the token information as provided by the
                 authorization server.
        :rtype: dict
        """
        Parameters = self.env['ir.config_parameter'].sudo()
        client_id = self.nexar_client_id or Parameters.get_param('nexar_account.client_id')
        client_secret = self.nexar_client_secret or Parameters.get_param('nexar_account.client_secret')

        # Get the Refresh Token From Microsoft And store it in ir.config_parameter
        headers = {}
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            'redirect_uri': False,
        }

        try:
            req = requests.post(self._get_token_endpoint(), data=data, headers=headers, timeout=TIMEOUT)
            req.raise_for_status()
            content = req.json()
        except requests.exceptions.RequestException as exc:
            raise UserError(_("Something went wrong during your token generation. Maybe your Authorization Code is invalid or already expired"))
        return content

    def get_token(self):
        token = self.generate_fresh_token()
        exp = decodeJWT(token.get('access_token')).get('exp')
        self.write({'nexar_token': token, 'nexar_exp': datetime.fromtimestamp(exp).strftime("%Y-%m-%d %H:%M:%S")})
        return token, exp

    @api.model
    def _do_request(self, uri, json=None, headers=None, preuri=DEFAULT_NEXAR_GRAPH_ENDPOINT, timeout=TIMEOUT):
        """
        Performs an HTTP POST request to a specified URI within a defined preuri path. This method
        handles authentication headers dynamically based on token expiration and processes the server
        response to extract important data, such as response content, status, and server time. The URI's
        host is validated against a set of allowed endpoints before the request is made. Logs diagnostic
        information and debugging details as necessary.

        :param uri: A string representing the resource path to be appended to preuri and requested.
        :type uri: str
        :param json: A dictionary containing data to be sent as JSON with the POST request.
        :type json: dict, optional
        :param headers: A dictionary defining additional HTTP headers for the request. If None,
                        headers will be generated dynamically (e.g., using the token).
        :type headers: dict, optional
        :param preuri: The base URL to prefix before the URI. Defaults to DEFAULT_NEXAR_GRAPH_ENDPOINT.
        :type preuri: str, optional
        :param timeout: Specifies the maximum time duration (in seconds) to wait for the server response.
                        Defaults to TIMEOUT.
        :type timeout: int, optional
        :return: A tuple containing three values: request status code, the response content (either parsed
                 JSON data or empty if the content is absent), and the time when the server responded
                 to the request.
        :rtype: tuple (int, dict, datetime.datetime)
        """
        ask_time = fields.Datetime.now()

        if headers is None:
            if not self.nexar_exp or ask_time > self.nexar_exp:
                token, exp = self.get_token()

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "token": self.nexar_token.get('access_token'),
            }

        assert urls.url_parse(preuri + uri).host in [
            urls.url_parse(url).host for url in (DEFAULT_NEXAR_TOKEN_ENDPOINT, DEFAULT_NEXAR_GRAPH_ENDPOINT)
        ]

        _logger.debug("Uri: %s - - Headers: %s - Json : %s !" % (uri, headers, json))

        try:
            res = requests.post(preuri + uri, headers=headers, timeout=timeout, json=json)
            _logger.info(f"requests {res} - {headers} - {json}")

            res.raise_for_status()
            status = res.status_code
            if int(status) in RESOURCE_NOT_FOUND_STATUSES:
                response = {}
                _logger.info(f"Errors: {res.json().get('errors')}")
            else:
                # Some answers return empty content
                response = res.content and res.json() or {}
            try:
                ask_time = datetime.strptime(res.headers.get('date'), "%a, %d %b %Y %H:%M:%S %Z")
            except:
                pass
        except requests.HTTPError as error:
            if error.response.status_code in RESOURCE_NOT_FOUND_STATUSES:
                status = error.response.status_code
                response = {}
            else:
                _logger.exception("Bad nexar request: %s!", error.response.content)
                raise error
        return status, response, ask_time
