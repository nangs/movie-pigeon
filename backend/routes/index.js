var express = require('express');
var router = express.Router();
var userControl = require('../controllers/user.js');
var authController = require('../controllers/auth');
var oauth2Controller = require('../controllers/oauth2');
var clientController = require('../controllers/client');
var movieController = require('../controllers/movie');

// on routes that end in /users
// ----------------------------------------------------
router.route('/users')
  .post(userControl.postUser)
  .get(authController.isAuthenticated, userControl.getUser);

router.post('/users/login', authController.isAuthenticated, function (req, res) {
  return res.send('login successful');
});

// Create endpoint handlers for /clients
router.route('/clients')
  .post(authController.isAuthenticated, clientController.postClients)
  .get(authController.isAuthenticated, clientController.getClients);

// Create endpoint handlers for oauth2 authorize
router.route('/oauth2/authorize')
  .get(authController.isAuthenticated, oauth2Controller.authorization)
  .post(authController.isAuthenticated, oauth2Controller.decision);

router.route('/oauth2/authorize/transactionId')
  .post(authController.isAuthenticated, oauth2Controller.authorization);

// Create endpoint handlers for oauth2 token
router.route('/oauth2/token')
  .post(authController.isClientAuthenticated, oauth2Controller.token);

router.route('/movies/id')
  .get(authController.isAuthenticated, movieController.getMoviesById);
router.route('/movies/title')
  .get(authController.isAuthenticated, movieController.getMoviesByTitle);
router.route('/movies/year')
  .get(authController.isAuthenticated,
    movieController.getMoviesByProductionYear);

module.exports = router;
