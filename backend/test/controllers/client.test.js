var server = require('../../server.js');
var request = require('supertest');
var should = require('should');
var client = require('../../models/client.js');
var user = require('../../models/user.js');

describe('Client controller test', function () {
  it('should add a client to the db', function (done) {
    var password = user.getHashedPassword('testpassword');

    user.build({
      username: 'testname',
      password: password,
      email: 'testemail'
    }).save().then(function (user) {
      request(server)
        .post('/api/clients')
        .set('Content-Type', 'application/x-www-form-urlencoded')
        .auth('testemail', 'testpassword')
        .send('name=testclient')
        .send('id=testclientid')
        .send('secret=testclientsecret')
        .expect(200)
        .end(function (err, res) {
          res.status.should.equal(200);
          res.body.message.should.equal('Client Created');
          client.find({where: {name: 'testclient'}}).then(function (client) {
            client.secret.should.equal('testclientsecret');
            client.destroy();
            user.destroy();
          });
          done();
        });
    });
  });

  it('should require authentication to add client', function (done) {
    user.build({
      username: 'testname',
      password: 'testpassword',
      email: 'testemail'
    }).save().then(function (user) {
      request(server)
        .post('/api/clients')
        .set('Content-Type', 'application/x-www-form-urlencoded')
        .send('name=testclientname')
        .send('id=testclientid')
        .send('secret=testclientsecret')
        .expect(401)
        .end(function (err, res) {
          res.status.should.equal(401);
          user.destroy();
          done();
        });
    });
  });

  it('should require correct username/password to add client', function (done) {
    user.build({
      username: 'testname',
      password: 'testpassword',
      email: 'testemail'
    }).save().then(function (user) {
      request(server)
        .post('/api/clients')
        .set('Content-Type', 'application/x-www-form-urlencoded')
        .auth('testname', 'wrongpassword')
        .send('name=testclientname')
        .send('id=testclientid')
        .send('secret=testclientsecret')
        .expect(401)
        .end(function (err, res) {
          res.status.should.equal(401);
          user.destroy();
          done();
        });
    });
  });
});
