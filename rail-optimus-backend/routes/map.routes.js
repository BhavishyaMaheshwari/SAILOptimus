import express from 'express';  
const mapRoutes = express.Router();
// const mapController = require('../controllers/map.controller');
import * as mapController from '../controllers/map.controller.js';
// This route will handle requests like GET /api/maps/mapdata/agra
// The ':section' part is a dynamic parameter that will hold the section name.
mapRoutes.get('/mapdata/:section', mapController.getMapDataBySection);

export default mapRoutes;