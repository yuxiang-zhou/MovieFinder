var express = require('express');
var router = express.Router();
var mongo = require('mongoskin');

/* GET cinema listing. */
router.get('/list', function(req, res) {
    var db = req.db;
    db.collection('cinemas').find().toArray(function (err, items) {
        res.json(items);
    });
});

/* GET cinema by id. */
router.get('/id/:_id', function(req, res) {
    var db = req.db;
    var _id = mongo.helper.toObjectID(req.params._id)
    db.collection('cinemas').find({"_id": _id}).toArray(function (err, items) {
        res.json(items);
    });
});

/* GET cinema by type. */
router.get('/type/:_type', function(req, res) {
    var db = req.db;
    var _type = req.params._type
    db.collection('cinemas').find({"type": _type}).toArray(function (err, items) {
        res.json(items);
    });
});

module.exports = router;

