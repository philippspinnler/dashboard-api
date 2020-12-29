module.exports = (req, res, next) => {
    const token = req.headers.authorization;
    if (process.env.TOKEN && token == process.env.TOKEN) {
       next();
    } else {
        res.status(401).send({ error: "Unauthorized"});
    }
};