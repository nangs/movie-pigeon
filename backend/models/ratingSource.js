// Load required packages
var sequelize = require('./db.js');
var DataTypes = require('sequelize');
// Define our ratingsource schema
var RatingSource = sequelize.define('rating_sources', {
  source_id: {
    type: DataTypes.STRING,
    allowNull: false,
    primaryKey: true
  },
  source_name: {
    type: DataTypes.STRING
  }
});

sequelize.sync({});
// Export the model
module.exports = RatingSource;
