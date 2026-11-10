// The "@/..." alias comes from tsconfig paths (Expo) and moduleNameMapper (Jest),
// so babel-plugin-module-resolver is not needed.
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
  };
};
