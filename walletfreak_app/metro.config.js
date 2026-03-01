const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// Allow Metro to resolve images from Django's static directory
config.watchFolders = [
  path.resolve(__dirname, '../walletfreak/static/images'),
];

module.exports = config;
