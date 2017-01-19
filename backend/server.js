var express = require('express');
var logger = require('morgan');
var bodyParser = require('body-parser');
var session = require('express-session');
var cookieParser = require('cookie-parser');
var uuid = require('uuid');
var passport = require('passport');
var LocalStrategy = require('passport-local').Strategy;
var User = require('./models/user.js');

var app = express();
app.use(bodyParser.urlencoded({extended: true}));
app.set('port', process.env.PORT || 3154);
app.use(logger('dev'));
app.use(cookieParser());
app.use(session({
  genid: function(req) {
    return uuid.v1();
  },
  secret: 'MoviePigeonXuanGeThePigeonist',
  saveUninitialized: true,
  resave: true
}));

app.use(passport.initialize());
app.use(passport.session());

var env = app.get('env') == 'development' ? 'dev' : app.get('env');

// Serialize sessions
passport.serializeUser(function(user, done) {
  done(null, user.id);
});

passport.deserializeUser(function(id, done) {
  User.findOne(id).then(function(user){
    done(null, user);
  }).error(function(err){
    done(err, null);
  });
});

// Use local strategy to create user account
passport.use(new LocalStrategy({
    usernameField: 'username'
  },
  function(username, password, done) {

    User.findOne({ where: { 'username' : username } }).then(function (user) {
      if (!user) {
        return done(null, false, { message: 'Incorrect username.' });
      }
      if (!user.validPassword(password)) {
				console.log('here');
        return done(null, false, { message: 'Incorrect password.' });
      }
			console.log('right');
      return done(null, user);
    });
  }
));


// IMPORT ROUTES
// =============================================================================
var router = require('./routes/index.js');

// Middleware to use for all requests
router.use(function(req, res, next) {
	// do logging
	console.log('Something is happening.');
	next();
});

app.use('/api', router);

app.listen(app.get('port'), function() {
  console.log('Express server listening on port ' + app.get('port'));
});
