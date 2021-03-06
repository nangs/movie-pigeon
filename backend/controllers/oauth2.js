// Load required packages
var oauth2orize = require('oauth2orize');
var Client = require('../models/client');
var Token = require('../models/token');
var Code = require('../models/code');

// Create OAuth 2.0 server
var server = oauth2orize.createServer();

// Register serialialization and deserialization functions.
//
// When a client redirects a user to user authorization endpoint, an
// authorization transaction is initiated.  To complete the transaction, the
// user must authenticate and approve the authorization request.  Because this
// may involve multiple HTTP request/response exchanges, the transaction is
// stored in the session.
//
// An application must supply serialization functions, which determine how the
// client object is serialized into the session.  Typically this will be a
// simple matter of serializing the client's ID, and deserializing by finding
// the client by ID from the database.

server.serializeClient(function (client, callback) {
  return callback(null, client.id);
});

server.deserializeClient(function (id, callback) {
  Client.findOne({where: {id: id}}).then(function (client) {
    return callback(null, client);
  });
});

// Register supported grant types.
//
// OAuth 2.0 specifies a framework that allows users to grant client
// applications limited access to their protected resources.  It does this
// through a process of the user granting access, and the client exchanging
// the grant for an access token.

// Grant authorization codes.  The callback takes the `client` requesting
// authorization, the `redirectUri` (which is used as a verifier in the
// subsequent exchange), the authenticated `user` granting access, and
// their response, which contains approved scope, duration, etc. as parsed by
// the application.  The application issues a code, which is bound to these
// values, and will be exchanged for an access token.

server.grant(oauth2orize.grant.code(
  function (client, redirectUri, user, ares, callback) {
    // Create a new authorization code
    var value = uid(16);
    var clientId = client.id;
    var userId = user.id;
    console.log('db here');
    // Save the auth code and check for errors
    Code.build({
      value: value,
      clientId: clientId,
      redirectUri: redirectUri,
      userId: userId
    })
      .save()
      .then(function (success) {
        callback(null, value);
      })
      .catch(function (err) {
        if (err) {
          return callback(err);
        }
      });
  }));

// Exchange authorization codes for access tokens.  The callback accepts the
// `client`, which is exchanging `code` and any `redirectUri` from the
// authorization request for verification.  If these values are validated, the
// application issues an access token on behalf of the user who authorized the
// code.

server.exchange(oauth2orize.exchange.code(
  function (client, code, redirectUri, callback) {
    Code.findOne({where: {value: code}}).then(function (authCode) {
      if (authCode === undefined) {
        return callback(null, false);
      }
      if (client.id.toString() !== authCode.clientId) {
        return callback(null, false);
      }
      if (redirectUri !== authCode.redirectUri) {
        return callback(null, false);
      }

      // Delete auth code now that it has been used
      authCode.destroy().then(function (err) {
        // Create a new access token
        var value = uid(128);
        var clientId = authCode.clientId;
        var userId = authCode.userId;

        Token.find({
          where: {
            userId: userId,
            clientId: clientId
          }
        })
          .then(function (tokens) {
            if (tokens) {
              tokens.destroy();
            }
          })
          .catch(function (err) {
            console.log(err);
          });
        // Save the access token and check for errors
        Token.build({value: value, clientId: clientId, userId: userId})
          .save()
          .then(function (success) {
            callback(null, value);
          })
          .catch(function (err) {
            if (err) {
              return callback(err);
            }
          });
      });
    });
  }));

// user authorization endpoint
//
// `authorization` middleware accepts a `validate` callback which is
// responsible for validating the client making the authorization request.  In
// doing so, is recommended that the `redirectUri` be checked against a
// registered value, although security requirements may vary accross
// implementations.  Once validated, the `callback` callback must be invoked with
// a `client` instance, as well as the `redirectUri` to which the user will be
// redirected after an authorization decision is obtained.
//
// This middleware simply initializes a new authorization transaction.  It is
// the application's responsibility to authenticate the user and render a dialog
// to obtain their approval (displaying details about the client requesting
// authorization).  We accomplish that here by routing through `ensureLoggedIn()`
// first, and rendering the `dialog` view.

exports.authorization = [
  server.authorization(function (clientId, redirectUri, callback) {
    Client.findOne({where: {id: clientId}}).then(function (client) {
      return callback(null, client, redirectUri);
    });
  }),
  function (req, res) {
    res.send(req.oauth2.transactionID);
  }
];

// user decision endpoint
//
// `decision` middleware processes a user's decision to allow or deny access
// requested by a client application.  Based on the grant type requested by the
// client, the above grant middleware configured above will be invoked to send
// a response.

exports.decision = [
  server.decision()
];

// token endpoint
//
// `token` middleware handles client requests to exchange authorization grants
// for access tokens.  Based on the grant type being exchanged, the above
// exchange middleware will be invoked to handle the request.  Clients must
// authenticate when making requests to this endpoint.

exports.token = [
  server.token(),
  server.errorHandler()
];

/**
 * Return a unique identifier with the given `len`.
 *
 *     utils.uid(10);
 *     // => "FDaS435D2z"
 *
 * @param {Number} len
 * @return {String}
 * @api private
 */
function uid(len) {
  var buf = [];
  var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  var charlen = chars.length;

  for (var i = 0; i < len; ++i) {
    buf.push(chars[getRandomInt(0, charlen - 1)]);
  }

  return buf.join('');
}

/**
 * Return a random int, used by `utils.uid()`
 *
 * @param {Number} min
 * @param {Number} max
 * @return {Number}
 * @api private
 */

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
