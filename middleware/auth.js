module.exports = (req, res, next) => {
    if (!req.headers.authorization) {
        res.status(401).send({ error: "Unauthorized"});
        return;
    }
    const token = req.headers.authorization.split(' ')[1];
    if (process.env.TOKEN && token == process.env.TOKEN) {
       next();
    } else {
        res.status(401).send({ error: "Unauthorized"});
    }
};