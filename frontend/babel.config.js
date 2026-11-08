// Alias "@/..." được Expo đọc từ tsconfig.json (paths) và Jest đọc từ moduleNameMapper,
// nên không cần babel-plugin-module-resolver.
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
  };
};
