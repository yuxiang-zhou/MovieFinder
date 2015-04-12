var express = require('express');
var router = express.Router();
var mongo = require('mongoskin');

/* GET cinema listing. */
router.get('/list', function(req, res) {
    var db = req.db;
    db.collection('films').find().toArray(function (err, items) {
        res.json(items);
    });
});

/* GET cinema listing. */
router.get('/latest', function(req, res) {
    var db = req.db;
    var date_today = new Date();
    date_today.setHours(0,0,0,0);

    db.collection('films').find({'when.date':{'$gte': date_today}}).toArray(function (err, items) {
        res.json(items);
    });
});

/* GET cinema by id. */
router.get('/id/:_id', function(req, res) {
    var db = req.db;
    var _id = mongo.helper.toObjectID(req.params._id)
    db.collection('films').find({"_id": _id}).toArray(function (err, items) {
        res.json(items);
    });
});

/* GET cinema by type. */
router.get('/type/:_type', function(req, res) {
    var db = req.db;
    var _type = req.params._type
    db.collection('films').find({"type": _type}).toArray(function (err, items) {
        res.json(items);
    });
});

/* GET cinema by cinema_id. */
router.get('/cinema_id/:_cinema_id', function(req, res) {
    var db = req.db;
    var _cinema_id = req.params._cinema_id
    db.collection('films').find({"cinema_id": _cinema_id}).toArray(function (err, items) {
        res.json(items);
    });
});

/* GET cinema by date. */
router.get('/date/:_date', function(req, res) {
    var db = req.db;
    var _date = req.params._date
    db.collection('films').find({'when':{"date": _date}}).toArray(function (err, items) {
        res.json(items);
    });
});

module.exports = router;

