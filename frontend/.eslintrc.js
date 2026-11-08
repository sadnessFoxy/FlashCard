module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    "react-native/react-native": true,
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "plugin:react-native/all",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 2022,
    sourceType: "module",
    project: "./tsconfig.json",
    tsconfigRootDir: __dirname,
  },
  plugins: ["react", "react-hooks", "@typescript-eslint", "react-native"],
  rules: {
    // TypeScript
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    "@typescript-eslint/no-non-null-assertion": "warn",
    "@typescript-eslint/no-floating-promises": "error",
    "@typescript-eslint/await-thenable": "error",

    // React
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",

    // React Native
    "react-native/no-unused-styles": "error",
    "react-native/split-platform-components": "off",
    "react-native/no-inline-styles": "warn",
    "react-native/no-color-literals": "off",
    "react-native/no-raw-text": "error",
    // Thứ tự thuộc tính style không ảnh hưởng chất lượng; chỉ gây nhiễu
    "react-native/sort-styles": "off",

    // General
    "no-console": ["warn", { allow: ["warn", "error"] }],
    // Cho phép vòng lặp đọc stream kiểu while (true) { ... break }
    "no-constant-condition": ["error", { checkLoops: false }],
  },
  settings: {
    react: {
      version: "detect",
    },
  },
  ignorePatterns: ["src/api/generated/", "node_modules/", ".expo/"],
};
